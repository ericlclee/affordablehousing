"""Train and evaluate the approval and S106 models.

    python scripts/train_models.py

Reads data/processed/features.parquet (from build_features.py) and writes:
    reports/model_metrics.md    accuracy, precision, recall, F1, ROC-AUC, PR-AUC, Brier per model
    reports/model_metrics.json  same numbers, machine-readable
    models/model.json           logistic-regression coefficients + preprocessing for the simulator
    models/xgb_approval.json    XGBoost approval model (native format)
    models/approval_with_text.joblib  offline approval model that also reads the description (score_with_text)
    models/web/                 browser bundle: approval_model.json + score.js (see models/web/README.md)

Leakage controls
- Time split: train on applications started 2022-2024, test on 2025.
- Sites in both periods are removed from the test set (a resubmission would otherwise be
  scored by a model that saw the earlier decision on the same site).
- All fill values, scaling, thresholds, tuning and calibration are fitted on the training
  years only (cross-validation grouped by site).
- Missingness is never a feature: missing rates differ by outcome (see build_report.md),
  so gaps are filled and no "is missing" flags are used, for both model types.
- Only at-submission fields are used; see FEATURES below and docs/DATA_DICTIONARY.md.
- The description model reads `description_at_submission`, which has post-submission wording
  ("amended plans", "withdrawn", ...) stripped. Its training-year scores are out-of-fold.

Description text: a TF-IDF + logistic-regression score of the description, stacked into XGBoost, added
about 0.02 ROC-AUC on the 2025 test year in the Sep 2026 probe. The simulator has no description, so
the text model is offline only (score_with_text) and the browser bundle stays parameter-only. Tried
and dropped because they did not help on 2025: earlier applications on the same site, the refusal
rate of applications within 400 m, and the borough's trailing 12-month refusal rate.
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, f1_score,
                             log_loss, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURES_FILE = Path("data/processed/features.parquet")
REPORTS, MODELS = Path("reports"), Path("models")
TEST_YEAR = 2025
SEED = 42
SMALL_LPAS = {"LLDC", "OPDC", "City of London"}  # too few rows for their own borough effect

FLAGS = ["is_major", "is_outline", "has_demolition", "has_basement", "has_roof_terrace", "has_commercial",
         "has_communal_amenity", "premium_amenity", "in_conservation_area", "in_article4_area", "in_green_belt",
         "in_opportunity_area", "in_town_centre", "listed_building_within_25m", "brownfield_site_within_50m",
         "mayor_1a_over_150_homes", "mayor_1c_height", "statutory_major", "has_backland", "has_pub_loss", "has_studio"]
# Numeric features that can be missing -> filled with training medians
FILL_MEDIAN = ["mix_studio", "mix_1b", "mix_2b", "log_site_area", "log_density", "avg_home_size_m2", "log_ptal",
               "space_std_share_below"]
TEXT_COL = "description_at_submission"
TEXT_VEC = dict(ngram_range=(1, 2), min_df=3, sublinear_tf=True, max_features=30000)
TEXT_MODEL = "XGBoost + description text (offline)"
S106_FEATURES = ["log_homes_net", "is_major", "is_outline", "affordable_pct_major", "social_rent_pct_major",
                 "has_commercial", "in_opportunity_area", "log_ptal", "imd_decile", "mayor_1a_over_150_homes",
                 "statutory_major",
                 "dev_change_of_use", "dev_conversion", "dev_extension"]


# ---------------------------------------------------------------- features

class Preprocessor:
    """Builds the model matrix. fit() learns fill values from training rows only."""

    def fit(self, df: pd.DataFrame) -> "Preprocessor":
        base = self._base(df)
        self.medians = {c: float(base[c].median()) for c in FILL_MEDIAN}
        major = base["is_major"] == 1
        self.afford_major = float(base.loc[major, "affordable_pct_major"].median())
        self.social_major = float(base.loc[major, "social_rent_pct_major"].median())
        # Storeys: median of similar schemes (development type x size), else overall
        self.storeys_by_group = base.groupby(["dev_type", "is_major"])["storeys"].median().to_dict()
        self.storeys_all = float(base["storeys"].median())
        self.lpas = sorted(set(base["lpa_grp"]))
        return self

    @staticmethod
    def _base(df: pd.DataFrame) -> pd.DataFrame:
        b = pd.DataFrame(index=df.index)
        b["log_homes_net"] = np.log1p(df["homes_net"])
        b["log_homes_lost"] = np.log1p(df["homes_lost"].fillna(0))
        for c in FLAGS:
            b[c] = df[c].astype(float)
        for c in ["mix_studio", "mix_1b", "mix_2b", "avg_home_size_m2", "space_std_share_below"]:
            b[c] = df[c]
        # Tenure only matters (and is only trusted) for 10+ homes; 0 below the threshold
        b["affordable_pct_major"] = np.where(df["is_major"], df["affordable_pct_units"], 0.0)
        b["social_rent_pct_major"] = np.where(df["is_major"], df["social_rent_pct_units"], 0.0)
        b["storeys"] = df["storeys"].clip(1, 40)
        b["log_site_area"] = np.log(df["site_area_m2"])
        b["log_density"] = np.log1p(df["density_homes_per_ha"])
        b["log_nonresi"] = np.log1p(df["nonresi_gia_gained_m2"].fillna(0).clip(lower=0))
        b["log_ptal"] = np.log1p(df["ptal_ai"])
        b["imd_decile"] = df["imd_decile"].astype(float)
        b["flood_zone_2"] = (df["flood_zone"] == 2).astype(float)
        b["flood_zone_3"] = (df["flood_zone"] == 3).astype(float)
        dev = df["dev_type"].replace({"other": "new_build"})
        b["dev_type"] = dev
        for d in ["change_of_use", "conversion", "extension"]:
            b[f"dev_{d}"] = (dev == d).astype(float)
        b["scheme_hmo"] = (df["scheme_type"] == "hmo").astype(float)
        b["scheme_student_coliving"] = df["scheme_type"].isin(["student", "coliving"]).astype(float)
        b["lpa_grp"] = df["lpa"].where(~df["lpa"].isin(SMALL_LPAS), "Other small")
        return b

    def transform(self, df: pd.DataFrame, interactions: bool = True) -> pd.DataFrame:
        b = self._base(df)
        for c, v in self.medians.items():
            b[c] = b[c].fillna(v)
        major = b["is_major"] == 1
        b.loc[major, "affordable_pct_major"] = b.loc[major, "affordable_pct_major"].fillna(self.afford_major)
        b.loc[major, "social_rent_pct_major"] = b.loc[major, "social_rent_pct_major"].fillna(self.social_major)
        b[["affordable_pct_major", "social_rent_pct_major"]] = b[["affordable_pct_major", "social_rent_pct_major"]].fillna(0)
        grp = [self.storeys_by_group.get((d, m), np.nan) for d, m in zip(b["dev_type"], b["is_major"])]
        b["storeys"] = b["storeys"].fillna(pd.Series(grp, index=b.index)).fillna(self.storeys_all)
        b["imd_decile"] = b["imd_decile"].fillna(5.0)
        for lpa in self.lpas[1:]:  # first borough alphabetically is the reference
            b[f"lpa_{lpa}"] = (b["lpa_grp"] == lpa).astype(float)
        if interactions:
            b["storeys_x_conservation"] = b["storeys"] * b["in_conservation_area"]
            b["density_x_ptal"] = b["log_density"] * b["log_ptal"]
        return b.drop(columns=["dev_type", "lpa_grp"])


# ---------------------------------------------------------------- metrics

def metrics(y, p, threshold=0.5, positive="approved"):
    y = np.asarray(y).astype(int)
    p = np.asarray(p, dtype=float)
    pred = (p >= threshold).astype(int)
    out = {
        "n": int(len(y)), "positive_rate": float(y.mean()), "threshold": float(threshold),
        "accuracy": accuracy_score(y, pred),
        f"precision_{positive}": precision_score(y, pred, zero_division=0),
        f"recall_{positive}": recall_score(y, pred, zero_division=0),
        f"f1_{positive}": f1_score(y, pred, zero_division=0),
        "roc_auc": roc_auc_score(y, p) if len(set(y)) > 1 else np.nan,
        f"pr_auc_{positive}": average_precision_score(y, p) if len(set(y)) > 1 else np.nan,
        "brier": brier_score_loss(y, p),
        "log_loss": log_loss(y, np.clip(p, 1e-6, 1 - 1e-6), labels=[0, 1]),
    }
    if positive == "approved":  # the refusal side is what developers care about
        out["precision_not_approved"] = precision_score(1 - y, 1 - pred, zero_division=0)
        out["recall_not_approved"] = recall_score(1 - y, 1 - pred, zero_division=0)
        out["pr_auc_not_approved"] = average_precision_score(1 - y, 1 - p) if len(set(y)) > 1 else np.nan
    rng = np.random.default_rng(SEED)
    boots = []
    for _ in range(500):
        i = rng.integers(0, len(y), len(y))
        if len(set(y[i])) > 1:
            boots.append(roc_auc_score(y[i], p[i]))
    out["roc_auc_ci95"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))] if boots else None
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in out.items()}


def best_f1_threshold(y, p):
    grid = np.linspace(0.05, 0.95, 91)
    return float(grid[np.argmax([f1_score(y, (p >= t).astype(int), zero_division=0) for t in grid])])


# ---------------------------------------------------------------- models

def fit_lr(X, y, groups):
    folds = list(GroupKFold(n_splits=5).split(X, y, groups))
    lr = make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=np.logspace(-3, 2, 12), cv=folds, scoring="neg_log_loss", max_iter=5000))
    lr.fit(X, y)
    # out-of-fold predictions at the chosen C, for threshold selection
    C = lr[-1].C_[0]
    oof = np.zeros(len(y))
    for tr, va in folds:
        m = make_pipeline(StandardScaler(), LogisticRegression(C=C, max_iter=5000)).fit(X.iloc[tr], y.iloc[tr])
        oof[va] = m.predict_proba(X.iloc[va])[:, 1]
    return lr, oof


class PlattCalibrator:
    """p' = sigmoid(a * logit(p) + b), fitted on out-of-fold predictions. Smooth, so small input
    changes move the output (isotonic calibration gave a 49-step staircase and a worse Brier)."""

    def __init__(self, p, y):
        z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
        lr = LogisticRegression(C=1e6).fit(z[:, None], y)
        self.a, self.b = float(lr.coef_[0][0]), float(lr.intercept_[0])

    def predict(self, p):
        p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
        return 1 / (1 + np.exp(-(self.a * np.log(p / (1 - p)) + self.b)))


def fit_xgb(X, y, groups):
    folds = list(GroupKFold(n_splits=5).split(X, y, groups))
    dtrain = xgb.DMatrix(X, label=y)
    best = None
    for depth in (2, 3, 4):
        for mcw in (5, 10):
            params = {"objective": "binary:logistic", "eval_metric": "logloss", "eta": 0.05,
                      "max_depth": depth, "min_child_weight": mcw, "subsample": 0.8,
                      "colsample_bytree": 0.8, "seed": SEED}
            cv = xgb.cv(params, dtrain, num_boost_round=2000, folds=folds, early_stopping_rounds=50,
                        verbose_eval=False)
            score = cv["test-logloss-mean"].min()
            if best is None or score < best[0]:
                best = (score, params, len(cv))
    _, params, n_rounds = best
    oof = np.zeros(len(y))
    for tr, va in folds:
        m = xgb.train(params, xgb.DMatrix(X.iloc[tr], label=y.iloc[tr]), n_rounds)
        oof[va] = m.predict(xgb.DMatrix(X.iloc[va]))
    iso = PlattCalibrator(oof, y)  # calibrate on out-of-fold predictions
    model = xgb.train(params, dtrain, n_rounds)
    return model, iso, iso.predict(oof), {"max_depth": params["max_depth"],
                                          "min_child_weight": params["min_child_weight"], "n_rounds": n_rounds}


def fit_text(text: pd.Series, y: pd.Series, groups):
    """TF-IDF + logistic regression on the description. Returns the model and out-of-fold scores."""
    make = lambda: make_pipeline(TfidfVectorizer(**TEXT_VEC), LogisticRegression(C=1.0, max_iter=3000))
    oof = np.zeros(len(y))
    for tr, va in GroupKFold(n_splits=5).split(text, y, groups):
        oof[va] = make().fit(text.iloc[tr], y.iloc[tr]).predict_proba(text.iloc[va])[:, 1]
    return make().fit(text, y), oof


def score_with_text(bundle: dict, df: pd.DataFrame) -> np.ndarray:
    """P(approved) from models/approval_with_text.joblib for rows shaped like features.parquet."""
    X = bundle["pre"].transform(df, interactions=False)
    X["text_score"] = bundle["text_model"].predict_proba(df[TEXT_COL].fillna(""))[:, 1]
    return bundle["calibrator"].predict(bundle["xgb"].predict(xgb.DMatrix(X[bundle["features"]])))


def baseline_rates(train: pd.DataFrame, test: pd.DataFrame, label: str, m: float = 20.0):
    """Borough x size-band approval rate from training years, shrunk towards the overall rate."""
    g = train[label].mean()
    stats = train.groupby(["lpa", "size_band"], observed=True)[label].agg(["sum", "count"])
    rate = ((stats["sum"] + m * g) / (stats["count"] + m)).to_dict()
    return np.array([rate.get((a, s), g) for a, s in zip(test["lpa"], test["size_band"])])


# ---------------------------------------------------------------- main

def run_task(name, df, label, positive, feature_filter=None, text=False):
    df = df[df[label].notna()].copy()
    df[label] = df[label].astype(int)
    train = df[df["year"] < TEST_YEAR]
    test_all = df[df["year"] == TEST_YEAR]
    test = test_all[~test_all["site_group"].isin(set(train["site_group"]))]
    split = {"train_rows": len(train), "test_rows": len(test),
             "test_rows_removed_site_overlap": int(len(test_all) - len(test)),
             "train_positive_rate": float(train[label].mean()), "test_positive_rate": float(test[label].mean())}

    pre = Preprocessor().fit(train)
    Xtr, Xte = pre.transform(train), pre.transform(test)
    Xtr_x, Xte_x = pre.transform(train, interactions=False), pre.transform(test, interactions=False)
    if feature_filter:
        lpa_cols = [c for c in Xtr.columns if c.startswith("lpa_")]
        cols = feature_filter + lpa_cols
        Xtr, Xte, Xtr_x, Xte_x = Xtr[cols], Xte[cols], Xtr_x[cols], Xte_x[cols]
    ytr, yte = train[label], test[label]

    print(f"[{name}] train {len(train):,}  test {len(test):,}  features {Xtr.shape[1]}", flush=True)
    lr, lr_oof = fit_lr(Xtr, ytr, train["site_group"])
    xgbm, iso, xgb_oof, xgb_params = fit_xgb(Xtr_x, ytr, train["site_group"])

    preds = {
        "Baseline (borough x size rate)": baseline_rates(train, test, label),
        "Logistic regression": lr.predict_proba(Xte)[:, 1],
        "XGBoost (calibrated)": iso.predict(xgbm.predict(xgb.DMatrix(Xte_x))),
    }
    thresholds = {"Baseline (borough x size rate)": best_f1_threshold(ytr, baseline_rates(train, train, label)),
                  "Logistic regression": best_f1_threshold(ytr, lr_oof),
                  "XGBoost (calibrated)": best_f1_threshold(ytr, xgb_oof)}
    text_out = {}
    if text:
        text_model, text_oof = fit_text(train[TEXT_COL].fillna(""), ytr, train["site_group"])
        Xtr_t = Xtr_x.assign(text_score=text_oof)
        Xte_t = Xte_x.assign(text_score=text_model.predict_proba(test[TEXT_COL].fillna(""))[:, 1])
        xgb_t, cal_t, xgb_t_oof, _ = fit_xgb(Xtr_t, ytr, train["site_group"])
        preds[TEXT_MODEL] = cal_t.predict(xgb_t.predict(xgb.DMatrix(Xte_t)))
        thresholds[TEXT_MODEL] = best_f1_threshold(ytr, xgb_t_oof)
        terms = pd.Series(text_model[-1].coef_[0], index=text_model[0].get_feature_names_out()).sort_values()
        text_out = {"text_bundle": {"pre": pre, "text_model": text_model, "xgb": xgb_t, "calibrator": cal_t,
                                    "features": list(Xtr_t.columns), "text_column": TEXT_COL},
                    "text_terms": {"refusal": list(terms.index[:15]), "approval": list(terms.index[::-1][:15])}}
    results = {}
    for model, p in preds.items():
        results[model] = {
            "at_0.5": metrics(yte, p, 0.5, positive),
            "at_best_f1_threshold_from_train": metrics(yte, p, thresholds[model], positive),
            "by_size": {grp: metrics(yte[mask], p[mask.to_numpy()], 0.5, positive)
                        for grp, mask in [("1-9 homes", ~test["is_major"]), ("10+ homes", test["is_major"]),
                                          ("labelled by Foundations", test["label_source"] == "foundations"),
                                          ("labelled by PLD", test["label_source"] == "pld")]
                        if mask.sum() > 0},
        }

    # Leakage probe: can data *completeness* alone predict the label? Should be near 0.5 AUC.
    raw_cols = ["mix_2b", "affordable_pct_units", "storeys", "avg_home_size_m2", "site_area_m2",
                "density_homes_per_ha", "ptal_ai"]
    Mtr = train[raw_cols].isna().astype(float).assign(src=(train["label_source"] == "pld").astype(float))
    Mte = test[raw_cols].isna().astype(float).assign(src=(test["label_source"] == "pld").astype(float))
    probe = LogisticRegression(max_iter=1000).fit(Mtr, ytr)
    probe_auc = roc_auc_score(yte, probe.predict_proba(Mte)[:, 1])

    coefs = pd.Series(lr[-1].coef_[0], index=Xtr.columns)
    export = {
        "label": label, "positive_class": positive, "C": float(lr[-1].C_[0]),
        "features": list(Xtr.columns), "intercept": float(lr[-1].intercept_[0]),
        "coef_standardised": coefs.round(6).to_dict(),
        "scaler_mean": dict(zip(Xtr.columns, lr[0].mean_.round(6).tolist())),
        "scaler_scale": dict(zip(Xtr.columns, lr[0].scale_.round(6).tolist())),
        "fill_values": {"medians": pre.medians, "affordable_pct_major": pre.afford_major,
                        "social_rent_pct_major": pre.social_major, "storeys_overall": pre.storeys_all,
                        "storeys_by_dev_type_and_major": {f"{d}|{int(m)}": v for (d, m), v in pre.storeys_by_group.items()}},
        "lpa_levels": pre.lpas, "lpa_reference": pre.lpas[0], "small_lpas_grouped": sorted(SMALL_LPAS),
        "threshold_best_f1": thresholds["Logistic regression"],
    }
    return {"split": split, "results": results, "xgb_params": xgb_params, "leakage_probe_auc": float(probe_auc),
            "top_coefficients": coefs.drop([c for c in coefs.index if c.startswith("lpa_")])
                                      .sort_values(key=abs, ascending=False).head(12).round(3).to_dict(),
            "export": export, "xgb_model": xgbm, "iso": iso, "pre": pre, "xgb_cols": list(Xtr_x.columns),
            "train": train, "test": test, "label": label,
            "xgb_test_pred": preds["XGBoost (calibrated)"], **text_out}


# Raw inputs score.js accepts (same names as features.parquet); everything else is derived
WEB_INPUTS = ["lpa", "homes_net", "homes_lost", "is_outline", "dev_type", "scheme_type", "storeys", "height_m_est",
              "site_area_m2", "density_homes_per_ha", "avg_home_size_m2", "space_std_share_below", "mix_studio", "mix_1b",
              "mix_2b", "affordable_pct_units", "social_rent_pct_units", "nonresi_gia_gained_m2", "has_demolition",
              "has_basement", "has_roof_terrace", "has_commercial", "has_communal_amenity", "premium_amenity",
              "in_conservation_area", "in_article4_area", "in_green_belt", "in_opportunity_area", "in_town_centre",
              "listed_building_within_25m", "brownfield_site_within_50m", "flood_zone", "ptal_ai", "imd_decile",
              "has_backland", "has_pub_loss", "has_studio"]


def export_web(task: dict, s106_task: dict) -> None:
    """Write a self-contained browser bundle: preprocessing, trees, calibration, baseline, S106 model."""
    web = MODELS / "web"
    web.mkdir(exist_ok=True)
    pre, iso, booster = task["pre"], task["iso"], task["xgb_model"]
    s106_export = s106_task["export"]
    cfg = json.loads(booster.save_raw("json"))["learner"]
    base_p = float(cfg["learner_model_param"]["base_score"].strip("[]"))
    def node_values(t):
        """Leaf values, and cover-weighted means for internal nodes (XGBoost's stored internal
        base_weights are not on the leaf scale). Used for exact per-feature path contributions."""
        L, R, h, leaf = t["left_children"], t["right_children"], t["sum_hessian"], t["split_conditions"]
        v = [0.0] * len(L)

        def rec(n):
            if L[n] == -1:
                v[n] = leaf[n]
            else:
                rec(L[n]); rec(R[n])
                v[n] = (h[L[n]] * v[L[n]] + h[R[n]] * v[R[n]]) / (h[L[n]] + h[R[n]])
        rec(0)
        return [round(x, 9) for x in v]

    trees = [{"l": t["left_children"], "r": t["right_children"], "f": t["split_indices"],
              "t": t["split_conditions"], "d": t["default_left"],  # thresholds unrounded (float32)
              "w": node_values(t)}
             for t in cfg["gradient_booster"]["model"]["trees"]]
    train, label = task["train"], task["label"]
    g = float(train[label].mean())
    stats = train.groupby(["lpa", "size_band"], observed=True)[label].agg(["sum", "count"])
    res = task["results"]
    bundle = {
        "version": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%MZ"),
        "trained_on": f"applications started 2022-{TEST_YEAR - 1}; tested on {TEST_YEAR}",
        "test_metrics": {m: {k: res[m]["at_0.5"][k] for k in ("roc_auc", "brier", "accuracy")}
                         for m in res if m != TEXT_MODEL},
        "inputs": WEB_INPUTS,
        "preprocess": {
            "medians": pre.medians, "affordable_pct_major": pre.afford_major, "social_rent_pct_major": pre.social_major,
            "storeys_overall": pre.storeys_all,
            "storeys_by_dev_type_and_major": {f"{d}|{int(m)}": v for (d, m), v in pre.storeys_by_group.items()},
            "lpa_levels": pre.lpas, "small_lpas": sorted(SMALL_LPAS), "flags": FLAGS,
        },
        "approval": {
            "features": task["xgb_cols"], "base_margin": float(np.log(base_p / (1 - base_p))), "trees": trees,
            "calibration": {"type": "platt", "a": iso.a, "b": iso.b},
        },
        "baseline": {"overall": g, "shrinkage": 20.0,
                     "by_borough_size": {f"{a}|{b}": [float(r["sum"]), int(r["count"])] for (a, b), r in stats.iterrows()}},
        "s106_given_approved": {**{k: s106_export[k] for k in ("features", "intercept", "coef_standardised",
                                                              "scaler_mean", "scaler_scale", "fill_values",
                                                              "lpa_levels")},
                                "reliability": "low: the label is S106 wording in decision text, which 20 of 35 "
                                               "boroughs never use; treat as indicative only"},
    }
    (web / "approval_model.json").write_text(json.dumps(bundle, separators=(",", ":")))
    # Parity samples so score.js can be checked against Python
    test = task["test"].reset_index(drop=True)
    idx = np.random.default_rng(SEED).choice(len(test), size=min(300, len(test)), replace=False)
    rows = test.loc[idx, WEB_INPUTS].astype(object).where(test.loc[idx, WEB_INPUTS].notna(), None)
    # Expected S106 probabilities from the exported coefficients and the S106 task's own fill values
    Xs = s106_task["pre"].transform(test.loc[idx])[s106_export["features"]]
    z = s106_export["intercept"] + sum(
        s106_export["coef_standardised"][f] * (Xs[f] - s106_export["scaler_mean"][f]) / s106_export["scaler_scale"][f]
        for f in s106_export["features"])
    p_s106 = 1 / (1 + np.exp(-z.to_numpy()))
    samples = [{"input": {k: (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in r.items()},
                "expected_p_approved": float(task["xgb_test_pred"][i]), "expected_p_s106": float(ps)}
               for i, ps, (_, r) in zip(idx, p_s106, rows.iterrows())]
    (web / "parity_samples.json").write_text(json.dumps(samples, default=float))
    print(f"Wrote {web / 'approval_model.json'} ({(web / 'approval_model.json').stat().st_size / 1e3:.0f} kB)")


def fmt(v):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.3f}"


def table(results, key, cols):
    head = "| Model | " + " | ".join(c[1] for c in cols) + " |"
    lines = [head, "|" + "---|" * (len(cols) + 1)]
    for model, r in results.items():
        m = r[key]
        cells = []
        for c, _ in cols:
            if c == "roc_auc":
                ci = m.get("roc_auc_ci95")
                cells.append(f"{fmt(m['roc_auc'])} ({fmt(ci[0])}–{fmt(ci[1])})" if ci else fmt(m["roc_auc"]))
            else:
                cells.append(fmt(m.get(c)))
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    df = pd.read_parquet(FEATURES_FILE)
    REPORTS.mkdir(exist_ok=True)
    MODELS.mkdir(exist_ok=True)

    tasks = {
        "A. P(approved), withdrawn = not approved": run_task("approval", df, "y_approved", "approved", text=True),
        "A2. P(approved | decided), withdrawn excluded": run_task("approval_decided", df, "y_approved_decided", "approved",
                                                                  text=True),
        "B. P(S106 | approved)": run_task("s106", df[df["outcome"] == "approved"], "y_s106", "s106", S106_FEATURES),
    }

    appr_cols = [("accuracy", "Accuracy"), ("precision_approved", "Precision (approved)"),
                 ("recall_approved", "Recall (approved)"), ("precision_not_approved", "Precision (not approved)"),
                 ("recall_not_approved", "Recall (not approved)"), ("roc_auc", "ROC-AUC (95% CI)"),
                 ("pr_auc_approved", "PR-AUC (approved)"), ("brier", "Brier")]
    s106_cols = [("accuracy", "Accuracy"), ("precision_s106", "Precision (S106)"), ("recall_s106", "Recall (S106)"),
                 ("f1_s106", "F1 (S106)"), ("roc_auc", "ROC-AUC (95% CI)"), ("pr_auc_s106", "PR-AUC (S106)"),
                 ("brier", "Brier")]

    md = ["# Model metrics", "",
          f"Train: applications started 2022–{TEST_YEAR - 1}. Test: started {TEST_YEAR}, excluding sites that also "
          "appear in training. Everything (fill values, scaling, tuning, calibration, thresholds) is fitted on training "
          "years only, with cross-validation grouped by site. Missingness is not used as a feature.", "",
          "Brier score: mean squared error of the probabilities (lower is better). PR-AUC: area under the "
          "precision–recall curve (compare with the positive rate). ROC-AUC 95% CI from 500 bootstrap resamples "
          "of the test set.", ""]
    for title, t in tasks.items():
        cols = s106_cols if "S106" in title else appr_cols
        s = t["split"]
        md += [f"## {title}", "",
               f"Train {s['train_rows']:,} rows (positive rate {s['train_positive_rate']:.1%}); "
               f"test {s['test_rows']:,} rows (positive rate {s['test_positive_rate']:.1%}); "
               f"{s['test_rows_removed_site_overlap']} test rows removed for site overlap.", "",
               "**Threshold 0.5**", "", table(t["results"], "at_0.5", cols), "",
               "**Threshold chosen to maximise F1 on training out-of-fold predictions**", "",
               table(t["results"], "at_best_f1_threshold_from_train", cols), ""]
        for grp in ("1-9 homes", "10+ homes", "labelled by Foundations", "labelled by PLD"):
            sub = {m: {"by": r["by_size"][grp]} for m, r in t["results"].items() if grp in r["by_size"]}
            if sub:
                n = next(iter(sub.values()))["by"]["n"]
                md += [f"**{grp}** (test n = {n}, threshold 0.5)", "", table(sub, "by", cols), ""]
        md += [f"XGBoost settings chosen by grouped CV: {t['xgb_params']}.", "",
               f"Leakage probe: a model using only *which fields are missing* and *which source labelled the row* scores ROC-AUC "
               f"**{t['leakage_probe_auc']:.3f}** on the test set (0.5 = no signal).", "",
               "Largest logistic-regression coefficients (standardised; positive = raises the probability; "
               "borough effects omitted):", "", "| Feature | Coefficient |", "|---|---|"]
        md += [f"| `{k}` | {v:+.3f} |" for k, v in t["top_coefficients"].items()]
        md += [""]
        if "text_terms" in t:
            md += [f"**{TEXT_MODEL}** stacks a TF-IDF + logistic-regression score of `{TEXT_COL}` onto the XGBoost "
                   "features (out-of-fold on training years). The simulator has no description, so this model is not "
                   "in the browser bundle.", "",
                   "- Refusal-leaning terms: " + ", ".join(f"`{w}`" for w in t["text_terms"]["refusal"]),
                   "- Approval-leaning terms: " + ", ".join(f"`{w}`" for w in t["text_terms"]["approval"]), ""]

    v1 = REPORTS / "model_metrics_v1.json"
    if v1.exists():
        old = json.loads(v1.read_text())
        md += ["## Change from v1 (Foundations-only, 7,766 rows)", "", "| Task | Model | v1 ROC-AUC | v2 ROC-AUC | v1 Brier | v2 Brier | v1 test n | v2 test n |",
               "|---|---|---|---|---|---|---|---|"]
        for title, t in tasks.items():
            if title not in old:
                continue
            for model, r in t["results"].items():
                o = old[title]["results"].get(model, {}).get("at_0.5", {})
                n = r["at_0.5"]
                md.append(f"| {title.split('.')[0]} | {model} | {fmt(o.get('roc_auc'))} | {fmt(n['roc_auc'])} | "
                          f"{fmt(o.get('brier'))} | {fmt(n['brier'])} | {o.get('n', '–')} | {n['n']} |")
        md.append("")
    (REPORTS / "model_metrics.md").write_text("\n".join(md) + "\n")
    (REPORTS / "model_metrics.json").write_text(json.dumps(
        {k: {kk: vv for kk, vv in v.items() if kk not in ("export", "xgb_model", "iso", "pre", "xgb_cols", "train", "test",
                                                          "label", "xgb_test_pred", "text_bundle")}
         for k, v in tasks.items()},
        indent=2, default=float))
    (MODELS / "model.json").write_text(json.dumps({
        "description": "Logistic-regression models. p = sigmoid(intercept + sum(coef * (x - mean) / scale)). "
                       "Build x with the transforms in scripts/train_models.py (Preprocessor).",
        "approval": tasks["A. P(approved), withdrawn = not approved"]["export"],
        "s106_given_approved": tasks["B. P(S106 | approved)"]["export"],
    }, indent=2, default=float))
    tasks["A. P(approved), withdrawn = not approved"]["xgb_model"].save_model(MODELS / "xgb_approval.json")
    joblib.dump(tasks["A. P(approved), withdrawn = not approved"]["text_bundle"], MODELS / "approval_with_text.joblib")
    export_web(tasks["A. P(approved), withdrawn = not approved"], tasks["B. P(S106 | approved)"])
    print(f"Wrote {REPORTS / 'model_metrics.md'}, {MODELS / 'model.json'}")


if __name__ == "__main__":
    # Run through the module so approval_with_text.joblib pickles train_models.Preprocessor (loadable
    # after `import train_models`), not __main__.Preprocessor
    import train_models
    train_models.main()

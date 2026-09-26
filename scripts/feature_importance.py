"""Which features actually move the approval model? Writes reports/feature_importance.md.

    python scripts/feature_importance.py

Uses the same train/test split and XGBoost settings as train_models.py, then on the 2025 test set:
- permutation importance: ROC-AUC lost when a feature (or feature group) is shuffled, 30 repeats;
  a feature counts as having a real effect if the 95% interval of that loss is above zero
- effect size: change in mean predicted approval (percentage points) from a low to a high value
  (10th -> 90th percentile, or no -> yes), everything else about each scheme unchanged
Associations, not causal effects.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score

import train_models as tm

TENURE = ("affordable_pct_major", "social_rent_pct_major")  # only defined for 10+ home schemes
GROUP_NAMES = {"borough": "Borough", "unit mix": "Unit mix (studio / 1b / 2b share)",
               "development type": "Development type", "flood zone": "Flood zone",
               "scheme type": "Scheme type (HMO / student / co-living)",
               "build form": "Build form (houses / flats / block…)"}


def group_of(c):
    return ("borough" if c.startswith("lpa_") else "unit mix" if c.startswith("mix_") else
            "development type" if c.startswith("dev_") else "flood zone" if c.startswith("flood_zone") else
            "scheme type" if c.startswith("scheme_") else "build form" if c.startswith("bf_") else c)


def main():
    df = pd.read_parquet(tm.FEATURES_FILE)
    train = df[df.year < tm.TEST_YEAR]
    test = df[(df.year == tm.TEST_YEAR) & ~df.site_group.isin(set(train.site_group))]
    pre = tm.Preprocessor().fit(train)
    Xtr, Xte = pre.transform(train, False), pre.transform(test, False)
    model, cal, _, _ = tm.fit_xgb(Xtr, train.y_approved, train.site_group)
    y = test.y_approved.values
    raw = lambda X: model.predict(xgb.DMatrix(X))
    pred = lambda X: cal.predict(raw(X))
    auc0 = roc_auc_score(y, raw(Xte))

    groups = {}
    for c in Xte.columns:
        groups.setdefault(group_of(c), []).append(c)
    rng = np.random.default_rng(tm.SEED)
    rows = []
    for g, cs in groups.items():
        drops = []
        for _ in range(30):
            Xp = Xte.copy()
            Xp[cs] = Xte[cs].values[rng.permutation(len(Xp))]
            drops.append(auc0 - roc_auc_score(y, raw(Xp)))
        lo, hi = np.percentile(drops, [2.5, 97.5])

        # effect size
        if g == "borough":
            vals = {}
            for c in [None] + cs:
                X = Xte.copy(); X[cs] = 0.0
                if c:
                    X[c] = 1.0
                vals[c[4:] if c else pre.lpas[0]] = pred(X).mean()
            s = pd.Series(vals).sort_values()
            effect = f"{s.iloc[0]:.0%} ({s.index[0]}) to {s.iloc[-1]:.0%} ({s.index[-1]}) for the same schemes"
        elif len(cs) > 1:
            X = Xte.copy(); X[cs] = 0.0
            base = pred(X).mean()
            parts = []
            for c in cs:
                X2 = X.copy(); X2[c] = 1.0
                parts.append(f"{c.split('_', 1)[1].replace('_', ' ')} {100 * (pred(X2).mean() - base):+.1f} pp")
            effect = ", ".join(parts) + " vs reference"
        else:
            c = cs[0]
            src = Xtr.loc[Xtr.is_major == 1, c] if c in TENURE else Xtr[c]
            binary = set(src.unique()) <= {0.0, 1.0}
            lo_v, hi_v = (0.0, 1.0) if binary else (src.quantile(0.1), src.quantile(0.9))
            X = Xte.copy()
            if c in TENURE:  # tenure only applies to 10+ home schemes
                X = X[X.is_major == 1]
            a = X.copy(); a[c] = lo_v
            b = X.copy(); b[c] = hi_v
            d = 100 * (pred(b).mean() - pred(a).mean())
            label = "no → yes" if binary else f"{lo_v:.3g} → {hi_v:.3g}"
            effect = f"{label}: {d:+.1f} pp" + (" (10+ home schemes)" if c in TENURE else "")
        rows.append({"feature": GROUP_NAMES.get(g, g), "auc_drop": np.mean(drops), "lo": lo, "hi": hi,
                     "real": lo > 0, "effect": effect})

    t = pd.DataFrame(rows).sort_values("auc_drop", ascending=False)
    md = ["# What drives the approval model", "",
          f"XGBoost approval model, 2025 test set ({len(test):,} proposals, ROC-AUC {auc0:.3f}). "
          "**ROC-AUC lost**: drop in ROC-AUC when the feature is shuffled (mean of 30, with 95% interval); "
          "**Effect**: change in mean predicted approval from a low to a high value (10th → 90th percentile of "
          "the model's input scale, or no → yes), everything else unchanged. Log-scale features "
          "(`log_*`) show log values. These are associations in historical decisions, not causal effects.", ""]
    for title, sub in [("Features with a real effect (interval above zero)", t[t.real]),
                       ("No clear effect (interval includes zero)", t[~t.real])]:
        md += [f"## {title}", "", "| Feature | ROC-AUC lost (95% CI) | Effect on predicted approval |", "|---|---|---|"]
        md += [f"| {r.feature} | {r.auc_drop:.4f} ({r.lo:.4f} to {r.hi:.4f}) | {r.effect} |" for r in sub.itertuples()]
        md.append("")
    (tm.REPORTS / "feature_importance.md").write_text("\n".join(md) + "\n")
    print(f"Wrote {tm.REPORTS / 'feature_importance.md'}")


if __name__ == "__main__":
    main()

"""Clean and join Foundations + PLD + spatial layers into one row per housing proposal.

    python scripts/build_features.py

Inputs (see README):  foundations_london_housing_*.csv (project root or data/raw/)
                      data/raw/pld/*.jsonl.gz
                      data/raw/spatial/*
Outputs:              data/processed/features.parquet
                      data/processed/build_report.md  (row counts per step + leakage audit)

Cohort: new full/outline applications that create at least one net home, decided
(approved / refused) or withdrawn. Labels come from Foundations; proposal features from
PLD; site context from spatial layers; amenity/type flags from the description.
"""

import argparse
import glob
import gzip
import json
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

RAW = Path("data/raw")
OUT = Path("data/processed")

# Foundations area_name -> PLD lpa_name
BOROUGH_MAP = {
    "Barking and Dagenham": "Barking & Dagenham",
    "Hammersmith and Fulham": "Hammersmith & Fulham",
    "Kensington": "Kensington & Chelsea",
    "City": "City of London",
    "London Legacy": "LLDC",
    "Old Oak Park Royal": "OPDC",
}

OUTCOME = {"Permitted": "approved", "Conditions": "approved", "Rejected": "refused", "Withdrawn": "withdrawn"}
# PLD decision -> outcome. Checked against Foundations on 7,230 shared applications: 99.7% agreement.
PLD_OUTCOME = {"approved": "approved", "approve": "approved", "refused": "refused", "ref": "refused",
               "withdrawn": "withdrawn"}
# London Plan 2021 Table 3.1 minimum GIA (m²) by bedrooms, smallest occupancy; 4+ bedrooms -> 90
SPACE_STD_MIN = {0: 37, 1: 50, 2: 61, 3: 74}

TENURE = {
    "market for sale": "market", "market for rent": "market", "self-build and custom build": "market",
    "social rent": "low_cost_rent", "london affordable rent": "low_cost_rent",
    "affordable rent (not at lar benchmark rents)": "low_cost_rent",
    "london shared ownership": "intermediate", "discount market rent": "intermediate",
    "intermediate other": "intermediate", "intermediateother": "intermediate",
    "london living rent": "intermediate", "discount market sale": "intermediate",
    "shared equity": "intermediate", "starter homes": "intermediate",
}

# Follow-up applications on an existing permission, certificates and prior approvals.
FOLLOWUP_RE = (r"variation|section 73|\bs73\b|non[- ]material|reserved matters|discharge|details pursuant|"
               r"pursuant to condition|details (?:of|for|submitted)[^.;]{0,40}condition \d|"
               r"approval of details|lawful development|certificate of lawful|prior approval|prior notification")
FP_NON_PROPOSAL_SUFFIX = r"/(?:HSE|HOU|HOT|HH|LDCP|PLUD|CLUE|CLUP|192|DISC|NMA|PA|PRE)\b"
PLD_PROPOSAL_TYPES = r"^(?:Full planning|Outline planning)"
S106_RE = r"106|legal agreement|legal ag\.|obligation|unilateral"

NUM_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty".split())}
NUM = r"(\d{1,2}|" + "|".join(NUM_WORDS) + r")"
STOREY_RE = re.compile(NUM + r"(?:\s*(?:-|to|/|and)\s*" + NUM + r")?[\s-]*stor(?:e)?y", re.I)

# (flag, pattern, removal pattern that means the feature is being lost, not provided)
TEXT_FLAGS = {
    "gym": (r"\bgym(?:nasium)?s?\b|fitness (?:suite|centre|studio)|health club", r"(?:loss|remov|demoli|change of use from|conversion of)[^.;]{0,40}(?:gym|fitness)"),
    "pool": (r"swimming pool|\bpool\b", r"(?:remov|demoli|infill|fill(?:ing)? in|decommission)[^.;]{0,40}pool"),
    "basement": (r"basement", r"(?:infill|fill(?:ing)? in)[^.;]{0,30}basement"),
    "roof_terrace": (r"roof terrace|rooftop terrace|roof garden", None),
    "concierge": (r"concierge", None),
    "communal_amenity": (r"communal (?:amenity|garden|space|lounge|roof)|residents'? (?:lounge|amenity)", None),
    "commercial": (r"class e\b|use class e|commercial|retail|office", None),
    "demolition": (r"demoli", None),
    "affordable_mention": (r"affordable", None),
    "student": (r"student", None),
    "coliving": (r"co-?living|large[- ]scale purpose[- ]built shared", None),
    "hmo": (r"\bhmo\b|house in multiple occupation", None),
    # Refusal-leaning wording found by the description text model (reports/model_metrics.md)
    "backland": (r"(?:land|site|garden|plot)s? (?:to the |at the |at )?rear of|backland|garden land|"
                 r"rear gardens? of|land adjacent to|land adjoining", None),
    "pub_loss": (r"public house|\bpub\b|drinking establishment", None),
    "studio": (r"\bstudio", None),
}
# Wording added to a description after submission (amended plans, withdrawals, decisions). Stripped
# from `description_at_submission`, the text the description model trains on. "refuse" is kept:
# it almost always means refuse (bin) storage.
POST_SUBMISSION_RE = (r"\b\w*(?:withdrawn|amend|revis|approv|appeal|dismiss|decision|superseded|deferred)\w*\b"
                      r"(?:\s+(?:description|drawings?|plans?))?")
POOL_FALSE_POS = r"liverpool|pool road|pool street|poole|whirlpool|car ?pool"

# "erection of 4 dwellings", "2 x 1-bed flats", "conversion into three self-contained flats"
HOMES_RE = re.compile(
    NUM.replace(r"\d{1,2}", r"\d{1,3}")
    + r"\s*(?:x\s*)?(?:no\.?\s*)?(?:new\s*)?(?:self[- ]contained\s*)?(?:residential\s*)?"
    r"(?:(?:\d|one|two|three|four|five)[- ]?bed(?:room)?(?:ed)?\s*)?"
    r"(?:dwellings?|dwellinghouses?|flats?|homes?|houses?|apartments?|maisonettes?|residential units?)\b",
    re.I)


def parse_homes(text: str) -> float:
    """Sum of 'N dwellings/flats/...' mentions, ignoring existing units."""
    total = 0
    for m in HOMES_RE.finditer(text):
        before = text[max(0, m.start() - 25):m.start()]
        if re.search(r"existing|current|retention of|loss of", before):
            continue
        g = m.group(1)
        v = int(g) if g.isdigit() else NUM_WORDS.get(g.lower(), 0)
        total += v
    return float(total) if 0 < total < 1000 else np.nan


def num(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else np.nan
    except (TypeError, ValueError):
        return np.nan


def norm_ref(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s).upper())


# ---------------------------------------------------------------- PLD

def flatten_pld(rec: dict) -> dict:
    ad = rec.get("application_details") or {}
    rd = ad.get("residential_details") or {}
    units = [u for u in rd.get("residential_units") or []
             if not u.get("superseded_by_lpa_app_no") and u.get("unit_type") != "Communal Space"]
    gain = [u for u in units if (u.get("change_type") or "").lower() == "gain"]
    loss = [u for u in units if (u.get("change_type") or "").lower() == "loss"]

    row = {
        "lpa": rec.get("lpa_name"),
        "nref": norm_ref(rec.get("lpa_app_no")),
        "pld_id": rec.get("_id"),
        "pld_app_type": rec.get("application_type_full"),
        "pld_last_updated": rec.get("last_updated"),
        "pld_description": rec.get("description"),
        "pld_outcome": PLD_OUTCOME.get(str(rec.get("decision") or "").strip().lower()),
        "pld_valid_date": rec.get("valid_date"),
        "pld_s106": rec.get("s106_agreement") if isinstance(rec.get("s106_agreement"), bool) else None,
        "homes_gained": len(gain),
        "homes_lost": len(loss),
    }

    # Unit mix (bedrooms) and scheme type
    beds = []
    for u in gain:
        b = num(u.get("no_bedrooms"))
        if u.get("unit_type") == "Studio Bedsit":
            b = 0
        beds.append(b)
    beds = np.array(beds, dtype=float)
    known = beds[~np.isnan(beds)]
    for name, cond in [("studio", known == 0), ("1b", known == 1), ("2b", known == 2), ("3b_plus", known >= 3)]:
        row[f"mix_{name}"] = cond.mean() if len(known) else np.nan
    # Share of self-contained homes below the London Plan minimum space standard (policy D6 / B08)
    below = []
    for u, b in zip(gain, beds):
        a = num(u.get("gia"))
        if u.get("unit_type") in ("Student Accommodation", "Co Living Unit", "HMO") or np.isnan(b) or not a > 0:
            continue
        below.append(a < SPACE_STD_MIN.get(int(b), 90))
    row["space_std_share_below"] = float(np.mean(below)) if below else np.nan
    utypes = [u.get("unit_type") or "" for u in gain]
    row["student_units"] = sum(t == "Student Accommodation" for t in utypes)
    row["coliving_units"] = sum(t == "Co Living Unit" for t in utypes)
    row["hmo_units"] = sum(t == "HMO" for t in utypes)

    # Tenure: affordable share by units and by habitable rooms
    ten = [TENURE.get((u.get("tenure") or "").strip().lower(), "unknown") for u in gain]
    hab = np.array([num(u.get("no_habitable_rooms")) for u in gain], dtype=float)
    ten = np.array(ten)
    known_t = ten != "unknown"
    aff = np.isin(ten, ["low_cost_rent", "intermediate"])
    row["tenure_known_share"] = known_t.mean() if len(ten) else np.nan
    row["affordable_pct_units"] = aff[known_t].mean() * 100 if known_t.any() else np.nan
    hab_ok = known_t & ~np.isnan(hab) & (hab > 0)
    row["habitable_rooms"] = np.nansum(hab) if (~np.isnan(hab)).any() else np.nan
    row["affordable_pct_habrooms"] = (hab[hab_ok & aff].sum() / hab[hab_ok].sum() * 100) if hab_ok.any() else np.nan
    n_aff = aff.sum()
    social = np.array([(u.get("tenure") or "").strip().lower() == "social rent" for u in gain])
    row["social_rent_share_of_affordable"] = social.sum() / n_aff if n_aff else np.nan
    row["low_cost_rent_share_of_affordable"] = (ten == "low_cost_rent").sum() / n_aff if n_aff else np.nan

    # Floor area of new homes
    unit_gia = np.array([num(u.get("gia")) for u in gain], dtype=float)
    row["resi_gia_m2"] = np.nansum(unit_gia) if (unit_gia > 0).any() else num(rd.get("total_gia_gained"))

    # Buildings: storeys and height (cleaned later)
    bd = ad.get("building_details") or []
    st = [num(b.get("no_storeys")) for b in bd]
    ht = [num(b.get("max_height")) for b in bd]
    row["pld_storeys"] = np.nanmax(st) if any(np.isfinite(st)) else np.nan
    row["pld_height_m"] = np.nanmax(ht) if any(np.isfinite(ht)) else np.nan
    row["n_buildings"] = len(bd) or np.nan

    # Site area: stated value is usually hectares; values > 50 are m²
    sa = num(ad.get("site_area"))
    if np.isnan(sa):
        sa = num(rd.get("site_area"))
    row["site_area_m2_stated"] = (sa * 10_000 if sa <= 50 else sa) if sa and sa > 0 else np.nan
    row["pld_polygon"] = json.dumps(rec["wgs84_polygon"]) if rec.get("wgs84_polygon") else None
    c = rec.get("centroid") or {}
    row["pld_lat"], row["pld_lng"] = num(c.get("lat")), num(c.get("lon"))

    # Non-residential floorspace
    fl = ad.get("existing_proposed_floorspace_details") or []
    nonresi = [f for f in fl if not str(f.get("use_class") or "").upper().startswith("C")]
    row["nonresi_gia_gained_m2"] = np.nansum([num(f.get("gia_gained")) for f in nonresi]) if nonresi else 0.0
    row["has_sport_use_class"] = any(str(f.get("use_class") or "").upper().replace(" ", "") in ("E(D)", "D2", "F2(D)")
                                     for f in fl)

    # Parking
    pk = rec.get("parking_details") or {}
    row["car_spaces"] = num(pk.get("no_proposed_car"))
    row["cycle_spaces"] = num(pk.get("no_proposed_cycle"))
    return row


def load_pld() -> pd.DataFrame:
    files = sorted(glob.glob(str(RAW / "pld" / "*.jsonl.gz")))
    if not files:
        raise SystemExit("No PLD data: run python scripts/download_pld.py")
    rows = []
    for fn in files:
        with gzip.open(fn, "rt") as f:
            for line in f:
                rows.append(flatten_pld(json.loads(line)))
    df = pd.DataFrame(rows)
    df["pld_last_updated"] = pd.to_datetime(df["pld_last_updated"], errors="coerce", utc=True)
    return (df.sort_values("pld_last_updated")
              .drop_duplicates(["lpa", "nref"], keep="last"))


# ---------------------------------------------------------------- text

def parse_storeys(text: str) -> float:
    best = np.nan
    for m in STOREY_RE.finditer(text):
        before = text[max(0, m.start() - 25):m.start()]
        if re.search(r"existing|current", before):
            continue
        for g in m.groups():
            if g:
                v = int(g) if g.isdigit() else NUM_WORDS.get(g.lower())
                if v and 1 <= v <= 60:
                    best = v if np.isnan(best) else max(best, v)
    return best


def dev_type(text: str) -> str:
    if re.search(r"erection|construction of|new build|redevelop|demolition", text):
        return "new_build"
    if "change of use" in text:
        return "change_of_use"
    if re.search(r"conver|subdivi|sub-divi", text):
        return "conversion"
    if re.search(r"extension|additional (?:storey|floor)|upward|mansard|roof", text):
        return "extension"
    return "other"


def text_features(desc: pd.Series) -> pd.DataFrame:
    d = desc.fillna("").str.lower()
    out = pd.DataFrame(index=desc.index)
    for flag, (pat, removal) in TEXT_FLAGS.items():
        has = d.str.contains(pat, regex=True)
        if flag == "pool":
            has &= ~d.str.contains(POOL_FALSE_POS, regex=True) | d.str.contains("swimming pool")
        if removal:
            removed = d.str.contains(removal, regex=True)
            out[f"{flag}_removed"] = removed
            has &= ~removed
        out[f"has_{flag}"] = has
    out["description_at_submission"] = (desc.fillna("").str.replace(POST_SUBMISSION_RE, " ", case=False, regex=True)
                                        .str.replace(r"\s+", " ", regex=True).str.strip())
    out["dev_type"] = d.map(dev_type)
    out["text_storeys"] = d.map(parse_storeys)
    return out


# ---------------------------------------------------------------- spatial

def spatial_features(pts: gpd.GeoDataFrame) -> pd.DataFrame:
    """pts: GeoDataFrame in EPSG:27700 indexed like the feature table."""
    sp = RAW / "spatial"
    out = pd.DataFrame(index=pts.index)
    base = pts[["geometry"]].copy()

    def within(layer: str, col: str):
        g = gpd.read_parquet(sp / f"{layer}.parquet").to_crs(27700)[["geometry"]]
        j = gpd.sjoin(base, g, predicate="within", how="inner")
        out[col] = pts.index.isin(j.index)

    def near(layer: str, col: str, dist: float):
        g = gpd.read_parquet(sp / f"{layer}.parquet").to_crs(27700)[["geometry"]]
        j = gpd.sjoin(base.assign(geometry=base.buffer(dist)), g, predicate="intersects", how="inner")
        out[col] = pts.index.isin(j.index)

    within("conservation-area", "in_conservation_area")
    within("article-4-direction-area", "in_article4_area")
    within("tree-preservation-zone", "in_tpo_zone")
    within("green-belt", "in_green_belt")
    within("opportunity-areas", "in_opportunity_area")
    within("strategic-industrial-land", "in_sil")
    within("town-centres", "in_town_centre")
    near("listed-building-outline", "listed_building_within_25m", 25)
    near("brownfield-land", "brownfield_site_within_50m", 50)

    fz = gpd.read_parquet(sp / "flood-risk-zone.parquet").to_crs(27700)[["flood-risk-level", "geometry"]]
    fz["lvl"] = pd.to_numeric(fz["flood-risk-level"], errors="coerce")
    j = gpd.sjoin(base, fz, predicate="within", how="inner")
    out["flood_zone"] = j.groupby(level=0)["lvl"].max().reindex(pts.index).fillna(1).astype(int)

    ptal = gpd.read_parquet(sp / "ptal-2023-grid.parquet").to_crs(27700)[["AI", "PTAL_2023", "geometry"]]
    j = gpd.sjoin_nearest(base, ptal, how="left", max_distance=150)
    j = j[~j.index.duplicated()]
    order = {"0": 0, "1a": 1, "1b": 2, "2": 3, "3": 4, "4": 5, "5": 6, "6a": 7, "6b": 8}
    out["ptal_ai"] = j["AI"]
    out["ptal_level"] = j["PTAL_2023"]
    out["ptal_ordinal"] = j["PTAL_2023"].map(order)

    lsoa = gpd.read_parquet(sp / "lsoa-2021.parquet").to_crs(27700)[["LSOA21CD", "geometry"]]
    j = gpd.sjoin(base, lsoa, predicate="within", how="left")
    j = j[~j.index.duplicated()]
    imd = pd.read_csv(sp / "imd-2025.csv", usecols=[
        "LSOA code (2021)", "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)",
        "Index of Multiple Deprivation (IMD) Score"])
    imd = imd.rename(columns={
        "LSOA code (2021)": "lsoa21",
        "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)": "imd_decile",
        "Index of Multiple Deprivation (IMD) Score": "imd_score"})
    out["lsoa21"] = j["LSOA21CD"]
    return out.join(imd.set_index("lsoa21"), on="lsoa21")


# ---------------------------------------------------------------- main

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--foundations", help="path to the Foundations CSV (default: search project root, data/raw)")
    args = p.parse_args()
    fp_path = args.foundations or next(iter(sorted(glob.glob("foundations_london_housing_*.csv")
                                                   + glob.glob(str(RAW / "foundations_london_housing_*.csv")))), None)
    if not fp_path:
        raise SystemExit("Foundations CSV not found; pass --foundations PATH")
    OUT.mkdir(parents=True, exist_ok=True)
    report = []

    def step(name, df):
        report.append((name, len(df)))
        print(f"{name}: {len(df):,}", flush=True)

    fp = pd.read_csv(fp_path, low_memory=False)
    step("Foundations rows", fp)
    fp["lpa"] = fp["area_name"].replace(BOROUGH_MAP)
    fp["nref"] = fp["uid"].map(norm_ref)
    fp = fp.drop_duplicates(["lpa", "nref"])
    fp_keys = set(zip(fp["lpa"], fp["nref"]))
    fp["outcome"] = fp["status"].map(OUTCOME)
    fp = fp[fp["outcome"].notna()]
    step("Foundations: decided or withdrawn (drop undecided/other)", fp)

    print("Loading PLD ...", flush=True)
    pld = load_pld()
    df_fp = fp.merge(pld, on=["lpa", "nref"], how="left")
    df_fp["label_source"] = "foundations"

    # PLD-only applications (not in Foundations at all), labelled from PLD's own decision
    not_in_fp = np.array([k not in fp_keys for k in zip(pld["lpa"], pld["nref"])])
    pld_only = pld[not_in_fp & pld["pld_outcome"].notna().to_numpy()].copy()
    pld_only["uid"] = pld_only["pld_id"].str.split("-", n=1).str[1]
    pld_only["description"] = pld_only["pld_description"]
    pld_only["decision"] = pld_only["pld_outcome"]
    pld_only["outcome"] = pld_only["pld_outcome"]
    pld_only["start_date"] = pd.to_datetime(pld_only["pld_valid_date"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    pld_only["label_source"] = "pld"
    pld_only = pld_only[pld_only["start_date"].notna()]
    step("PLD-only: decided or withdrawn, not in Foundations", pld_only)
    df = pd.concat([df_fp, pld_only], ignore_index=True)
    df["in_pld"] = df["pld_app_type"].notna()

    desc = df["description"].fillna("").str.lower()
    followup = desc.str.contains(FOLLOWUP_RE, regex=True)
    fp_proposal = df["app_type"].isin(["Full", "Outline"]) & ~df["uid"].str.contains(FP_NON_PROPOSAL_SUFFIX, regex=True)
    pld_proposal = df["pld_app_type"].fillna("").str.contains(PLD_PROPOSAL_TYPES, regex=True)
    df = df[np.where(df["in_pld"], pld_proposal, fp_proposal) & ~followup]
    step("New full/outline proposals (drop householder, discharges, amendments, variations, LDCs, prior approvals)", df)

    # Homes: PLD unit list, else Foundations n_dwellings (majors only)
    df["homes_net"] = np.where(df["homes_gained"] > 0, df["homes_gained"] - df["homes_lost"].fillna(0), np.nan)
    use_fp = df["homes_net"].isna() & df["n_dwellings"].notna()
    for col in ("homes_net", "homes_gained"):
        df.loc[use_fp, col] = df.loc[use_fp, "n_dwellings"]
    df["homes_source"] = np.where(use_fp, "foundations", np.where(df["homes_net"].notna(), "pld", None))
    # Last resort: home count stated in the description. A conversion of one house loses one home.
    text_homes = df["description"].fillna("").str.lower().map(parse_homes)
    use_text = df["homes_net"].isna() & text_homes.notna()
    conv = df["description"].fillna("").str.lower().str.contains(r"conver|subdivi|sub-divi")
    df.loc[use_text, "homes_gained"] = text_homes[use_text]
    df.loc[use_text, "homes_lost"] = np.where(conv[use_text], 1, 0)
    df.loc[use_text, "homes_net"] = df.loc[use_text, "homes_gained"] - df.loc[use_text, "homes_lost"]
    df.loc[use_text, "homes_source"] = "text"
    df = df[df["homes_net"] >= 1].copy()
    step("Creating at least 1 net home", df)

    # Text features
    tf = text_features(df["description"])
    df = pd.concat([df, tf], axis=1)

    # Storeys / height cleaning
    st = df["pld_storeys"].where((df["pld_storeys"] >= 1) & (df["pld_storeys"] <= 60))
    df["storeys"] = st.fillna(df["text_storeys"])
    df["storeys_source"] = np.where(st.notna(), "pld", np.where(df["text_storeys"].notna(), "text", None))
    ratio = df["pld_height_m"] / df["storeys"]
    ok_h = (ratio.between(2.4, 6.0)) | (df["storeys"].isna() & df["pld_height_m"].between(2.5, 250))
    df["height_m"] = df["pld_height_m"].where(ok_h)
    df["height_m_est"] = df["height_m"].fillna(df["storeys"] * 3.2)

    # Site area: PLD polygon area first, else stated
    def to_shape(s):
        try:
            return shapely.geometry.shape(json.loads(s)) if isinstance(s, str) else None
        except (ValueError, TypeError, AttributeError, shapely.errors.GEOSException):
            return None

    poly = df["pld_polygon"].map(to_shape)
    poly_area = gpd.GeoSeries(poly, crs=4326).to_crs(27700).area.where(poly.notna())
    poly_area = poly_area.where(poly_area.between(10, 5e6))
    df["site_area_m2"] = poly_area.fillna(df["site_area_m2_stated"].where(df["site_area_m2_stated"].between(10, 5e6)))
    df.loc[df["site_area_m2"] < 50, "site_area_m2"] = np.nan  # smaller than a single plot: bad data

    # Habitable rooms: 1-10 per home, otherwise treat as bad data
    hab_per_home = df["habitable_rooms"] / df["homes_gained"]
    bad_hab = ~hab_per_home.between(1, 10)
    df.loc[bad_hab, ["habitable_rooms", "affordable_pct_habrooms"]] = np.nan

    # Sanity checks on floor area
    # Below 30 m²/home is under any London space standard (studio minimum 37 m²): bad data.
    # Above 200 m²/home is capped (large houses, or GIA that includes non-residential space).
    per_home = df["resi_gia_m2"] / df["homes_gained"]
    df["resi_gia_m2"] = df["resi_gia_m2"].where(per_home.between(30, 400))
    df["avg_home_size_m2"] = (df["resi_gia_m2"] / df["homes_gained"]).clip(upper=200)
    df["density_homes_per_ha"] = df["homes_net"] / (df["site_area_m2"] / 10_000)
    df["density_habrooms_per_ha"] = df["habitable_rooms"] / (df["site_area_m2"] / 10_000)
    df.loc[df["density_homes_per_ha"] > 1000, ["density_homes_per_ha", "density_habrooms_per_ha"]] = np.nan

    # Scheme type
    df["scheme_type"] = np.select(
        [(df["student_units"].fillna(0) > 0) | df["has_student"],
         (df["coliving_units"].fillna(0) > 0) | df["has_coliving"],
         (df["hmo_units"].fillna(0) > 0) | df["has_hmo"]],
        ["student", "coliving", "hmo"], "standard")
    df["has_gym"] = df["has_gym"] | df["has_sport_use_class"].fillna(False).astype(bool)

    # Location: Foundations lat/lng, else PLD centroid
    in_london = lambda la, lo: la.between(51.2, 51.8) & lo.between(-0.6, 0.4)
    fp_ok = in_london(df["lat"], df["lng"])
    pld_ok = in_london(df["pld_lat"], df["pld_lng"])
    df["lat"] = np.where(fp_ok, df["lat"], np.where(pld_ok, df["pld_lat"], np.nan))
    df["lng"] = np.where(fp_ok, df["lng"], np.where(pld_ok, df["pld_lng"], np.nan))
    df = df[df["lat"].notna()].copy()
    step("With a location", df)
    df = df.reset_index(drop=True)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(df["lng"], df["lat"]), crs=4326, index=df.index).to_crs(27700)
    print("Spatial joins ...", flush=True)
    sf = spatial_features(pts)
    df = pd.concat([df, sf], axis=1)

    # Derived flags and labels
    df["size_band"] = pd.cut(df["homes_net"], [0, 9, 49, 149, np.inf], labels=["1-9", "10-49", "50-149", "150+"])
    df["is_major"] = df["homes_net"] >= 10
    # Mayor of London Order 2008: Category 1A is MORE THAN 150 homes; Category 1C height is over 30 m
    # outside the City and over 150 m in the City (the 25 m Thames-side rule is not modelled).
    df["mayor_1a_over_150_homes"] = df["homes_net"] > 150
    df["mayor_1c_height"] = np.where(df["lpa"] == "City of London", df["height_m_est"] > 150, df["height_m_est"] > 30)
    df["mayor_referable"] = df["mayor_1a_over_150_homes"] | df["mayor_1c_height"]
    # Statutory major residential development: 10+ dwellings, or a site of 0.5 ha or more
    df["statutory_major"] = (df["homes_net"] >= 10) | (df["site_area_m2"] >= 5000)

    # Affordable housing is only required from 10 homes, and small schemes show implausible 100%
    # affordable values (likely a data-entry default), so tenure is treated as unknown below 10 homes.
    small = ~df["is_major"]
    df.loc[small, ["affordable_pct_units", "affordable_pct_habrooms", "social_rent_share_of_affordable",
                   "low_cost_rent_share_of_affordable"]] = np.nan
    df["social_rent_pct_units"] = np.where(
        df["affordable_pct_units"] == 0, 0.0,
        df["affordable_pct_units"] * df["social_rent_share_of_affordable"])
    df["premium_amenity"] = df["has_gym"] | df["has_pool"] | df["has_concierge"]
    df["is_outline"] = df["app_type"].eq("Outline") | df["pld_app_type"].fillna("").str.startswith("Outline")
    df["year"] = df["start_date"].str[:4].astype(int)
    df["site_group"] = df["lat"].round(4).astype(str) + "," + df["lng"].round(4).astype(str)

    df["y_approved"] = (df["outcome"] == "approved").astype(int)  # withdrawn counts as not approved
    df["y_approved_decided"] = np.where(df["outcome"] == "withdrawn", np.nan, df["y_approved"])
    s106 = df["decision"].fillna("").str.contains(S106_RE, case=False, regex=True)
    # S106 comes from Foundations decision text only; PLD's s106_agreement flag is too sparse to use
    df["y_s106"] = np.where((df["outcome"] == "approved") & (df["label_source"] == "foundations"),
                            s106.astype(float), np.nan)

    id_cols = ["uid", "lpa", "nref", "pld_id", "url", "description", "description_at_submission", "decision", "status",
               "outcome", "label_source",
               "start_date", "year", "site_group", "lat", "lng", "homes_source", "storeys_source", "in_pld", "lsoa21"]
    label_cols = ["y_approved", "y_approved_decided", "y_s106"]
    feature_cols = [
        # proposal
        "homes_net", "homes_gained", "homes_lost", "size_band", "is_major", "is_outline",
        "mix_studio", "mix_1b", "mix_2b", "mix_3b_plus", "habitable_rooms",
        "affordable_pct_units", "affordable_pct_habrooms", "social_rent_share_of_affordable",
        "low_cost_rent_share_of_affordable", "social_rent_pct_units", "tenure_known_share",
        "storeys", "height_m", "height_m_est", "n_buildings", "site_area_m2", "resi_gia_m2", "avg_home_size_m2",
        "density_homes_per_ha", "density_habrooms_per_ha", "nonresi_gia_gained_m2",
        "car_spaces", "cycle_spaces", "dev_type", "scheme_type",
        "has_gym", "has_pool", "has_basement", "has_roof_terrace", "has_concierge", "has_communal_amenity",
        "has_commercial", "has_demolition", "has_affordable_mention", "premium_amenity",
        "gym_removed", "pool_removed", "has_backland", "has_pub_loss", "has_studio",
        # site
        "lpa", "in_conservation_area", "in_article4_area", "in_tpo_zone", "in_green_belt",
        "in_opportunity_area", "in_sil", "in_town_centre", "listed_building_within_25m",
        "brownfield_site_within_50m", "flood_zone", "ptal_ai", "ptal_ordinal", "ptal_level",
        "imd_decile", "imd_score", "mayor_referable", "mayor_1a_over_150_homes", "mayor_1c_height",
        "statutory_major", "space_std_share_below",
    ]
    feats = df[list(dict.fromkeys(id_cols + label_cols + feature_cols))]
    feats.to_parquet(OUT / "features.parquet", index=False)
    step("Final rows written", feats)

    # ---- report: counts, outcomes, missingness and leakage audit
    lines = ["# Feature build report", "", f"Foundations file: `{fp_path}`", "", "## Rows at each step", "",
             "| Step | Rows |", "|---|---|"]
    lines += [f"| {n} | {c:,} |" for n, c in report]
    lines += ["", "## Outcomes", "", feats.groupby(["size_band", "outcome"], observed=True).size()
              .unstack(fill_value=0).to_markdown(), "",
              f"- PLD match rate: {feats['in_pld'].mean():.1%}",
              f"- S106 label among approved: {feats['y_s106'].mean():.1%} "
              f"(major {feats.loc[feats.is_major, 'y_s106'].mean():.1%}, minor {feats.loc[~feats.is_major, 'y_s106'].mean():.1%})",
              "", "Small samples: " + ", ".join(f"{c} = {int(feats[c].sum())}" for c in
                                                ["has_gym", "has_pool", "has_concierge", "in_sil", "in_tpo_zone"]),
              "", "## Leakage audit: % missing by outcome",
              "", "Features whose missing rate differs by more than 10 points between outcomes are flagged: "
              "the field may be filled in after the decision.", ""]
    miss = feats[feature_cols].isna().groupby(feats["outcome"]).mean().T * 100
    miss["spread"] = miss.max(axis=1) - miss.min(axis=1)
    miss["FLAG"] = np.where(miss["spread"] > 10, "LEAK?", "")
    lines.append(miss.round(1).to_markdown())
    (OUT / "build_report.md").write_text("\n".join(lines) + "\n")
    print(f"Report: {OUT / 'build_report.md'}")
    flagged = miss.index[miss["FLAG"] != ""].tolist()
    if flagged:
        print("Possible leakage (missingness differs by outcome):", flagged)


if __name__ == "__main__":
    main()

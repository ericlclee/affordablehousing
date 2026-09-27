"""
build_council_stats.py  -  writes proposal106/data/council_stats.json

Usage (from anywhere):
  .venv/bin/python analysis/build_council_stats.py <land_value_xlsx> <uk_hpi_csv>
  .venv/bin/python analysis/build_council_stats.py --observed-only    (refresh 'observed' in the existing JSON)

observed: foundations.parquet, cleaned exactly as analysis/sim_parameters.py
          (AMEND_RE / DISCH_RE reclassification of mislabelled Full/Outline rows;
           ok = 1 Permitted/Conditions, 0 Rejected). Restricted to app_type Full/Outline
           (after reclassification) with n_dwellings >= 10, then to full applications only:
           NOT_FULL_RE drops reserved matters, EIA screening/scoping, prior approval / Class MA,
           neighbouring-authority consultations and lawful-development certificates, and rows whose
           statutory period is under 13 weeks (a 10+ home full application is a major: 13 weeks).
           Date check: days_to_decision = decided_date - start_date on every row; the short medians
           came from those non-full application types, not from date errors.
"""
import ast
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "foundations.parquet"
OUT = ROOT / "proposal106" / "data" / "council_stats.json"
OBSERVED_ONLY = sys.argv[1:2] == ["--observed-only"]
if not OBSERVED_ONLY:
    LV_XLSX, HPI_CSV = sys.argv[1], sys.argv[2]
NOT_FULL_RE = (r"reserved matters|screening opinion|scoping opinion|prior approval|prior notification|class ma\b"
               r"|schedule 2,? part 3|consultation from|neighbouring (borough|authority)|lawful development|certificate of lawful")

BOROUGHS = ["Barking and Dagenham", "Barnet", "Bexley", "Brent", "Bromley", "Camden", "City of London",
            "Croydon", "Ealing", "Enfield", "Greenwich", "Hackney", "Hammersmith and Fulham", "Haringey",
            "Harrow", "Havering", "Hillingdon", "Hounslow", "Islington", "Kensington and Chelsea",
            "Kingston upon Thames", "Lambeth", "Lewisham", "Merton", "Newham", "Redbridge",
            "Richmond upon Thames", "Southwark", "Sutton", "Tower Hamlets", "Waltham Forest",
            "Wandsworth", "Westminster"]

# ---- reuse the regexes from sim_parameters.py verbatim (parsed, not re-typed) ----
src = (ROOT / "analysis" / "sim_parameters.py").read_text()
consts = {}
for node in ast.parse(src).body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and getattr(node.targets[0], "id", "") in ("AMEND_RE", "DISCH_RE"):
        consts[node.targets[0].id] = ast.literal_eval(node.value)
AMEND_RE, DISCH_RE = consts["AMEND_RE"], consts["DISCH_RE"]

# PlanIt area_name -> canonical borough. 'Old Oak Park Royal' (OPDC) and 'London Legacy' (LLDC)
# are separate planning authorities: skipped.
AREA_MAP = {"City": "City of London", "Kensington": "Kensington and Chelsea",
            "Kingston": "Kingston upon Thames", "Richmond": "Richmond upon Thames"}
SKIP = {"Old Oak Park Royal", "London Legacy"}

con = duckdb.connect()
con.execute(f"create table raw as select * from read_parquet('{PARQUET.as_posix()}')")
con.execute(f"""
create table f as
with r2 as (
  select * replace (
    case when app_type in ('Full','Outline') and regexp_matches(lower(coalesce(description,'')), '{AMEND_RE}') then 'Amendment'
         when app_type in ('Full','Outline') and regexp_matches(lower(coalesce(description,'')), '{DISCH_RE}') then 'Conditions'
         else app_type end as app_type)
  from raw)
select area_name,
  case when status in ('Permitted','Conditions') then 1 when status = 'Rejected' then 0 end as ok,
  (status = 'Withdrawn')::int as wd,
  case when status in ('Permitted','Conditions','Rejected','Withdrawn') then 1 end as closed,
  case when days_to_decision >= 0 then days_to_decision end as days,
  case when n_dwellings >= 150 then '150+' when n_dwellings >= 50 then '50-149' else '10-49' end as band,
  description
from r2 where app_type in ('Full','Outline') and n_dwellings >= 10
  and not regexp_matches(lower(coalesce(description,'')), '{NOT_FULL_RE}')
  and (n_statutory_days is null or n_statutory_days >= 89)
""")

AGG = """count(ok) as n, count(*) as n_all, sum(wd) as n_withdrawn,
  round(100 * (1 - avg(ok)), 1) as refusal_pct,
  round(100 * sum(wd) / nullif(sum(closed), 0), 1) as withdrawn_pct,
  median(days) filter (where ok is not null) as median_days,
  count(days) filter (where ok is not null) as n_with_days"""
by_band = con.execute(f"select area_name, band, {AGG} from f group by all").fetchdf()
by_all = con.execute(f"select area_name, '10+ (all)' as band, {AGG} from f group by all").fetchdf()
lon_band = con.execute(f"select band, {AGG} from f where area_name not in {tuple(SKIP)} group by all").fetchdf()
lon_all = con.execute(f"select '10+ (all)' as band, {AGG} from f where area_name not in {tuple(SKIP)}").fetchdf()


def rec(row):
    md = row["median_days"]
    return {"n": int(row["n"]), "n_all_statuses": int(row["n_all"]), "n_withdrawn": int(row["n_withdrawn"]),
            "refusal_pct": None if pd.isna(row["refusal_pct"]) else float(row["refusal_pct"]),
            "withdrawn_pct": None if pd.isna(row["withdrawn_pct"]) else float(row["withdrawn_pct"]),
            "median_days": None if pd.isna(md) else float(round(md)),
            "n_with_days": int(row["n_with_days"]), "low_n": bool(int(row["n"]) < 10)}


EMPTY = {"n": 0, "n_all_statuses": 0, "n_withdrawn": 0, "refusal_pct": None, "withdrawn_pct": None,
         "median_days": None, "n_with_days": 0, "low_n": True}
BANDS = ["10-49", "50-149", "150+", "10+ (all)"]
obs = {b: {k: dict(EMPTY) for k in BANDS} for b in BOROUGHS}
for df in (by_band, by_all):
    for _, r in df.iterrows():
        if r["area_name"] in SKIP:
            continue
        name = AREA_MAP.get(r["area_name"], r["area_name"])
        assert name in obs, r["area_name"]
        obs[name][r["band"]] = rec(r)
london_obs = {r["band"]: rec(r) for df in (lon_band, lon_all) for _, r in df.iterrows()}

# ---- height signal check (podium vs tower): storeys only exist as free text in description ----
storey = con.execute(r"""
select count(*) n, count(*) filter (where regexp_matches(lower(coalesce(description,'')), '\d+\s*(-|\s)?(storey|story|stories|floors)')) n_storeys
from f where area_name not in ('Old Oak Park Royal','London Legacy')""").fetchone()

METHOD = ("Cleaning as analysis/sim_parameters.py: Full/Outline rows whose description matches AMEND_RE -> "
          "'Amendment', DISCH_RE -> 'Conditions' (removed). Kept app_type Full or Outline with n_dwellings >= 10, "
          "full applications only: NOT_FULL_RE removes reserved matters, EIA screening/scoping opinions, prior approval / Class MA, "
          "neighbouring-authority consultations and lawful-development certificates, and rows with a statutory period under "
          "13 weeks (n_statutory_days < 89). Dates checked: days_to_decision equals decided_date - start_date on every row. "
          "n = decided (status Permitted/Conditions/Rejected); refusal_pct = Rejected / decided; "
          "withdrawn_pct = Withdrawn / (decided + Withdrawn); median_days = median days_to_decision (>= 0) "
          "over decided rows. Undecided rows excluded, so medians for recent large schemes are biased low. "
          "area_name mapping: City->City of London, Kensington->Kensington and Chelsea, Kingston->Kingston upon Thames, "
          "Richmond->Richmond upon Thames; 'Old Oak Park Royal' (OPDC) and 'London Legacy' (LLDC) skipped. "
          "'10+ (all)' is the pooled 10+ dwellings figure; '_london' pools the 33 boroughs.")
if OBSERVED_ONLY:
    cur = json.loads(OUT.read_text())
    for b in BOROUGHS:
        cur[b]["observed"] = obs[b]
    cur["_london"]["observed"] = london_obs
    cur["_sources"]["observed"]["method"] = METHOD
    cur["_sources"]["observed"]["small_n_warning"] = ("Many borough x band cells have n < 10 (the 150+ band especially); "
                                                      "the app headlines a borough median only when n >= 10 and it is at least 91 days.")
    OUT.write_text(json.dumps(cur, indent=1, ensure_ascii=False))
    print("refreshed observed in", OUT)
    sys.exit(0)

# ---- land values (MHCLG, Oct 2023 values, published Mar 2026) ----
lv = pd.read_excel(LV_XLSX, sheet_name="Residential", header=None)
hdr = lv.iloc[4]
assert str(hdr[14]).startswith("50") and "Medium" in str(lv.iloc[3, 12])
lvl = lv[lv[1] == "London"].set_index(3)
land = {}
for b in BOROUGHS:
    r = lvl.loc[b]
    land[b] = {"medium_density_median": int(r[14]), "low_density_median": int(r[9]), "high_density_median": int(r[19]),
               "density_dph": {"low": int(r[4]), "medium": int(r[5]), "high": int(r[6])}}

# ---- UK HPI ----
hpi = pd.read_csv(HPI_CSV, usecols=["Date", "RegionName", "AreaCode", "AveragePrice"])
hpi["Date"] = pd.to_datetime(hpi["Date"], format="%d/%m/%Y")
lon = hpi[hpi.AreaCode.str.startswith("E09") | (hpi.AreaCode == "E12000007")]
latest = lon.Date.max()
m = lon[lon.Date == latest].copy()
m["RegionName"] = m["RegionName"].replace({"City of Westminster": "Westminster"})
price = dict(zip(m.RegionName, m.AveragePrice))
london_price = int(price.pop("London"))

# ---- Mayoral CIL (MCIL2 Table 1, Annual CIL Rate Summary 2026) ----
MCIL_RATE_2026 = {1: 96.97, 2: 72.73, 3: 30.30}
MCIL_ADOPTED_2019 = {1: 80, 2: 60, 3: 25}
MCIL_BAND = {**{b: 1 for b in ["Camden", "City of London", "Westminster", "Hammersmith and Fulham", "Islington",
                                "Kensington and Chelsea", "Richmond upon Thames", "Wandsworth"]},
             **{b: 2 for b in ["Barnet", "Brent", "Bromley", "Ealing", "Enfield", "Hackney", "Haringey", "Harrow",
                                "Hillingdon", "Hounslow", "Kingston upon Thames", "Lambeth", "Lewisham", "Merton",
                                "Redbridge", "Southwark", "Tower Hamlets", "Waltham Forest"]},
             **{b: 3 for b in ["Barking and Dagenham", "Bexley", "Croydon", "Greenwich", "Havering", "Newham", "Sutton"]}}
assert sorted(MCIL_BAND) == sorted(BOROUGHS)

out = {}
for b in BOROUGHS:
    band = MCIL_BAND[b]
    out[b] = {
        "observed": obs[b],
        "land_value_per_ha_2023": land[b]["medium_density_median"],
        "land_value_detail": land[b],
        "avg_house_price": int(price[b]),
        "london_avg_house_price": london_price,
        "house_price_month": latest.strftime("%Y-%m"),
        "mcil_band": band,
        "mcil_rate_2026": MCIL_RATE_2026[band],
        "mcil_rate_adopted_2019": MCIL_ADOPTED_2019[band],
    }

ACCESSED = "2026-09-26"
out["_london"] = {"observed": london_obs, "avg_house_price": london_price, "house_price_month": latest.strftime("%Y-%m")}
out["_sources"] = {
    "observed": {
        "file": "data/foundations.parquet (Foundations / PlanIt London planning applications, start dates 2022-2025)",
        "method": METHOD,
        "small_n_warning": "Many borough x band cells have n < 10 (the 150+ band especially); treat them as indicative only.",
        "height_data": (f"No storeys/height field exists. Only {storey[1]} of {storey[0]} kept rows "
                        f"({round(100 * storey[1] / storey[0])}%) mention storeys/floors in free-text description."),
    },
    "land_value_per_ha_2023": {
        "url": "https://assets.publishing.service.gov.uk/media/69b2d95f912f3f96bf687b1c/Land_value_estimates_for_policy_appraisal_2023.xlsx",
        "publisher": "MHCLG, Land value estimates for policy appraisal 2023 (published March 2026, valuation date 1 Oct 2023)",
        "sheet": "Residential",
        "column": "Medium site density, across the house price distribution: (£/ha) -> '50 (Median)'",
        "detail_columns": "land_value_detail: low/medium/high site density '50 (Median)' columns and the sheet's 'Site Density (dwellings/ha)' Low/Medium/High",
        "units": "GBP per hectare, residential land with planning permission",
        "accessed": ACCESSED,
    },
    "avg_house_price": {
        "url": "https://publicdata.landregistry.gov.uk/market-trend-data/house-price-index-data/UK-HPI-full-file-2026-07.csv",
        "publisher": "HM Land Registry / ONS UK House Price Index, full file",
        "column": "AveragePrice (all property types, not seasonally adjusted)",
        "month": latest.strftime("%Y-%m"),
        "note": "UK-HPI-full-file-2026-08.csv returned 404 on the access date, so 2026-07 is the latest. 'City of Westminster' mapped to Westminster; London = region E12000007.",
        "accessed": ACCESSED,
    },
    "mcil": {
        "url": "https://www.london.gov.uk/media/111917/download",
        "document": "Mayoral Community Infrastructure Levy (MCIL): Annual CIL Rate Summary 2026, Table 1 (MCIL2 charging rates for all development)",
        "rates": "mcil_rate_2026 = MCIL2 rate indexed for permissions granted in calendar year 2026 (GBP per sq m; Ip 400 / Ic 330). Band 1 GBP 96.97, Band 2 GBP 72.73, Band 3 GBP 30.30 (adopted 2019: 80/60/25).",
        "note": "All 33 boroughs are listed by name in Table 1, so no band is null. Excludes Central London/Isle of Dogs office, retail and hotel rates (Table 2).",
        "accessed": ACCESSED,
    },
}

OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("wrote", OUT)
print("storeys mention:", storey)

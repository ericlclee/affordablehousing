"""Merge councils_part1-3.json (policy) + council_stats.json (numbers) -> councils.json keyed by borough name.
Names are checked against london-boroughs.geojson properties.name so point-in-polygon finds the pack."""
import json, re, sys, pathlib

D = pathlib.Path(sys.argv[1])
parts = []
for i in (1, 2, 3):
    d = json.loads((D / f"councils_part{i}.json").read_text())
    if isinstance(d, dict):
        d = d.get("councils", d)
        d = list(d.values()) if isinstance(d, dict) else d
    parts += d
stats = json.loads((D / "council_stats.json").read_text())
geo = json.loads((D / "london-boroughs.geojson").read_text())
geo_names = {f["properties"]["name"] for f in geo["features"]}

STAT_KEYS = ["observed", "land_value_per_ha_2023", "land_value_detail", "avg_house_price", "london_avg_house_price",
             "house_price_month", "mcil_band", "mcil_rate_2026", "mcil_rate_adopted_2019"]
src = stats.get("_sources", {})
STAT_SOURCES = [u for u in [src.get("land_value_per_ha_2023", {}).get("url"), src.get("avg_house_price", {}).get("url"),
                            src.get("mcil", {}).get("url")] if u]
london = stats.get("_london", {})


# Site-level minimum affordable % on private land, read by hand from each affordable_target_note.
# Only where the note states a per-site minimum or threshold; strategic (borough-wide) targets are left out (None).
SITE_MIN = {"Barnet": 35, "Bexley": 35, "Bromley": 35, "City of London": 30, "Croydon": 30, "Ealing": 50, "Enfield": 40,
            "Greenwich": 35, "Hackney": 50, "Haringey": 40, "Harrow": 35, "Havering": 35, "Hillingdon": 35,
            "Kensington and Chelsea": 35, "Kingston upon Thames": 50, "Lewisham": 35, "Merton": 35, "Newham": 35,
            "Redbridge": 35, "Richmond upon Thames": 50, "Southwark": 35, "Sutton": 35, "Tower Hamlets": 35,
            "Waltham Forest": 35, "Westminster": 35}


def nums(s):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(s).replace(",", ""))]


def money(v):
    return f"£{int(v)}" if float(v).is_integer() else f"£{v:g}"


def blank(v):
    return v is None or (isinstance(v, str) and v.strip().lower() in ("", "none", "null", "n/a", "not found"))


out, problems = {}, []
for p in parts:
    name = p["name"].strip()
    if name not in geo_names:
        problems.append(f"policy name not in geojson: {name}")
    c = dict(p)
    c["name"] = name
    # local plan: the app reads local_plan.year (falls back to year_adopted); give both
    lp = dict(c.get("local_plan") or {})
    if lp.get("year") is None and lp.get("year_adopted") is not None:
        lp["year"] = lp["year_adopted"]
    c["local_plan"] = lp
    # 'None' strings -> null so the card shows 'not researched' instead of the word None
    for k in ("tall_building_definition", "affordable_target_note", "borough_cil_note", "priorities"):
        if blank(c.get(k)):
            c[k] = None
    # affordable target as a number
    if isinstance(c.get("affordable_target_pct"), str):
        n = nums(c["affordable_target_pct"])
        c["affordable_target_pct"] = n[0] if n else None
    c["affordable_site_min_pct"] = SITE_MIN.get(name)
    # Borough CIL: one number when flat, '£a–£b' + numeric min/max when zoned
    raw = c.get("borough_cil_resi_per_m2")
    lo, hi = c.get("borough_cil_resi_min"), c.get("borough_cil_resi_max")
    if lo is None or hi is None:
        n = [raw] if isinstance(raw, (int, float)) else nums(raw) if raw is not None else []
        if n:
            lo, hi = min(n[:2]), max(n[:2])
    if lo is not None and hi is not None:
        lo, hi = (int(x) if float(x).is_integer() else x for x in (lo, hi))
        if lo == hi:
            c["borough_cil_resi_per_m2"] = lo
            c.pop("borough_cil_resi_min", None); c.pop("borough_cil_resi_max", None)
        else:
            c["borough_cil_resi_per_m2"] = f"{money(lo)}–{money(hi)}"
            c["borough_cil_resi_min"], c["borough_cil_resi_max"] = lo, hi
    else:
        c["borough_cil_resi_per_m2"] = None
    # numbers from council_stats
    s = stats.get(name)
    if s is None:
        problems.append(f"no stats for {name}")
        s = {}
    for k in STAT_KEYS:
        c[k] = s.get(k)
    if c.get("london_avg_house_price") is None:
        c["london_avg_house_price"] = london.get("avg_house_price")
    c["sources"] = list(dict.fromkeys((c.get("sources") or []) + STAT_SOURCES))
    out[name] = c

missing = geo_names - set(out)
if missing:
    problems.append(f"geojson boroughs without a pack: {sorted(missing)}")
(D / "councils.json").write_text(json.dumps(dict(sorted(out.items())), ensure_ascii=False, indent=1))
print(len(out), "councils written;", "problems:", problems or "none")

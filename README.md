# House London: approval and S106 prediction

Predicts, for a proposed London housing scheme, **P(approved)** and **P(S106 | approved)** from proposal parameters (storeys, homes, floor area, tenure, amenities such as gym or pool) plus site context (conservation area, flood zone, PTAL, Opportunity Area, deprivation).

## Setup

```bash
./setup.sh
source .venv/bin/activate
```

Needs Python 3.11+. Data goes in `data/`, which is gitignored: never commit it.

## Get the data

| Step | Command | Time | Output |
|---|---|---|---|
| 1. Planning London Datahub (GLA), applications validated 2022–2025 | `python scripts/download_pld.py` | ~8 min | `data/raw/pld/*.jsonl.gz` (447k applications, 220 MB) |
| 2. Site-context layers | `python scripts/download_spatial.py` | ~15–30 min | `data/raw/spatial/*.parquet` |
| 3. Foundations applications (hackathon file) | copy manually | — | `foundations_london_housing_2022_2025_*.csv` in the project root |

Then build the model table (~1 min):

```bash
python scripts/build_features.py
```

This writes `data/processed/features.parquet` (one row per new housing proposal: labels, proposal features, site features) and `data/processed/build_report.md` (rows kept at each step, outcome counts, and a leakage audit of each feature's missing rate by outcome). Don't use the habitable-room features (`habitable_rooms`, `affordable_pct_habrooms`, `density_habrooms_per_ha`) as model inputs: the audit flags them because they're missing far more often for approved schemes. Use `affordable_pct_units` instead.

Both download scripts are safe to re-run: `download_pld.py` resumes from the last saved record, and `download_spatial.py` skips layers that already exist (`--force` to redo, `--only <layer>` for one layer, `--list` to see names).

The Foundations file comes from the hackathon organisers ([Foreman/Foundations](https://foreman.house-london.uk/)); it is not publicly downloadable by script. The London EPC file (`london-domestic-epc.csv`) is not needed for the model.

Full details: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) (every source, access method, snapshot date, join logic) and [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md) (every column in `features.parquet`, its source, and whether it's a model input).

## What each dataset is for

| Dataset | Source | Role |
|---|---|---|
| Foundations (182k applications) | Hackathon file, PlanIt-based | **Labels**: approved/refused from `status`; S106 from `decision` text ("subject to S106 / legal agreement"). Description text for amenity flags |
| PLD applications | [GLA Planning London Datahub API](https://www.london.gov.uk/programmes-strategies/planning/digital-planning/planning-london-datahub) | **Proposal features**: units, tenure mix, bedrooms, storeys, height, GIA, site area, use classes, parking, `s106_agreement` |
| conservation-area, article-4-direction-area, listed-building-outline, green-belt, brownfield-land, tree-preservation-zone, flood-risk-zone | [planning.data.gov.uk](https://www.planning.data.gov.uk/) | Constraint flags (point-in-polygon) |
| opportunity-areas, strategic-industrial-land, town-centres | London Datastore | London Plan designations |
| ptal-2023-grid | TfL (100 m grid) | Public transport accessibility |
| lsoa-2021 + imd-2025 | ONS boundaries + MHCLG Indices of Deprivation 2025 | Deprivation decile |
| mayor-referrals-2011-2024 | London Datastore | Referred-to-Mayor flag (150+ homes or 30 m+) |

## How the data joins

1. **Foundations is the spine** (one row per application). Drop `app_type = Conditions` / amendments; keep decided rows. `approved = status in {Permitted, Conditions}`, `refused = Rejected`.
2. **Foundations → PLD** on `(borough, normalised reference)`. Normalise by upper-casing and stripping punctuation (`23/AP/1312` → `23AP1312`). Borough names differ (`Kensington` vs `Kensington & Chelsea`, `City` vs `City of London`, `London Legacy` vs `LLDC`, `Old Oak Park Royal` vs `OPDC`). Tested match rate: 97–100% overall, 98.6–100% for schemes of 10+ homes (Croydon, Southwark, Camden, Barnet, 2023).
3. **Flatten PLD** nested fields: `application_details.residential_details.residential_units[]` (tenure, bedrooms), `building_details[]` (storeys, height), `existing_proposed_floorspace_details[]` (use class, GIA), `parking_details`.
4. **Spatial joins** on Foundations lat/lng (96% present; fall back to PLD `centroid`): point-in-polygon for constraint layers, nearest PTAL cell, LSOA → IMD decile.
5. **Text flags** from descriptions: gym, pool, basement, roof terrace, co-living, student, HMO, demolition; storeys/units parsed as fallback.

## Known data issues

- PLD under-records refusals (94–96% approval), so take approval labels from Foundations and features from PLD.
- PLD `affordable_percentage` is present on every record with a unit count, so it likely defaults to 0; recompute it from tenure counts.
- Storeys is PLD's sparsest proposal field; supplement from description text.
- Don't use post-submission fields as features: `days_to_decision`, `decided_by`, `n_comments`, `n_documents`, `last_changed`, decision dates, final S106 terms.
- Foundations only kept rows with `housing_relevance_score ≥ 0.9`, so Westminster, Tower Hamlets, Islington and Hackney have fewer rows than their real volume.
- Of the planning.data.gov.uk developer-agreement (S106) datasets, only Greenwich and Islington have London data.

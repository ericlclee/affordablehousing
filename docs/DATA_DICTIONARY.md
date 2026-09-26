# Data dictionary: `data/processed/features.parquet`

One row per **new housing proposal**: a full or outline application creating at least one net home, which was approved, refused or withdrawn. Rows come from Foundations (with PLD features joined) plus PLD applications that Foundations doesn't contain (`label_source`). Built by `scripts/build_features.py`; row counts and per-field missing rates are in `data/processed/build_report.md`.

**Source codes:** FP = Foundations, PLD = Planning London Datahub, TEXT = parsed from the Foundations `description`, SPATIAL = spatial join (see [DATA_SOURCES.md](DATA_SOURCES.md)), DERIVED = calculated from other columns.

**Model use:** ✅ planned model input · ⚠️ don't use as a model input (reason given) · — identifier, label or metadata.

## Identifiers and metadata

| Column | Type | Source | Description | Model |
|---|---|---|---|---|
| `uid` | str | FP | Council application reference, e.g. `23/AP/1312` | — |
| `lpa` | str | FP → PLD names | Local planning authority (borough or development corporation), in PLD naming | ✅ (borough) |
| `nref` | str | DERIVED | Normalised reference used for the join (upper-case, punctuation removed) | — |
| `pld_id` | str | PLD | PLD record id (`<LPA>-<reference>`) | — |
| `url` | str | FP | Link to the council's planning record | — |
| `description` | str | FP | Proposal description as submitted | — (source of TEXT features) |
| `description_at_submission` | str | DERIVED | `description` with post-submission wording removed ("amended plans/description", "revised", "withdrawn", "appeal", "approved", "decision"…; pattern `POST_SUBMISSION_RE`). "refuse" is kept: it almost always means bin storage | ✅ offline text model only (`models/approval_with_text.joblib`) |
| `decision` | str | FP | Raw decision text (452 spellings) | — (source of `y_s106`) |
| `status` | str | FP | Normalised status: Permitted / Conditions / Rejected / Withdrawn | — |
| `outcome` | str | DERIVED | `approved` (Permitted or Conditions), `refused` (Rejected) or `withdrawn`. From Foundations `status`, or PLD `decision` for PLD-only rows | — |
| `label_source` | str | DERIVED | `foundations` or `pld`: which dataset supplied the row, its label and its description | ⚠️ provenance, not a proposal property |
| `start_date` | str | FP | Application start date (YYYY-MM-DD) | — |
| `year` | int | DERIVED | Year of `start_date`; used for the train (2022–24) / test (2025) split | ⚠️ can't extrapolate to future years |
| `site_group` | str | DERIVED | Rounded `lat,lng` (4 dp, about 10 m). Keeps applications on the same site together in cross-validation | — |
| `lat`, `lng` | float | FP, else PLD centroid | WGS84 location | ⚠️ would memorise locations |
| `lsoa21` | str | SPATIAL | 2021 Lower Layer Super Output Area code | — |
| `in_pld` | bool | DERIVED | Row matched a PLD record | — |
| `homes_source` | str | DERIVED | Where the home count came from: `pld` or `foundations` (`n_dwellings`, majors only) | — |
| `storeys_source` | str | DERIVED | Where `storeys` came from: `pld`, `text`, or empty | — |

## Labels

| Column | Type | Description |
|---|---|---|
| `y_approved` | 0/1 | 1 = approved. **Withdrawn counts as 0** (the applicant did not get permission) |
| `y_approved_decided` | 0/1/NaN | 1 = approved, 0 = refused, NaN = withdrawn. For the sensitivity check |
| `y_s106` | 0/1/NaN | Approved rows labelled by Foundations only (PLD has no usable S106 field): 1 if the decision text mentions S106 / legal agreement / planning obligation / unilateral undertaking. NaN if not approved. **Under-records S106 for major schemes** (only 32% of approved 10+ home schemes are positive) |

## Proposal: size and type

| Column | Type | Source | Description | Model |
|---|---|---|---|---|
| `homes_net` | float | PLD (else FP) | Homes gained minus homes lost. Always ≥ 1 | ✅ log(1+x) |
| `homes_gained` | float | PLD (else FP) | Residential units gained, excluding superseded units and communal space; includes student and co-living rooms | ⚠️ near-duplicate of `homes_net` |
| `homes_lost` | float | PLD | Residential units lost (demolished or converted) | ✅ log(1+x) |
| `size_band` | category | DERIVED | `1-9`, `10-49`, `50-149`, `150+` net homes | ⚠️ duplicates `homes_net`; for reporting |
| `is_major` | bool | DERIVED | 10+ net homes (the affordable-housing and S106 threshold) | ✅ |
| `is_outline` | bool | FP / PLD | Outline application (details reserved) | ✅ |
| `dev_type` | str | TEXT | `new_build`, `change_of_use`, `conversion`, `extension`, `other`. First matching rule wins, in that order. PLD's own `unit_development_type` is **not used**: it is mostly filled after approval (leakage) | ✅ one-hot |
| `scheme_type` | str | PLD unit types or TEXT | `standard`, `student`, `coliving`, `hmo` | ✅ one-hot (student + co-living merged) |

## Proposal: unit mix and tenure

| Column | Type | Source | Description | Model |
|---|---|---|---|---|
| `mix_studio`, `mix_1b`, `mix_2b`, `mix_3b_plus` | float 0–1 | PLD | Share of gained homes by bedrooms (studio = 0 bedrooms or `Studio Bedsit`) | ✅ (3b+ as reference) |
| `affordable_pct_units` | float 0–100 | PLD | % of gained homes (with known tenure) that are affordable (low-cost rent or intermediate) | ✅ |
| `social_rent_share_of_affordable` | float 0–1 | PLD | Social Rent share of affordable homes. NaN when no affordable homes | ⚠️ 8% coverage; use the planned `social_rent_pct_units` instead |
| `low_cost_rent_share_of_affordable` | float 0–1 | PLD | Low-cost rent (Social Rent, London Affordable Rent, Affordable Rent) share of affordable homes | ⚠️ 8% coverage |
| `tenure_known_share` | float 0–1 | PLD | Share of gained homes with a recognised tenure | ⚠️ data quality, not a proposal property |
| `habitable_rooms` | float | PLD | Total habitable rooms in gained homes (nulled outside 1–10 per home) | ⚠️ **leakage flag**: missing 13% of approved vs 2% of refused |
| `affordable_pct_habrooms` | float 0–100 | PLD | Affordable % by habitable room (the London Plan measure) | ⚠️ **leakage flag** (as above) |

Tenure groups: **market** = Market for sale, Market for rent, Self-Build and Custom Build; **low-cost rent** = Social Rent, London Affordable Rent, Affordable Rent (not at LAR benchmark); **intermediate** = London Shared Ownership, London Living Rent, Discount Market Rent / Sale, Intermediate Other, Shared Equity, Starter Homes.

## Proposal: building and site

| Column | Type | Source | Description | Model |
|---|---|---|---|---|
| `storeys` | float | PLD, else TEXT | Max storeys. PLD values outside 1–60 discarded; text fallback ignores "existing N storey" | ✅ capped 1–40 |
| `height_m` | float | PLD | Max building height in metres; kept only if 2.4–6 m per storey | ⚠️ sparse; duplicates storeys |
| `height_m_est` | float | DERIVED | `height_m`, else storeys × 3.2 m | ⚠️ used only for `mayor_referable` |
| `n_buildings` | float | PLD | Number of buildings in the scheme | ⚠️ 69% coverage |
| `site_area_m2` | float | PLD | Area of the PLD site polygon; else stated site area (hectares if ≤ 50, m² above). Kept if 10 m² – 500 ha | ✅ log |
| `resi_gia_m2` | float | PLD | Gross internal area of the new homes (nulled outside 30–400 m² per home) | ✅ via `avg_home_size_m2` |
| `avg_home_size_m2` | float | DERIVED | `resi_gia_m2` ÷ `homes_gained`, capped at 200 m² | ✅ |
| `space_std_share_below` | float 0–1 | PLD | Share of self-contained new homes whose GIA is below the London Plan Table 3.1 minimum for their bedroom count (studio 37, 1b 50, 2b 61, 3b 74, 4b+ 90 m²; smallest occupancy) | ✅ |
| `density_homes_per_ha` | float | DERIVED | `homes_net` ÷ site area in hectares (nulled above 5,000) | ✅ log |
| `density_habrooms_per_ha` | float | DERIVED | Habitable rooms per hectare | ⚠️ leakage flag (habitable rooms) |
| `nonresi_gia_gained_m2` | float | PLD | Non-residential floorspace gained (use classes not starting with C) | ✅ log(1+x) |
| `car_spaces`, `cycle_spaces` | float | PLD | Proposed parking spaces | ⚠️ 25–28% coverage |

## Proposal: features parsed from the description (TEXT)

Case-insensitive regular expressions on `description`. Full patterns: `TEXT_FLAGS` in `scripts/build_features.py`. `has_backland`, `has_pub_loss` and `has_studio` come from the most refusal-leaning terms of the description text model (see `reports/model_metrics.md`).

| Column | Matches | Notes | Model |
|---|---|---|---|
| `has_gym` | gym, gymnasium, fitness suite/centre/studio, health club; **or** PLD use class E(d) / D2 | Excludes loss/removal/change of use *from* a gym | ✅ merged into `premium_amenity` (42 rows) |
| `has_pool` | swimming pool, "pool" | Excludes Liverpool, Poole, "pool road/street", whirlpool, car pool, and removals/infills | ✅ merged into `premium_amenity` (10 rows) |
| `has_concierge` | concierge | | ✅ merged into `premium_amenity` (2 rows) |
| `has_basement` | basement | Excludes infilling a basement | ✅ |
| `has_roof_terrace` | roof terrace, rooftop terrace, roof garden | | ✅ |
| `has_communal_amenity` | communal amenity/garden/space/lounge/roof, residents' lounge/amenity | | ✅ |
| `has_commercial` | class E, commercial, retail, office | Also matches loss of commercial space | ✅ |
| `has_demolition` | demoli… | | ✅ |
| `has_affordable_mention` | affordable | | ⚠️ 52 rows; duplicates tenure data |
| `gym_removed`, `pool_removed` | Loss, removal, demolition, infill of a gym / pool | Rows here have `has_gym` / `has_pool` = False | ⚠️ too rare |
| `has_backland` | land/site/garden/plot (to the) rear of, backland, garden land, rear garden of, land adjacent to / adjoining | 261 rows, 38% approved vs 48% overall | ✅ |
| `has_pub_loss` | public house, pub, drinking establishment | Almost always a pub being converted or redeveloped. 130 rows, 44% approved | ✅ |
| `has_studio` | studio… | Complements `mix_studio`, which is often missing. 787 rows, 43% approved | ✅ |
| `storeys` (when `storeys_source = "text"`) | "N storey", "N-M storey", "part three part five storey" (numbers 1–60 or words one–twenty) | Takes the maximum; skips matches preceded by "existing"/"current" | ✅ via `storeys` |
| `dev_type` | See above | | ✅ |

Also stored: `premium_amenity` = gym or pool or concierge (✅); `social_rent_pct_units` = `affordable_pct_units` × social-rent share, 0 if no affordable homes (✅).

## Site context (SPATIAL)

| Column | Type | Rule | Model |
|---|---|---|---|
| `in_conservation_area` | bool | Point within a conservation area | ✅ |
| `in_article4_area` | bool | Point within an Article 4 direction area | ✅ |
| `in_tpo_zone` | bool | Point within a tree preservation zone | ⚠️ 44 rows |
| `in_green_belt` | bool | Point within green belt | ✅ |
| `in_opportunity_area` | bool | Point within a London Plan Opportunity Area | ✅ |
| `in_sil` | bool | Point within Strategic Industrial Land | ⚠️ 9 rows |
| `in_town_centre` | bool | Point within a town centre boundary | ✅ |
| `listed_building_within_25m` | bool | A listed building outline within 25 m | ✅ |
| `brownfield_site_within_50m` | bool | A brownfield register site point within 50 m | ✅ |
| `flood_zone` | int 1/2/3 | Highest EA flood zone containing the point (1 = neither 2 nor 3) | ✅ one-hot |
| `ptal_ai` | float | TfL access index of the nearest 100 m PTAL cell (within 150 m) | ✅ log(1+x) |
| `ptal_level` | str | PTAL band: 0, 1a, 1b, 2, 3, 4, 5, 6a, 6b | ⚠️ duplicates `ptal_ai` |
| `ptal_ordinal` | float 0–8 | `ptal_level` as an ordered number | ⚠️ duplicates `ptal_ai` |
| `imd_decile` | int 1–10 | IMD 2025 decile of the LSOA (1 = most deprived 10%) | ✅ |
| `imd_score` | float | IMD 2025 score (higher = more deprived) | ⚠️ duplicates `imd_decile` |
| `mayor_referable` | bool | DERIVED: `mayor_1a_over_150_homes` or `mayor_1c_height` | ⚠️ replaced by its two parts |
| `mayor_1a_over_150_homes` | bool | DERIVED: more than 150 net homes (Mayor of London Order 2008, Category 1A) | ✅ |
| `mayor_1c_height` | bool | DERIVED: estimated height over 30 m, or over 150 m in the City (Category 1C; the 25 m Thames-side rule is not modelled). Other referral categories (Green Belt/MOL, 2026 Category 3J) not covered | ✅ |
| `statutory_major` | bool | DERIVED: 10+ net homes or a site of 0.5 ha or more (statutory major residential definition) | ✅ |

## Excluded on purpose (not in the table)

Post-submission fields that would leak the outcome: `days_to_decision`, `decided_by`, `decided_date`, `n_comments`, `n_documents`, `last_changed`, and PLD commencement / completion / appeal / lapsed dates. Also PLD `unit_development_type` (filled mostly after approval) and PLD `affordable_percentage` (defaults to 0; recomputed from tenure instead).

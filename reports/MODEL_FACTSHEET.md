# Model factsheet: London housing approval and S106

*House London #2, 26 September 2026. Figures from `reports/model_metrics.md` and `reports/feature_importance.md` (commit `368d2df`).*

## What it does

Given a proposed housing scheme and its site, the model estimates:

- **P(approved):** the chance the application is granted (withdrawn counts as not approved)
- **P(S106 | approved):** the chance approval comes with a Section 106 agreement (1–9 home schemes only; for 10+ homes an S106 is expected)

It also reports the **historical approval rate for the same borough and scheme size**, and the **factors pushing this scheme's estimate up or down**.

**In one line:** borough and scheme size explain most of what public data can tell you about approval; the model adds a modest, measurable improvement and explains which scheme features matter.

## Data

| | |
|---|---|
| Proposals | **~15,100** new full or outline applications creating at least one home, decided or withdrawn, started 2022–2025, all 33 boroughs plus the development corporations |
| Of which 10+ homes | ~680 |
| Outcome labels | Foundations planning file (hackathon); Planning London Datahub (GLA) for the ~7,400 applications Foundations doesn't hold. The two agree on 99.7% of 7,230 shared decisions |
| Outcome mix | ~48% approved, ~43% refused, ~9% withdrawn |
| Proposal details | Planning London Datahub: homes, bedrooms, tenure, storeys, site area, floor area, parking, use classes |
| Site context | planning.data.gov.uk (conservation areas, Article 4, listed buildings, flood zones, Green Belt, TPOs, brownfield), GLA (Opportunity Areas, industrial land, town centres), TfL PTAL 2023, ONS LSOA + Indices of Deprivation 2025 |
| Excluded | Householder extensions, condition discharges, amendments, variations, lawful-development certificates, prior approvals, undecided applications |

## Inputs (~40 features)

- **Scheme:** homes (gained, lost), storeys, site area, density, average home size, share of homes below London Plan space standards, unit mix, affordable % and social-rent % (10+ homes), non-residential floorspace, development type, scheme type (standard / HMO / student / co-living), outline or full
- **Parsed from the description:** demolition, basement, roof terrace, commercial space, communal amenity, gym / pool / concierge, backland or garden site, loss of a pub
- **Site:** borough, conservation area, Article 4, listed building within 25 m, Green Belt, flood zone, Opportunity Area, town centre, brownfield site nearby, PTAL, deprivation decile
- **Policy definitions:** statutory major development, Mayor referral (over 150 homes; over 30 m, or 150 m in the City)

## Model

- **XGBoost** (340–400 trees of depth 4), with smooth (Platt) calibration so probabilities mean what they say
- Chosen over logistic regression because it ranks schemes better: +0.015 ROC-AUC (95% CI +0.004 to +0.027) on the same test rows. Interactions between features account for that gain; adding more by hand did not help
- A browser version (`models/web/score.js`, no dependencies) matches Python to within 1e-6

## How it was tested (leakage controls)

- **Time split:** trained on applications started 2022–2024, tested on 2025
- **Repeat sites removed from the test set:** 466 test applications on sites already in training were dropped
- **Fitted on training years only:** fill values, tuning, calibration and thresholds, with cross-validation grouped by site
- **Only information available at submission:** no decision dates, comments, officer, document counts or final S106 terms
- **Missing data is not a feature:** a check model using only which fields are blank (and which source labelled the row) scores ROC-AUC 0.506 on the test set, i.e. no signal
- **A PLD field that leaked the outcome was removed:** `unit_development_type`, which is filled mostly after approval

## Performance (2025 test set, 2,328 applications)

| | ROC-AUC (95% CI) | Brier | Accuracy |
|---|---|---|---|
| Always guess the average (48%) | 0.500 | 0.250 | 0.52 |
| **Baseline:** borough × size approval rate | 0.615 (0.592–0.637) | 0.240 | 0.59 |
| Logistic regression | 0.638 (0.614–0.659) | 0.235 | 0.59 |
| **XGBoost (shipped)** | **0.652 (0.630–0.674)** | **0.232** | **0.60** |
| XGBoost + description text (offline only) | 0.673 (0.652–0.695) | 0.227 | 0.62 |

Brier = average squared error of the probabilities (lower is better).

- **vs the baseline:** better ranking (+0.04 ROC-AUC) and better-calibrated probabilities. Accuracy is barely higher, within noise
- **Risk flagging:** the fifth of schemes the model rates lowest were approved about 27% of the time, against about 66% for the top fifth (the baseline's lowest fifth: 35%). Measured before the text-model commit
- **10+ home schemes:** ROC-AUC 0.66, but on only 64 test schemes (CI 0.52–0.80)
- **Excluding withdrawn applications:** ROC-AUC 0.668
- **Description text** adds about +0.02, but needs a written description. The simulator doesn't have one, so the browser model is parameter-only

## What drives approval

Features with a real effect (shuffling them reliably costs accuracy). Effects are changes in predicted approval with everything else unchanged. **Associations in past decisions, not causes.**

| Feature | Effect |
|---|---|
| **Borough** | 27% (Waltham Forest) to 70% (Haringey) for the same schemes: by far the largest factor, and partly a data-recording effect |
| Average home size | 49 → 125 m²: +6 pp |
| HMO scheme | −7 pp vs standard housing |
| Density | low → high: −5 pp |
| Homes below minimum space standards | 0% → 50% of homes: −3 pp |
| Loss of a pub | −3 pp |
| Conservation area | +3 pp (likely self-selection: only stronger schemes get submitted) |
| Affordable housing (10+ homes) | 0% → 100%: +20 pp (few schemes; directional) |
| Unit mix, number of homes, development type | ±1–2 pp |

**No measurable effect:** flood zone, Green Belt, listed building nearby, Opportunity Area, town centre, gym / pool / concierge (too rare: ~56 schemes), Mayor-referral flags.

## S106 model

- Logistic regression, approved Foundations applications only (~3,600), 13% positive
- Test ROC-AUC 0.945, but **this is inflated**: the label is S106 wording in the decision text, 20 of 35 boroughs never use that wording, and 5 boroughs hold 76% of positives. It mostly learns which boroughs write "S106"
- So it's shown only for 1–9 home schemes and marked indicative. For 10+ homes it returns "S106 expected"

## Known limits

- **The ceiling is information, not method.** More data, 11 extra features, 12 policy rules and interaction terms each moved ROC-AUC by under ±0.005. What decides many small schemes (design, neighbour impact, officer judgement) isn't in any public dataset
- **Borough effects** partly reflect how each borough's applications were recorded and filtered, not just policy
- **Major schemes:** few examples, so estimates for 10+ homes are wide
- **Policy rules** (Fast Track, the March 2026 route, the 2026 Mayoral 3J notification) are policy checks, not model inputs. They took effect after the training data, or don't predict refusal. They belong in a separate policy screen
- **Not planning advice** and not a viability assessment

## Files

| Path | What |
|---|---|
| `scripts/build_features.py` | Joins Foundations, PLD and spatial layers → `data/processed/features.parquet` |
| `scripts/train_models.py` | Trains and evaluates all models; writes reports and model files |
| `scripts/feature_importance.py` | Writes `reports/feature_importance.md` |
| `models/web/` | Browser bundle: `approval_model.json`, `score.js`, parity check, README |
| `models/xgb_approval.json`, `models/model.json`, `models/approval_with_text.joblib` | Python-side models |
| `docs/DATA_SOURCES.md`, `docs/DATA_DICTIONARY.md` | Every source and every column |

Reproduce: `./setup.sh`, then `python scripts/download_pld.py`, `python scripts/download_spatial.py`, `python scripts/build_features.py`, `python scripts/train_models.py`. This needs the Foundations CSV, which the organisers provided.

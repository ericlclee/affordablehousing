# Contributor model integration boundary

## Current state

Approval screening is **unavailable** in this build. No authorized, versioned model artifact or accepted validation manifest is installed. The app must not show approval or Section 106 probabilities, use an artifact found on disk automatically, or turn screening on because caller-provided fields look complete. `screeningAvailability()` remains unavailable until a human integration review explicitly changes this contract.

The feasibility engine works independently. Its policy-route results, financial sensitivity, documented Section 106 cost, and balanced-scenario selection do not depend on approval screening. The adapter does not train, benchmark, or score a competing model.

## Canonical input mapping

`canonicalModelInput(scenario, siteFacts = null)` accepts the engine's canonical scenario and an optional contributor-owned `SiteFacts` record. It returns an allowlisted pre-submission feature object:

| Model feature | Canonical source and treatment |
|---|---|
| `storeys`, `height_m`, `site_area_m2`, `coverage_ratio`, `gia_m2` | `scenario.geometry.storeys`, `heightM`, `siteAreaM2`, `coverageRatio`, `giaM2`; metric values remain numeric. |
| `homes`, `density_homes_per_ha` | `scenario.homes` and homes divided by `geometry.siteAreaM2 / 10,000`; density is unknown when area is absent or zero. |
| `unit_mix_pct_by_bedrooms` | `scenario.allocation[].homes`, grouped by `bedrooms` as studio, 1 bedroom, 2 bedrooms, or 3+ bedrooms. A missing or unsupported schedule yields `null`. |
| `affordable_habitable_rooms_pct` | Exact integer `affordableHabitableRooms / totalHabitableRooms × 100`. It does not use `targetAffordablePct` or the former UI's illustrative affordable slider. |
| `social_rent_share_of_affordable_pct` | `socialHabitableRooms / affordableHabitableRooms × 100`; it is unknown when the affordable-room denominator is absent or zero. |
| Development type, demolition, amenities, non-residential floorspace, parking, scheme type | Only explicit canonical values are mapped. Unsupported or absent fields remain `null`; the adapter does not infer them from policy labels, scenario names, or user-interface state. |
| Borough and site context | Read only from a `SiteFacts` object with a non-empty `version`. Each absent flag is `null`; explicit `false` is preserved. A missing/unversioned record never means “no constraint.” |

All feature percentages use 0–100 units. Area fields use square metres; height uses metres; density uses homes per hectare. Numeric zero and boolean false remain distinct from unknown (`null`). The adapter also returns `feature_states`, keyed by output feature name. Each state is `known`, `unknown`, or `not_applicable`; an absent or explicit `null` source is `unknown`, while a source explicitly set to the string `not_applicable` (or an object with `state` or `status` equal to `not_applicable`) is preserved as that state even though its typed model value remains `null`. Values with the wrong type are treated as unknown. If site facts lack a version, ordinary site values remain unknown; an explicit not-applicable marker is retained. A future score consumer must inspect and explicitly handle every `not_applicable` state before scoring; it must never silently encode it as false, zero, or ordinary missingness. `feature_states` is adapter metadata, not a model feature. The output does not include policy routes, appraisal results, user comments, decision dates, decision makers, document counts, or final S106 terms.

The contributor has not supplied a trained-model feature schema or exact categorical enum contract. The mapped names and accepted development/scheme values in `adapter.js` are therefore a safe handoff proposal, not evidence of scorer compatibility. In particular, the feasibility engine's `sale` / `build_to_rent` policy choice is not silently converted to the contributor's `standard` / `co-living` / `student` / `HMO` scheme categories.

## Evidence required before enabling scores

The contributor must provide the artifact and integration evidence defined in PRD section 7:

- A versioned model artifact, exact input/output schema, supported ranges, missing-value/imputation provenance, and abstention behavior.
- Training and held-out test periods, target cohort definition, and PLD↔Foundations join counts with unmatched, duplicate, and revision audit.
- Held-out 2025 Brier score, calibration, and refusal PR-AUC against the borough-by-size baseline; subgroup counts and performance for the target full/outline, approximately 10+ home cohort. A single aggregate metric is not sufficient.
- Evidence that post-submission comments, decision dates, decision makers, document counts, and final S106 terms were excluded.
- Confirmation of feature names, units, category enums, and score semantics, plus an explicit human integration decision accepting the evidence.

Before any score is displayed, integration must also confirm that an out-of-coverage scenario abstains; that each output carries model version, cohort/date, coverage state, and uncertainty; and that `p_approved_with_s106` equals `p_approved × p_s106` within numeric tolerance. Drivers may describe model associations only; they must not be presented as causal effects. A model output must not change a policy badge, documented S106 cost, financial result, or balanced-scenario choice.

No automated gate based on truthy artifact or manifest fields is implemented. A future enablement change requires code review against this evidence package and an explicit human decision. Until then, the UI should display **“Approval screening unavailable”** and keep all other study functions available.

# Approval + S106 model: what I'm building (so we don't overlap)

**TL;DR:** I'm building a data-trained model that replaces the simulator's assumed approval multipliers. Given a proposal and its site, it outputs **P(approved)** and **P(S106 | approved)** and ships as a `model.json` that the JS sweep can score directly.

## Outputs

- `p_approved`: probability the application is granted
- `p_s106`: probability it's granted *subject to* a Section 106 agreement, given approval
- `p_approved_with_s106` = the two multiplied
- `drivers`: the top 3 features pushing each probability up or down, for the "why" text

## Input features

**Proposal (from the architect/developer inputs):**

- homes (log), storeys, max height (m), GIA (m², log), site area → density
- unit mix: % studio/1b/2b/3b+
- affordable % by habitable room, social-rent share
- development type: new build / conversion / extension / change of use; demolition yes/no
- amenities: gym, pool, basement, roof terrace, concierge, communal amenity
- non-residential floorspace (commercial E class), car and cycle spaces
- scheme type: standard / co-living / student / HMO

**Site (looked up automatically from location, never typed by the user):**

- borough
- conservation area, Article 4 area, listed building on site, tree preservation zone
- flood zone 2/3, green belt, brownfield register
- Opportunity Area, Strategic Industrial Land, town centre
- PTAL 2023 (public transport access)
- deprivation decile (IMD 2025)
- Mayor-referable flag (150+ homes or 30 m+)

**Deliberately excluded:** comments, decision dates, `decided_by`, document counts and final S106 terms. These only exist after submission. The residents' comments → refusal effect stays in the simulator's resident layer, not in my model.

## Model

- **Logistic regression (L2)** is what ships, because it runs in JS inside the ~7,900-variant sweep.
- **XGBoost** is the offline benchmark. It only replaces logistic regression if it's clearly better on held-out data.
- Train on 2022–24, test on 2025. Metrics: Brier score, calibration, and refusal PR-AUC, against a borough × size baseline. The CivisOpt PRD's model gate is satisfied.
- Two models: P(approved) on all decided residential schemes, P(S106) on approved ones only.

## Data (done, and anyone can reproduce it)

- `./setup.sh`, then `python scripts/download_pld.py` (GLA Planning London Datahub, 447k applications 2022–25, ~8 min).
- `python scripts/download_spatial.py` downloads conservation areas, Article 4 areas, listed buildings, flood zones, green belt, brownfield land, TPOs, Opportunity Areas, SIL, town centres, PTAL, LSOA + IMD 2025, and Mayor referrals. All are clipped to London.
- Join: Foundations (labels) ↔ PLD (proposal features) on borough + normalised reference number. Tested at **97–100% match**.
- Approval labels come from Foundations, because PLD under-records refusals. Proposal features come from PLD.
- FYI: we **do have EPC** locally (London, 3.6M certificates). It's not needed for this model.

See `README.md` for setup, the dataset table and join details.

## Interface for the simulator (engine + UI)

- `model.json`: coefficients, feature means/scales, borough effects.
- `score(params) → {p_approved, p_s106, p_approved_with_s106, drivers}`: about 20 lines of JS; I'll provide it.
- Parameters the user doesn't set get filled from the architect formulas (GIA = site × coverage × storeys, etc.) plus medians of comparable schemes. That includes refused schemes, so the defaults aren't biased towards approval.

## What I'm NOT doing (yours if you want it)

- The developer viability / residual land value maths
- The residents' score, Pareto front and Nash compromise
- The 3D map and front-end UI
- The policy-era rules (Fast Track vs Viability Tested)
- The LLM agent that turns plain English into parameters: happy to pair on it, but not starting it

## Asks

1. Whoever has `data/pld_res10.json` and `analysis/sim_parameters.json`, please share them so we don't duplicate work.
2. Engine owner: confirm the parameter names you use for storeys, homes, coverage, mix and affordable %, so `score()` matches them.
3. Anyone already working on approval odds or constraint multipliers: tell me now and we'll merge.

## Timing

`model.json` v0 before the 15:30 cut line, then the XGBoost comparison if there's time.

# Proposal 106: build spec (26 Sep 2026, 13:20)

Rebuilds the ChatGPT MVP (`mvp_chatgpt/`, "One Roof London v2") as **Proposal 106**. It follows `CIVISOPT_v3_SHARED.md`. The aim: simpler, more interactive, and every number real or labelled as an assumption.

## Keep from the MVP
- The visual language: sage greens, calm cards, clean type. It looks good.
- The Three.js 3D context: OSM building footprints extruded, drag to orbit, scroll to zoom.
- The honesty: assumptions labelled, "not planning advice".
- A stepper through the planning stages.

## Drop from the MVP
- Invented 0–100 actor scores and the "everyone reaches 60" middle ground.
- Room and rooftop modes. Proposal 106 is for schemes of **10+ homes**, where Section 106 applies.
- Station-anchor presets. Leaflet map picking. The "illustrative mitigation budget" slider that isn't linked to viability. The WebMCP tools.

## One screen
- **Left, always visible:** the 3D view. It shows the real site boundary as a red dashed line, the proposal massing among OSM neighbours, and the neighbour median height.
- **Top strip: four voices, as measured quantities, never scores.**
  - Architect: vision retained %
  - Developer: surplus against the target return, in £m, plus break-even £/m²
  - Planning: route badge
  - Residents: Social Rent homes, and height as a multiple of the neighbour median
- **Right: a stepper through stages 0 to 5.** Each stage has at most 3 controls and one headline output.

## Site
Morrisons, Walworth Road, Southwark: brownfield register entity 1710099 / 0.51 ha / 135–165 homes. The polygon comes from `data/brownfield-land.csv` (the `geometry` column, WKT). Land type is a toggle (private / public / industrial), defaulting to private, labelled "verify ownership".

Save the OSM context as `proposal106/data/context.json`: Overpass `out geom`, buildings and highways, within ±0.0032 lng and ±0.002 lat. It's the same shape as `mvp_chatgpt/src/One-Roof-London-v2/dist/data/camden.json`.

## Stages

**0. The architect's proposal (the vision).** The architect enters the massing: podium coverage (% of site), podium storeys, tower coverage (% of site, 0 means no tower), tower storeys, floor-to-floor height (default 3.2 m), and unit mix (1b / 2b / 3b %). "Save as my vision" freezes this as Concept 0.

Derived values:
- `GIA = site × (podium_cov × podium_st + tower_cov × tower_st)`, and `NIA = 0.80 × GIA` (assumption)
- unit sizes of 50 / 70 / 86 m² NIA for 1b2p / 2b4p / 3b5p (London Plan Table 3.1)
- homes = NIA ÷ the mix-weighted average size
- habitable rooms per home: 1b = 2, 2b = 3, 3b = 4
- height = storeys × floor-to-floor

**1. Site and policy.** Toggle: land type. Output: the route matrix, adopted rules only.
- **Temporary route** (March 2026 guidance, applications validated by 31 Mar 2028): private land needs ≥20% affordable **by habitable room** with ≥60% Social Rent; public or industrial land needs 35% (with ≥60% Social Rent, as the app reads it; confirm against the March 2026 guidance).
- **H5 Fast Track:** ≥35% (50% on public or industrial land), with at least 30% low-cost rent and 30% intermediate.
- **Otherwise H5 Viability Tested:** "requires review".
- **Mayor:** 50+ homes means notified (Category 3J); 150+ homes or over 30 m means referable.
- **Tall building:** over 6 storeys or 18 m means checking the borough's tall-building zones ("not checked").
- The draft plan appears only as a what-if line (bands A/B/C: 35/25/20%). Southwark's band is not checked.

**2. Developer.** Controls: affordable % by habitable room (quick buttons 20 / 35 / 50, plus a slider 0–50), the Social Rent share of the affordable homes (default 60%), and low/base/high assumptions. Output: surplus and break-even £/m², with a small break-even vs affordable-% chart.

All inputs editable and labelled:
- Market sale: £8,000/m² base (7,200 / 9,000 low/high). This is a **placeholder from the Lewisham study, not Southwark evidence**.
- Social Rent transfer: £2,987/m² (from the Lewisham LAR figure; Social Rent itself is not verified).
- Shared ownership: £4,500/m² (assumption).
- Build: £2,014/m² GIA up to 5 storeys, £2,364 above (Lewisham), × 1.10 contingency.
- Fees: 10% of build. Sales: 2.75% of market GDV.
- Mayoral CIL band 2: £72.73/m² GIA (confirm Southwark's band). Borough CIL: input, default "not entered", shown as a warning.
- S106 contributions: £/home input, default 0, with a "not entered" warning.
- Finance: 6.5% × (land + ½ build) × 2 years (assumption).
- Land (existing use value plus premium): £12m default (**assumption**: enter the real figure).
- Target return: 17.5% of GDV.

Formulas:
```
surplus = GDV − costs − target return
break-even market £/m² = (total cost incl. land + target return − affordable receipts) ÷ market NIA
```
Iterate 5 times, because fees, sales cost and return depend on GDV.

**3. Residents.** Controls: open space kept (derived from coverage; nudge coverage here too). Outputs:
- height against the neighbour median (from `context.json`)
- Social Rent homes
- open space in m²
- play space need: 10 m² per child, with child yield 0.2 per 2b and 0.6 per 3b (assumption)

Observed context line: in the hackathon data, small full applications are refused 18% of the time with 0 comments and 68% with 25–99 comments (14 boroughs; a correlation, not a prediction).

**4. Section 106: the negotiation.** Planning asks for the route threshold the land type needs. The developer's best offer is the highest affordable % that keeps surplus ≥ 0 at base assumptions. Show:
- the ask, the offer and the gap
- whether the route is "Fast Track (no viability assessment)" or "Viability Tested (assessment + reviews)"
- CIL as fixed and not negotiable
- an "Accept the offer" button that sets the affordable %

**5. Middle ground.** Sweep storeys from 2 to (vision + 6), podium coverage from 0.30 to 0.70 in steps of 0.05, and affordable % from 0 to 50 in steps of 5, keeping the tower ratio. That's about 2,000 variants, all in the browser.

Utilities from 0 to 1:
- `U_dev = min(1, profit on GDV ÷ 0.25)`
- `U_plan = min(1, affordable_hr ÷ 50)`
- `U_res = 0.5·(1 − clamp((height ÷ neighbour_median − 1) ÷ 4)) + 0.5·min(1, open_space_share ÷ 0.5)`
- `U_arch = V`

Walk-away points are sliders:
- developer 0.6 (a 15% return)
- planning = the route minimum ÷ 50
- residents 0.3
- architect 0.6

**Balanced** is the argmax of Π(Uᵢ − dᵢ) over variants where every Uᵢ > dᵢ. Cards: Architect's proposal (Concept 0), Higher return, More affordable rooms, Balanced. Clicking a card applies it to the 3D view. Add "what each gave up" bars, and a process strip of observed medians:
- full applications of 10+ homes: median 289 days, 26.6% refused
- by size, 10–49 / 50–149 / 150+ homes: 252 / 374 / 322 days, and 35.4 / 10.0 / 8.0% refused
- with Section 106 wording: 359 vs 91 days for medium schemes
- all labelled "observed, not a prediction"

If no variant clears every walk-away, say which actor blocks it.

## Vision retained
```
V = 1 − (0.3·|Δstoreys|/seed + 0.3·|Δcoverage|/seed + 0.2·|Δhomes|/seed + 0.2·|Δopen space|/seed)
```
Use total storeys and podium coverage. Clamp to 0–1.

## Model hook (teammate's approval model)
Expose `window.P106.params()` with exactly these names:
`site_area_m2, podium_coverage, podium_storeys, tower_coverage, tower_storeys, storeys, max_height_m, gia_m2, nia_m2, homes, habitable_rooms, mix_b1, mix_b2, mix_b3, affordable_hr_pct, social_rent_share, land_type, borough, lat, lng`.

If `window.P106Model?.score` exists, show its output in stage 5 as "historical pattern, teammate model, not used in the optimisation". Otherwise hide it.

## Tech
- `proposal106/index.html`: one file with inline CSS and JS, plus `proposal106/data/context.json` and `proposal106/data/site.json`.
- Three.js r128 UMD from cdnjs, pinned (`https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`), with its own simple orbit controls.
- No other libraries. No external fetch except the relative data files.
- Must work served with `python3 -m http.server 4174 --directory proposal106` **and** published as a Claude artifact, with the data files published alongside.
- Works at 390 px wide. Theme tokens for light and dark.

---

## Addendum (13:40): agents and the residents add-on, as phase 2 after the core build

**Decided by Maria:** the Planning and Developer voices are *agents* you can talk to. The residents are an **add-on**: off by default, and switched on when you want their view.

### Who owns which parameter
| Owner | Parameters it can change | Rule |
|---|---|---|
| Architect (you, stage 0) | podium_coverage, podium_storeys, tower_coverage, tower_storeys, floor_to_floor, mix_b1/b2/b3 | Only you change these. An agent can *suggest* a massing change, and you must accept it (vision retained updates) |
| Planning agent | affordable_hr_pct, social_rent_share, borough_cil_per_m2, s106_per_home; land_type only if you confirm it | Answers from the route rules and their sources |
| Developer agent | sale_per_m2 (low/base/high), build_cost_per_m2, land_value, target_return, finance_rate | Answers from the appraisal and its assumptions |
| Residents (add-on) | None. They react to height against neighbours, open space, Social Rent homes and play space | Toggle "Invite the residents". When on: a fifth card, stage 3 unlocks, they join the Balanced calculation with their own walk-away, and an "Ask the residents" chat |

### How an agent works
- The chat panel has three buttons: "Ask Planning", "Ask the Developer", and (with the add-on) "Ask the Residents". Each agent keeps its own turns in page memory.
- **Live mode, in the published artifact:**
  - Declare `capabilities: {sample: {}}` and use `const sample = await claude.use("sample")`.
  - Call `sample([instructionsTurn, ...turns], {tools, modelTier: "quick", cache: false, onText, signal})`.
  - The instructions turn holds the role, the current state (small JSON), that agent's rules with their sources, and: "Never state a number you did not get from a tool. To change anything, call propose_changes; the user decides."
  - **Tools** (small JSON results):
    - `get_state()`
    - `run_engine({changes})`: a what-if that does not apply the changes
    - `max_affordable({min_profit_pct})`: sweeps affordable from 0 to 50%
    - `propose_changes({changes, reason})`: validates that each parameter belongs to this agent (architect parameters become "suggestion to architect") and renders a diff card with **Accept / Reject** in the chat
  - Handle errors: on `not_granted`, `sampling_disabled` or `tools_unavailable`, switch to scripted mode. On `rate_limited`, show a message and keep the control.
- **Scripted mode** (localhost, or when sampling is unavailable). This keeps the demo safe offline. There are quick-question buttons per agent, answered deterministically from the engine, with the same diff cards:
  - Planning: "Which route am I on?", "What do I need to fast-track?", "Is this referable to the Mayor?"
  - Developer: "Do we break even?", "What's the most affordable we can offer?", "What would it take to reach 35%?" (the required sale £/m², or the extra storeys, as a suggestion to the architect)
  - Residents: "How does it compare with our street?", "How many Social Rent homes?", "Is there enough play space?"
- **Guardrail (PRD F7):** the same parameters always give the same numbers, whether they came from the chat or a slider. Agents never write numbers the engine did not produce.

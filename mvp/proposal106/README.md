# Proposal 106: review snapshot

This is the running version Maria selected on 26 September 2026, imported from Claude's local preview. It is added alongside the original geographic MVP in `mvp/dist/`, leaving that version and the team's model pipeline unchanged.

From the repository root:

```sh
python3 -m http.server 4174 --bind 127.0.0.1 --directory mvp/proposal106
```

Open http://127.0.0.1:4174/. If that port is occupied, choose another port. Three.js r128 is loaded from cdnjs, so 3D needs internet access; numerical controls remain available if the library cannot load.

## What is included

- Fixed Walworth Road site in Southwark, with a site boundary and OSM context.
- Podium/tower massing, unit mix and saved architect's vision.
- Editable cost/value assumptions, break-even chart and affordable-housing scenarios.
- Six stages covering site policy, developer, residents, Section 106 and compromise search.
- Optional `window.P106Model.score(params)` hook; no trained model is installed.

The later redesign brief's arbitrary-location search, MapLibre map and chat agents are not implemented in this snapshot.

## Checks

Requires Node.js and Python 3:

```sh
node mvp/proposal106/check_inputs.mjs
node mvp/proposal106/engine_check.mjs
python3 mvp/proposal106/check_engine.py
```

The first command asserts the cleared-input regression. The other two generate arithmetic reports; a successful exit alone is not a full regression suite. An independent comparison at the same 5,090 m² site area matched GIA, GDV, total costs, surplus and break-even within 1e-6 at 20%, 35% and 50% affordable housing. The search returned 1,881 alternatives, 587 feasible under its stated utility thresholds.

One import fix resets a cleared nested assumption, such as the base sale value, to its numeric default instead of an object. Original import hashes are recorded in `SNAPSHOT.json`.

## Evidence and review limits

`PROPOSAL106_SPEC.md` preserves the source specification. `analysis/sim_parameters.py` and its aggregate JSON preserve the provenance of the displayed historical summaries. To rerun that analysis, install pandas and duckdb and supply the compatible Foundations parquet at `mvp/proposal106/data/foundations.parquet`; raw datasets remain ignored. The aggregate analysis was not rerun during this import.

The calculation comparison verifies arithmetic, not planning policy or market values. Temporary affordable-housing route conditions, referral rules and current site constraints still require review. The source spec flags an unresolved tenure condition for public/industrial land. Costs and values include Lewisham placeholders; land value is assumed, and missing borough CIL/S106 inputs are counted as zero. Actor utilities are illustrative and are not approval probabilities.

Small public map assets are explicitly included by this folder's ignore rules. Site source links and OSM attribution are retained in the app and `data/site.json`. OSM context: © OpenStreetMap contributors, ODbL. No raw modelling dataset is included.

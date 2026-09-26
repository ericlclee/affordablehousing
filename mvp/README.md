# House Hackaton · One Roof, Two Answers

An interactive London housing-planning simulator built for House London. Explore the compromises between architect, developer, planning policy and residents—from the first idea to an illustrative decision, including Section 106.

## Try it locally

No package installation or API key is needed. Requires Python 3 and a browser with WebGL.

```sh
git clone https://github.com/ericlclee/affordablehousing.git
cd affordablehousing/mvp
python3 -m http.server 4173 --bind 127.0.0.1 --directory dist
```

Open **http://127.0.0.1:4173/**. Serve over HTTP rather than opening index.html directly.

## CivisOpt: evidence-grounded feasibility

Open **http://127.0.0.1:4173/civisopt.html** for the new site study. It compares three integer affordable-room allocations against a fixed envelope and editable financial assumptions, with sourced policy checks, break-even values, input snapshots and a printable brief. A public Croydon register record anchors the illustration; its indicative boundary and unresolved site conditions remain visible.

Run `npm test` from this directory with Node.js 22+ for the finance, allocation, policy and adapter checks. No dependency installation is required. See [implementation scope](research/CIVISOPT_IMPLEMENTATION.md), [source audit](research/CIVISOPT_SOURCES.md), and [model handoff](research/MODEL_INTEGRATION.md).

The original interface below remains a separate illustrative planning conversation. Its actor scores do not enter the CivisOpt calculations.

## What you can explore

- Choose London coordinates on a map; identify the council using all 33 GLA borough areas.
- See real OpenStreetMap building footprints and streets in a 3D view.
- Start near Dalston Junction (Hackney), Kentish Town (Camden), or Stratford (Newham).
- Compare a room extension, rooftop homes, and a housing block up to 12 storeys.
- Adjust setbacks, affordability, privacy screening and an illustrative mitigation budget.
- Follow the planning stages, actor responses and trade-off chart.
- Compare a suggested compromise before applying it; your affordable target is preserved.

## For teammates

| File | Purpose |
|---|---|
| `dist/index.html` | Page structure, labels, sources and evidence notes |
| `dist/style.css` | Layout and visual design |
| `dist/app.js` | Map, 3D geometry, interactions and score formulas |
| `dist/context/` | GLA boundaries and three saved neighbourhood extracts |
| `research/ROOF_RATE_FINDINGS.md` | Audit of the unverified 75% / 56% claim |
| `research/LONDON_MAP_POLICY_SOURCES.md` | Verified location and borough-policy sources |
| `research/check_roof_rates.py` | Reproducible exploratory dataset checks |

The repository root contains the team’s data-download and feature-building pipeline. This MVP is self-contained and does not yet consume a trained model. When integrating the planned `model.json` and `score(params)` interface, keep empirical predictions separate from the four illustrative actor scores. Follow the root README’s current feature guidance, including its data-leakage exclusions.

## Evidence and limitations

**The original 75% versus 56% approval-rate claim could not be reproduced from a documented method and is not used as a factual headline.** The audit covers the 181,929-row Foundations dataset. Exploratory keyword cohorts are not validated room-versus-rooftop-home categories.

The coordinates, boundaries and mapped footprints are real. The green proposal is a hypothetical overlay, not a cleared development site. Presets are station/neighbourhood anchors. Building heights use mapped heights, then storeys × 3 m, then an explicitly labelled 9 m fallback. Complex multipolygon buildings may be incomplete.

Actor scores, financial assumptions and decision thresholds are teaching models—not permission probabilities, a viability assessment or a legal assessment. Exact formulas appear in the evidence panel. Borough policies are researched for Hackney, Camden and Newham; other councils are identified but marked unreviewed. Borough boundaries do not identify every special planning authority, conservation area or local policy designation.

Map tiles and custom-coordinate geometry need internet access; preset geometry is bundled. Live requests use a small area and a short cooldown. A larger public deployment should use a dedicated map-data backend and durable caching.

## Re-run the data audit

Download the source from [Foundations](https://foreman.house-london.uk/download/csv/), then:

```sh
python3 research/check_roof_rates.py /path/to/foundations.csv --out audit-output
```

No original CSV is committed. The checked source filename and checksum are recorded in the audit.

## Sources and licenses

- [GLA / Ordnance Survey Open Data borough boundaries](https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/301): contains public sector information licensed under the Open Government Licence v3.0.
- [OpenStreetMap](https://www.openstreetmap.org/copyright): © OpenStreetMap contributors, ODbL 1.0.
- [TfL](https://api.tfl.gov.uk): preset station coordinates.
- Three.js: MIT, included in `dist/vendor/THREE-LICENSE.txt`.
- Leaflet: BSD-2-Clause, included in `dist/vendor/LEAFLET-LICENSE.txt`.
- Design references: [UI Skills](https://www.ui-skills.com) and [Beautiful UI](https://www.beautifului.dev).

## Checks completed

JavaScript syntax; desktop and mobile layout; all three neighbourhoods; a custom Newham coordinate; room-only Section 106 route; compromise comparison and application; valid/invalid structured control calls.

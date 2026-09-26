# Proposal 106 v2: location and negotiation interface

This review snapshot adds the updated app selected from localhost:4174 on 26 September 2026. The earlier `mvp/proposal106/`, original `mvp/dist/` and team prediction pipeline are preserved.

From the repository root:

```sh
python3 -m http.server 4174 --bind 127.0.0.1 --directory mvp/proposal106-v2
```

Open http://127.0.0.1:4174/. Choose another port if occupied. The map, fonts, address lookup and live constraints need internet access. No package installation or API key is needed for the scripted demo.

## Changes from the previous snapshot

- MapLibre 3D map, postcode/address search, council detection and 33 council information packs.
- Single-block building controls, three size presets, site drawing and GeoJSON/OBJ outline uploads.
- Three stages: Architect, Planning, Section 106; planning/developer chat with optional residents and accept/reject proposals.
- Optional user-configured AI provider connection, with prepared answers when not connected.
- The arithmetic engine is byte-identical to the previous snapshot. The team's trained prediction models are not wired into this imported interface.

## Import fixes and checks

Three review fixes are applied only in this copied version:

1. Switching AI provider cannot reuse another provider's saved key; changing provider clears stale model choices.
2. Missing, failed or malformed constraint responses show incomplete screening instead of a positive conclusion. Known mapped flags remain visible.
3. Invalid coordinates and zero-area uploaded footprints are rejected before changing model state.

Run `node mvp/proposal106-v2/check_snapshot.mjs` for assertions covering unchanged engine, valid/invalid GeoJSON, incomplete screening, mocked provider-key isolation and borough-pack coverage. Tests use fake credentials and do not call an AI provider. Browser checks covered loading, postcode search from Southwark to Hackney, matching council information, planning submission and scripted responses; no JavaScript errors were reported. The checked desktop document width matched its viewport.

`SNAPSHOT.json` records hashes of the source import; the HTML includes the fixes above. The copied council-statistics script's output path is adapted to this directory. The original Claude workspace is unchanged.

## Data and limitations

Bundled data contains public geometry, council policy summaries and aggregate statistics, not raw planning records. Source URLs and caveats remain in the JSON files. `merge_councils.py` rebuilds `councils.json` from the three policy parts and aggregate statistics. `analysis/build_council_stats.py` requires compatible Foundations parquet in `data/foundations.parquet`, external value/price inputs, pandas and duckdb. Its source dataset analysis was not rerun during import.

Policy thresholds, council packs and historical statistics still need team review. Point lookups are screening only; they are not full-site checks. Costs and land values are assumptions, and utilities are not permission probabilities. Do not treat green screening as planning permission.

Optional AI saves the supplied key in this browser's localStorage and sends chat/scheme context to the chosen provider. Provider charges may apply; live AI calls were not tested. Keep this as a local prototype until credential storage and deployment are reviewed. No keys are bundled. External map styles can emit missing-icon warnings.

The source redesign specification is retained for context; it is not proof that every requested feature is complete. The app remains a prototype for team review.

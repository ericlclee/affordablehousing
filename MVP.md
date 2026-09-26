# Run the housing-planning MVP

The interactive simulator is in [`mvp/`](mvp/README.md). It includes a geographic London map, 3D surroundings, four actor panels, planning stages, Section 106 negotiation and a trade-off comparison.

From the repository root:

```sh
python3 -m http.server 4173 --bind 127.0.0.1 --directory mvp/dist
```

Open **http://127.0.0.1:4173/**. No package installation or API key is needed; use a browser with WebGL. Map tiles and custom locations need internet access. Three preset neighbourhood extracts are bundled.

The original pipeline and its instructions remain in [README.md](README.md). The MVP currently uses illustrative actor scores, not trained approval probabilities. It does not yet load the model described in [MODEL_BRIEF.md](MODEL_BRIEF.md).

The claimed 75% versus 56% roof-extension approval rates could not be reproduced from a documented classification method and are excluded from the factual headline. See the [evidence audit](mvp/research/ROOF_RATE_FINDINGS.md).

Public map geometry and its attribution are included in `mvp/dist/context/`; raw modelling datasets remain untracked.

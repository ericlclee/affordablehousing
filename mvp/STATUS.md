# Status — 26 September 2026

Geographic prototype ready for team review: larger schemes, mapped surroundings, 33 council boundaries, three researched borough contexts, four actor panels and a compromise comparison.

Verified: JavaScript syntax; desktop/mobile inspection; 251 Hackney, 468 Camden and 93 Newham footprints; one custom Newham coordinate; compare/apply; room-only Section 106 route; valid and invalid structured controls.

Unverified 75% / 56% claim removed. Keep every teaching assumption and height-estimation caveat visible. Do not reinterpret the actor scores as approval probabilities.

Next: team reviews the simulator and chooses whether to validate application classifications for an empirical roof-room versus rooftop-home comparison. A hosted live website is separate from this source repository.

## 2026-09-26 — Codex: team repository integration

DECIDED by Maria: add the MVP to `ericlclee/affordablehousing`, then delete the separate `mparanzales/house-hackaton` repository after verification. The standalone simulator lives in `mvp/`; the existing model pipeline is unchanged. Public map geometry is under `dist/context/` so raw modelling datasets remain excluded by the root ignore rules. Trained-model integration and a hosted deployment remain separate next steps.

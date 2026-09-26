# CivisOpt implementation boundary

This extension implements the version 2.2 PRD's P0 decision: how three integer affordable-room allocations affect a fixed concept's break-even market sale value. It lives alongside the original illustrative planning room, without changing its model, resident layer, or the contributor-owned acquisition and training pipeline.

## Ownership

- `dist/civisopt.html` and `dist/civisopt/`: the new feasibility surface and deterministic finance/policy calculations.
- `dist/index.html`: a navigation link only; the existing map/3D tool stays available.
- `scripts/`, `MODEL_BRIEF.md`, modelling datasets and the original `dist/app.js`: retained from upstream.

There is no new scraper, shared spatial-layer downloader, classifier, backend, database, or LLM dependency. A single public register polygon is a dated P0 evidence snapshot, not a competing enrichment pipeline. The map is illustrative context; calculations do not depend on live tiles, external APIs, WebGL, or a trained approval model.

## Scope and limits

The fixed dwelling schedule, envelope and commercial ranges are editable assumptions. The actual site record is identified and corroborated, but its indicative register polygon is not a surveyed boundary or title check. A newer council schedule differs in area. The app surfaces that discrepancy and unresolved constraints; it does not certify a development envelope or claim planning compliance.

The companion `LONDON_PREAPP_POLICY_REGISTER.md` was not supplied. The user authorized provisional readiness checks. Validation documents, conditional statutory assessments, planning merits, Mayor referral and post-permission conditions therefore remain distinct review categories, with no automatic legal clearance. No live referral rule or proposed CIL relief is treated as enacted eligibility.

Financial output is an indicative sensitivity exercise. Assumptions have units, ranges and attribution; an omitted required cost/value stays unknown. Grant is excluded pending the evidence required by the PRD. Finance is an editable lump sum, so cash-flow IRR and sale-dependent finance are not inferred. S106 is an independent cost assumption, never derived from a model probability.

The original planning room's actor scores remain explicitly illustrative and isolated from this feasibility result. The new screen does not use them to choose scenarios, calculate financial outputs, or classify policy routes.

## Local use

From `mvp`, run `npm start` and open `http://127.0.0.1:4173/civisopt.html`. Python 3 serves the static files. No package installation or API key is needed. Run `npm test` with Node.js 22 or newer for deterministic arithmetic, policy boundary and adapter checks.

## Reproducibility

Save the structured scenario inputs with the pinned site/source snapshot. Commercial ranges, the unit schedule, the selected reference date and rule versions are part of the result. The exported brief must retain its indicative label, sources, open questions and calculated room denominator. Live map imagery is not evidence of constraint clearance.

## Deferred work

User-drawn sites, rigorous buildable envelopes, multiple physical massings, audited nearby precedents, professional costs, a complete borough readiness register and a validated contributor model are separate extensions. The P0 interface reports absent precedents and approval screening as unavailable.

Verification evidence and the independent financial row are in [CIVISOPT_VERIFICATION.md](CIVISOPT_VERIFICATION.md). The native file/print dialogs were not available to browser automation; saved data was independently restored with the production parser and the standalone brief was inspected at A4 dimensions.

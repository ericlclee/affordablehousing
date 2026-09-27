# CivisOpt verification

## Independent numerical row

The default illustrative envelope uses the 3,456.97 m² register polygon, 40% coverage, four storeys, 85% GIA efficiency, and 80% saleable efficiency. GIA is 4,701.4792 m². The explicitly entered dwelling schedule is 38 homes and 110 habitable rooms, occupying 2,580 m². The unused saleable headroom earns no invented receipts.

For the 35% target, the integer allocator produces 39 affordable rooms (35.4545%), including 24 social-rent rooms. Market dwelling area is 1,670 m², social area 560 m² and intermediate area 350 m². With illustrative base values of £6,500, £2,300 and £3,300 per respective m²:

- Market receipts: 1,670 × £6,500 = £10,855,000.
- Affordable receipts: 560 × £2,300 + 350 × £3,300 = £2,443,000.
- GDV: £13,298,000; no grant or other receipts.
- Build cost: 4,701.4792 × £2,800 = £13,164,141.76.
- Fees and contingency: 10% + 7% of build = £2,237,904.0992.
- Abnormal, finance, CIL, S106 and land: £400,000 + £500,000 + £200,000 + £200,000 + £2,000,000 = £3,300,000.
- Total cost including land: £18,702,045.8592.
- Development surplus: −£5,404,045.8592.
- With a fixed £1,500,000 target return, break-even is (£18,702,045.8592 + £1,500,000 − £2,443,000) / 1,670 = **£10,634.159197/m²**.

This row was independently rederived during review, rather than accepted from the displayed result. All commercial values remain illustrative. Neither a negative surplus nor meeting the displayed break-even price establishes a planning outcome.

## Automated checks

Run `npm test --prefix mvp` from the repository root. Tests cover independent finance arithmetic; geometry changes; integer housing/tenure counts; room-versus-unit denominators; exact policy thresholds despite display rounding; private/public/industrial land and date/scope rules; missing values versus zero; invalid source attribution and ranges; impossible/oversized schedules; ranking reversal when affordable receipts exceed market receipts; no qualifying balanced concept; adapter exclusions and unknown site facts; and an independent EPSG:27700 polygon-area calculation.

The model adapter never calls a scorer. Tests verify that supplying apparent model metadata cannot enable screening, post-submission fields do not affect mapped inputs, and model mapping does not change the S106 cost line.

## Integration boundary

The original `mvp/dist/app.js`, saved context, vendor code, root acquisition scripts, `MODEL_BRIEF.md`, requirements and setup script are unchanged. The original planning-room page receives only a navigation link, with a compact-screen navigation adjustment. No modelling data is committed.

## Known limits

The official register boundary remains indicative; its current planning status, title and site constraints have not been cleared. The separate 2024 council schedule is proposed policy, not adopted policy. No application-specific precedent has been independently cleared for inclusion. Contributor-model integration, a full borough readiness register, professional cost evidence, grant schedule and cash-flow IRR are unavailable. The model artifacts themselves arrived upstream and were preserved. The interface reports those limits instead of producing substitute values.

## Final local verification (26 September 2026)

- 20 automated checks passed with `npm test --prefix mvp`; JavaScript syntax and Git whitespace checks passed.
- Live browser: three concepts render; editing construction cost recalculates results; keyboard deletion of the base cost produces Unknown; public land rejects the 20% temporary-route comparison; 100% room preference produces no qualifying Balanced concept; source attribution is editable.
- Desktop width 1,280 px and phone width 390 px were checked. Final phone document width is 390 px, with wide detail tables scrolling inside their containers.
- The actual browser-downloaded JSON was parsed through the application's restore function and reproduced its saved calculated result exactly. Incompatible engine, policy, geometry and source manifests are rejected. The native file chooser was unavailable to the browser test tools; this check exercises the same restore function without that dialog.
- The standalone downloaded HTML brief was opened and inspected. At its A4 content width of 188 mm, the default brief occupied about 773 px vertically versus 1,039 px available inside the specified print margins. It includes the site outline, three scenarios, route states, low/base/high inputs, provenance, dated policy sources and open issues. The operating-system print/PDF dialog was not exercised.
- No browser console errors were reported. The original planning room still renders its WebGL scene and the new navigation link.

The UI extends the incumbent off-white, forest-green and copper palette, with the existing typography. Layout fixes address mobile containment and keyboard focus without replacing the original planning room's design.

After incorporating the upstream Proposal 106 and model deliveries, the 20 CivisOpt tests, Proposal 106 input regression and model browser/Python parity check all passed. The combined branch has no unresolved conflicts.

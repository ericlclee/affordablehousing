# Project 106 (final hackathon submission)

**Live demo:** https://project106.vercel.app (also https://proposal106-submission.vercel.app)

Project 106 simulates how a London housing proposal gets from an architect's idea to planning permission, and what each side gives up on the way.

- **Site.** Search by postcode, address or coordinates. The site is checked live against planning.data.gov.uk and GLA layers, and each constraint is tiered STOP / SERIOUS / CHECK / SUPPORT. The council policy pack (`data/councils.json`, 33 boroughs) updates with the site.
- **Your proposal.** Choose a new block (optionally with 0–3 commercial floors) or houses (1–9), or upload an OBJ massing (`samples/`). Set storeys, footprint, unit mix, affordable % by habitable room and the Social Rent share. Affordable floors show in blue, commercial in grey.
- **Planning and Section 106.** A council planning officer and a developer argue in one chat thread. The conversation pauses at every decision until you accept or reject. It ends with an outcome panel for planners and developers, including how to pitch the scheme to each.
- **Numbers.** Every number comes from the deterministic engine in `index.html` (`<script id="engine-src">`), independently re-checked in Python (`analysis/check_engine.py`).
  - **Approval probability** comes from the team model (`model/`, identical to `models/web/`), always shown next to the borough baseline, because it beats that baseline only modestly (test AUC 0.65 vs 0.62).
  - **Labelled assumptions:** costs, commercial value and land.
- **AI.** Typed questions go to `api/agent.js`, a Vercel function that uses the `GROQ_API_KEY` environment variable. The key never reaches the browser. The Section 106 rounds use prepared lines built from engine numbers. With no key, the whole app falls back to prepared answers.

Run locally from the repository root. AI answers then need "Connect AI" with your own key, stored only in your browser:

```sh
python3 -m http.server 4174 --bind 127.0.0.1 --directory mvp/project106
```

Not modelled: adding floors to an existing building, daylight and overshadowing, and real land prices. See the Assumptions sheet in the app.

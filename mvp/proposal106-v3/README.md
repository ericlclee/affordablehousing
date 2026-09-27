# Proposal 106 (v3, hackathon submission)

Live demo: https://proposal106-submission.vercel.app

Put a new building anywhere in London, then watch Planning, the Developer and Residents argue it through approval and Section 106.

- Location search by postcode, address or coordinates; live site constraints from planning.data.gov.uk and GLA layers.
- Council policy packs for all 33 London boroughs (`data/councils.json`).
- Approval probability from the team model (`model/approval_model.json`, `model/score.js`), always shown next to the borough baseline.
- Agents chat in one thread and pause at each decision point. Replies are scripted by default. "Connect AI" uses your own key, which is stored only in your browser and never in this repository.

Run locally from the repository root:

```sh
python3 -m http.server 4174 --bind 127.0.0.1 --directory mvp/proposal106-v3
```

> **Superseded by [`mvp/project106`](../project106/)**, the final submission (live at https://project106.vercel.app).

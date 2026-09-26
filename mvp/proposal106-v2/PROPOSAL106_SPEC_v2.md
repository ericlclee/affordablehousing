# Proposal 106, v2: redesign spec (Maria, 13:50)

This replaces the v1 layout. **Reuse the v1 engine verbatim** from `proposal106/index_v1.html`: `engine()`, the route logic, the break-even and the sweep. An independent Python check has already verified them.

## What Maria asked for (her words, condensed)
- Simpler. Less text. More empty space. Minimal and clear. Visually appealing, with motion.
- **Input any location.** Choosing the site or the council updates the policy information. That is key.
- **Stage 0: the architect inputs the model.** Either upload it from outside, or set parameters that adapt to the location.
- **New buildings only**, at three scales: Minor, Mid or Higher.
- **Stages:** 0 Architect → 1 Planning approval → 2 Section 106.
- **Layout:** architectural parameters on top; the map and model in the centre; **Planning agent on the left**; **Developer agent on the right**; results along the bottom.
- **Agents you can actually use:** you ask questions, and they answer and argue with each other like a WhatsApp chat, so you watch the argument happen.
- **Site constraints matter first.** In some areas a scheme is refused almost at once.

## Layout (desktop, 1280 px and up)
```
┌──────────────────────────────────────────────────────────────────────┐
│ 106  Proposal 106   [ Search postcode or address… ]  ● Southwark    │  top bar
│ Scale: (Minor)(Mid)(Higher)   Storeys ▭   Footprint ▭   ⤒ Upload       │  architect bar
│                                           [ Submit to planning → ]   │
├────────────┬─────────────────────────────────────────┬───────────────┤
│ PLANNING   │                                         │  DEVELOPER    │
│ council    │        3D MAP + MASSING (MapLibre)      │  appraisal    │
│ card       │                                         │  card         │
│ ─ chat ─   │                                         │  ─ chat ─     │
│ bubbles    │   [ Ask the table…            ⏎ ]       │  bubbles      │
├────────────┴─────────────────────────────────────────┴───────────────┤
│ ○ 0 Architect ─── ○ 1 Planning ─── ○ 2 Section 106                   │  results
│ 281 homes │ 35% affordable · Fast Track │ +£4.1m │ 289 days │ 88% vision │
└──────────────────────────────────────────────────────────────────────┘
```
- Generous gaps (24–32 px). Hairline dividers, not heavy card borders. A clear hierarchy: one big number per result.
- Below 1024 px, stack as: bar, map, results, then Planning and Developer as two tabs.
- **Motion** (respect `prefers-reduced-motion`):
  - the map flies to the site
  - the massing grows from 0 to its height
  - the council card crossfades
  - numbers count up
  - chat bubbles slide in after 0.6–1.2 s of "typing…" dots
  - the stage tracker fills

## Location and site
- **Search:** a UK postcode uses `https://api.postcodes.io/postcodes/<pc>` (CORS OK). Anything else uses `https://nominatim.openstreetmap.org/search?format=json&countrycodes=gb&limit=1&q=` (1 request per second at most, and only on Enter). Clicking the map also sets the site.
- **Council:** point-in-polygon against the London borough boundaries. Copy `mvp_chatgpt/src/One-Roof-London-v2/dist/data/london-boroughs.geojson` into `proposal106/data/`. Outside London, show "Outside London: London policies only".
- **Site shape:** by default a square of the chosen site area (slider 0.1–2 ha, default 0.5), centred on the point. "Draw site" lets you click corners and double-click to close. The site area feeds the engine.
- **Map:** MapLibre GL JS v5 (`https://unpkg.com/maplibre-gl@5/dist/maplibre-gl.js` + css) with the OpenFreeMap style `https://tiles.openfreemap.org/styles/liberty` (no key). Pitch 55, 3D buildings on. The massing renders as ONE `fill-extrusion` block, in the architect's green. The site boundary is a red dashed line.
- **"Match the street":** use `queryRenderedFeatures` on the building layer within 150 m to read neighbour heights (the render_height property). Show the median height and suggest storeys. Label it "from OpenStreetMap; many heights estimated".

## Stage 0: the architect's model
- **ONE BLOCK ONLY (Maria, 13:55): no podium or tower split.** The massing is a single block with footprint % and storeys. Internally, call the v1 engine with `podium_coverage = footprint`, `podium_storeys = storeys`, `tower_coverage = 0`, `tower_storeys = 0`, and keep the `params()` names.
- **Scale presets** (new build only). Each sets storeys and footprint for the current site area, aiming for the middle of the home range:
  - Minor: 10–49 homes, up to 6 storeys
  - Mid: 50–149 homes, 6–12 storeys
  - Higher: 150+ homes, 12+ storeys, with a smaller footprint
- **Controls on the bar:** storeys and footprint %. Unit mix and floor-to-floor sit in one "More" popover.
- **Upload:**
  - GeoJSON: a Polygon or MultiPolygon with `height` or `storeys` in its properties
  - OBJ: parse the vertices, take the footprint as the convex hull of the plan coordinates, and the height as the vertical range. Detect Y-up or Z-up by the larger range and assume metres. Say "Read as its outline massing".
  - Place it at the site centroid, then derive the engine parameters from it: footprint coverage (from the footprint area) and storeys = height ÷ floor-to-floor, as one block.
- **"Save as my vision"** happens automatically on "Submit to planning". Vision retained is measured against this.

## Stage 1: planning approval
1. **Point constraints, looked up live:** `https://www.planning.data.gov.uk/entity.json?latitude=..&longitude=..&limit=100` (CORS OK). Group the results by `dataset`. Also check the London layers (MOL, SIL, Opportunity Areas, town centres, protected vistas) through the GLA ArcGIS service that the research step identifies (`data/london_layers.json` gives the endpoints). Tiers:
   - **STOP** (policy says no in principle): green-belt, Metropolitan Open Land, Strategic Industrial Location, flood zone 3b / functional floodplain, scheduled monument, SSSI, ancient woodland
   - **SERIOUS**: listed building on site, conservation area (serious if above 6 storeys or 18 m), flood zone 3 (3a), protected vista
   - **CHECK**: flood zone 2, archaeological priority area, tree preservation zone, Article 4 (it barely affects a full application)
   - **SUPPORT** (in the scheme's favour): brownfield land, Opportunity Area, town centre

   Wording: "Red flag: policy presumption against housing here". Never say "rejected" or give odds.
2. **Council policy card** (left column, updates on every council change), from `data/councils.json`:
   - local plan (name, year, link)
   - affordable target
   - borough CIL
   - tall building definition
   - Mayoral CIL band
   - observed data for this council at this scale: refusal %, median days to decision, n
   - residential land value per hectare
   - average house price

   Anything missing shows "not researched" in grey.
3. **Route matrix** (the v1 engine): the temporary 20% route, H5 Fast Track 35/50%, or Viability Tested. Plus the Mayor flags.
4. **Planning's verdict in chat**, one of: "Supportable in principle", "Concerns", or "Red flags", with the 1–3 reasons that matter most. The Developer answers.

## Stage 2: Section 106, as a negotiation you watch
Rounds play in the chat, alternating left and right:
1. Planning asks for the route threshold, or the council target if that's higher and says so.
2. The Developer offers its maximum viable affordable % (the v1 `max_affordable` logic at base assumptions).
3. If there's a gap, the Developer proposes one lever:
   - a tenure shift toward shared ownership, which Planning checks against the 60% Social Rent rule
   - +N storeys, as a suggestion to the architect, which Planning checks against conservation area and height flags
   - lower land value, shown as "Developer: land price is fixed; that's the landowner's problem", in character
4. Planning counters with viability tested plus a review mechanism, and the extra time that costs (the observed difference: 359 vs 91 days for medium schemes; label it "observed").
5. They converge on the Balanced point: the v1 Nash sweep, with residents included only if invited.
6. Show the **Heads of terms** card: affordable % and tenure, the route, the review mechanism yes/no, Mayoral plus borough CIL in £, S106 £, and vision retained.

Every proposed change is a card with **Accept / Reject** for the user. Nothing changes without Accept.

## Agents
- **Chat look:** WhatsApp-style bubbles. Each agent has an avatar and a colour: Planning `#2B4C7E`, Developer `#B8741A`, Architect/you `#2E7D5B`, Residents `#7A5BA6`. There are timestamps, "typing…" dots, and a thin connector line when one answers the other.
- **Input:** "Ask the table…" under the map. `@planning`, `@developer` or `@residents` targets one agent; with no target, both answer, then may react to each other (one round).
- **Engine of answers:**
  - **Scripted mode** is the default and always works: intent matching over about 12 intents per agent. Examples: route, what do you need, red flags, CIL, how long, can we go higher, break even, max affordable, what would it take for 35%, land value, tenure, residents. Every number comes from the engine, the council pack or the constraint lookup. Keep lines under 25 words each, in character.
  - **Live hook:** `window.P106LLM = async ({agent, messages, state}) => string|null`. If it's defined and returns text, use it; otherwise use scripted. Also POST to `/api/agent` if the page is served with that endpoint, falling back on any error. Prompts include the role, a compact state JSON, the council pack and the rule "only use numbers given here".
- **Residents:** the "Invite residents" pill under the map adds a Residents avatar, their bubbles appear in the centre under the map, and they join the Balanced sweep.

## Results bar (bottom)
- The stage tracker, then five metrics with count-up:
  - **Homes** and scale
  - **Affordable %** and route chip
  - **Developer** surplus, with break-even £/m² small underneath
  - **Decision time:** the observed median for this council and scale, labelled "observed"
  - **Vision kept %**
- Plus a red-flag count chip.
- A tiny "Assumptions" link opens a sheet listing every placeholder: land value (£25m, or the council's land value per hectare × site area when researched, labelled "with-permission value, overstates existing use value"), sale £/m² (scaled from the council's average price relative to London, labelled "assumption"), borough CIL, S106.

## Tech
- `proposal106/index.html`, one file with inline CSS and JS. Google Fonts are allowed (localhost). Choose a distinctive but clean pairing: not Inter, not Space Grotesk.
- MapLibre from unpkg, pinned to v5. No other frameworks.
- Data files in `proposal106/data/`: `site.json` (v1 Walworth default), `london-boroughs.geojson`, `councils.json`, `london_layers.json`.
- Default state on load: Walworth Road Morrisons site (the v1 site), Mid preset, stage 0.
- `window.P106.params()` is kept with the same names.
- It must work on `http://localhost:4174/` with no console errors.

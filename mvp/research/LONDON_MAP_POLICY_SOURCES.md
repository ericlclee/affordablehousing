# London map and local-policy sources — checked 26 September 2026

## Downloaded borough boundaries

`london-boroughs-gla.geojson` — official Greater London Authority ArcGIS layer, fetched successfully. GeoJSON FeatureCollection, 33 features (32 boroughs and City of London), 1,933,314 bytes. Coordinates requested as EPSG:4326 (longitude/latitude). Properties include `name` and `gss_code`.

Metadata: https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/301

Download: https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/301/query?where=1%3D1&outFields=*&outSR=4326&f=geojson

Metadata identifies these as official borough polygons, references 2017 geography, and states a monthly update frequency. Do not describe the geometry as a new 2026 boundary survey. License: Open Government Licence v3.0. Suggested visible attribution: “Borough boundaries: Greater London Authority / Ordnance Survey Open Data. Contains public sector information licensed under the Open Government Licence v3.0.”

## Verified neighbourhood map anchors

The three coordinates below are official TfL station coordinates, fetched from its public API. A point-in-polygon test against the downloaded GLA geometry verifies each borough. These are neighbourhood/station anchors, **not vacant plots, housing allocations, actual project boundaries, or a claim that housing can be built on the station**. Label scenarios “near Stratford”, “near Dalston Junction” and “near Kentish Town”, with “Illustrative site; real neighbourhood context”.

| Anchor | Latitude | Longitude | Borough checked spatially | TfL ID |
|---|---:|---:|---|---|
| Stratford | 51.541508 | -0.002410 | Newham | HUBSRA |
| Dalston Junction Rail Station | 51.546116 | -0.075137 | Hackney | 910GDALS |
| Kentish Town | 51.550409 | -0.140545 | Camden | HUBKTN |

Coordinate sources, responses saved as stratford-tfl.json, dalston-tfl.json and kentish-tfl.json:

- https://api.tfl.gov.uk/StopPoint/Search?query=Stratford&modes=tube&maxResults=4
- https://api.tfl.gov.uk/StopPoint/Search?query=Dalston%20Junction&maxResults=3
- https://api.tfl.gov.uk/StopPoint/Search?query=Kentish%20Town&modes=tube&maxResults=3

## Concrete local context and safe short copy

### Stratford — Newham

Official current plan landing page: https://www.newham.gov.uk/planning-development-conservation/planning-policy-local-plan/2

Former LLDC area: https://www.newham.gov.uk/planning-development-conservation/london-legacy-development-corporation-lldc

Verified: Newham regained planning powers for its former LLDC area on 1 December 2024. Its council page says the LLDC Local Plan and supplementary guidance continue to apply in that area until replaced by the new Newham Local Plan. The page links the applicable policy boundary map, LLDC plan, carbon-offset and planning-obligations SPDs. This is a concrete example of why borough identification alone does not identify all applicable policy.

Safe UI copy: “Newham Council. Around Stratford, check whether the plot falls within the former LLDC policy area. The council determines applications, while that area's local plan and guidance can still apply.”

Policy status warning: The current adopted-plan page links Newham Local Plan 2018. The examination news page records a soundness report, subject to modifications, on 18 August 2026; it does not itself confirm adoption of the replacement. Do not use the search-indexed 2022/2024 draft tall-building-zone maxima as adopted rules.

Examination source: https://www.newham.gov.uk/planning-development-conservation/newham-local-plan-examination/2

### Dalston — Hackney

Adopted local plan: https://www.hackney.gov.uk/planning-and-building/planning-policies-and-local-plan/local-plan/local-plan-2033-lp33

Adopted Dalston SPD: https://www.hackney.gov.uk/planning-and-building/planning-policies-and-local-plan/supplementary-planning-documents-and-guidance/dalston-supplementary-planning-document

Property-level designations lookup: https://map2.hackney.gov.uk/check-local-planning-information/

Verified: LP33 was adopted 22 July 2020. The council links an adopted Dalston Plan 2025 with local development/public-space guidance reflecting built heritage, local identity, communities and Ridley Road market. It supports LP33 rather than constituting a separate blanket height limit.

Safe UI copy: “Hackney Council. Test the proposal against LP33 and the Dalston Plan: built heritage, local character, public space and the town centre's existing uses matter alongside housing delivery.”

Do not lift precise garden-sunlight or unit targets from the web page's historic Draft Dalston Plan section and label them final 2025 clauses without reading the adopted PDF. Do not declare the anchor within a conservation area based only on neighbourhood name.

### Kentish Town — Camden

Adopted plan status: https://www.camden.gov.uk/local-plan-documents

Kentish Town Planning Framework: https://www.camden.gov.uk/kentish-town-planning-framework1

Neighbourhood plan: https://www.camden.gov.uk/kentish-town-neighbourhood-forum

Affordable housing statement requirements: https://www.camden.gov.uk/affordable-housing-statements

Verified: the current council page identifies the 2017 Local Plan as adopted; the replacement remains labelled draft/examination. Kentish Town's framework, adopted 17 July 2020, seeks coordinated mixed-use development with industrial, commercial and creative activity alongside homes. The neighbourhood plan was adopted 19 September 2016. These frameworks have mapped areas, not automatic borough-wide applicability.

Concrete documentation requirement: Camden asks for an affordable housing statement where there is at least one additional home and at least 100 square metres of additional residential floorspace. For schemes with 1,000 square metres GIA or more, it requires a market/affordable tenure breakdown, affordable-home layouts, rent and service-charge details. This is a submission requirement, not a single fixed affordable percentage or approval outcome.

Safe UI copy: “Camden Council. Around Kentish Town, check the neighbourhood plan and framework boundary. In the framework area, housing must be considered alongside employment uses and coordinated redevelopment. Larger schemes need a detailed affordable housing statement.”

## UI interpretation limits

- GeoJSON can identify borough. It cannot determine conservation areas, listed buildings, flood zones, tall-building suitability, site allocations or exact applicable plan without additional spatial layers.
- Council differences should be expressed as applicable documents and design/obligation considerations, never invented strictness scores or probabilities.
- Use a scenario response such as “Further assessment needed”, with concrete prompts: height/context, neighbours/daylight, public space, tenure mix, infrastructure and relevant local designation checks.
- Shared London affordable-housing framework includes the March 2026 additional time-limited route. Avoid universal 35% or 50% pass/fail thresholds. Source: https://www.london.gov.uk/md3490-support-housebuilding-london-plan-guidance-shblpg
- No precise height limit, site availability, existing-building height or mapped conservation designation was verified for these three station anchors during this bounded check.

// One manually checked public brownfield-register record for the P0 concept.
// Boundary coordinates are returned by the official GLA ArcGIS layer in WGS84.
// The published hectares value (0.346 ha) is the same record's rounded area;
// its projected geometry area is 3,456.97 m². This is indicative register
// geometry, not a surveyed, title, or legal parcel boundary.
export const SITE = {
  id: '17080144',
  name: 'Motor Village Croydon, 121 Canterbury Road',
  borough: 'Croydon',
  areaM2: 3456.97,
  areaBasis: 'GLA Brownfield Register polygon area, calculated in EPSG:27700 (3,456.9699 m²; register attribute is 0.346 ha).',
  projectedGeometry: {
    type: 'Polygon',
    crs: 'EPSG:27700',
    coordinates: [[
      [530949.9484999999, 166851.4985000007],
      [530939.1475, 166763.20380000025],
      [530876.6498999996, 166818.0680999998],
      [530878.1835000003, 166829.72470000014],
      [530949.9484999999, 166851.4985000007],
    ]],
  },
  geometry: {
    type: 'Polygon',
    coordinates: [[
      [-0.11951002935235784, 51.38560976792501],
      [-0.12054877439434492, 51.385430611933124],
      [-0.1205750962536195, 51.385326207777794],
      [-0.11969771197571288, 51.3848187562725],
      [-0.11951002935235784, 51.38560976792501],
    ]],
  },
  sourceName: 'Greater London Authority Brownfield Register layer, feature 2862 / site reference 17080144',
  sourceUrl: 'https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101/query?where=sitereference%3D%2717080144%27&outFields=*&returnGeometry=true&outSR=4326&f=geojson',
  sourceSnapshotAt: '2026-09-26',
  recordDate: '2017-12-31',
  verification: 'Corroborated against Croydon Council’s 2024 Local Plan proposal-site schedule for the named site and car-showroom/garage use. The council schedule rounds its separate proposal site area to 0.36 ha; this feature remains 0.346 ha. The GLA register explicitly says its GIS boundaries are indicative and should be confirmed with the borough. This is public-record corroboration, not surveyed or title verification.',
  unknowns: [
    'The GLA layer marks its boundary as indicative; Croydon Council confirmation or a site survey is still needed before treating it as a definitive parcel.',
    'Current ownership, title, and land control have not been checked. The register’s older ownership-status field is not treated as current evidence.',
    'No buildable area, floorspace capacity, height, massing, or development envelope is inferred from the register polygon.',
    'Site-specific constraints, local policy requirements, and current planning status need a property-level check.',
  ],
};

export const SOURCE_RECORDS = [
  {
    id: 'gla-brownfield-17080144',
    name: 'GLA Brownfield Register feature 17080144',
    url: 'https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101/query?where=sitereference%3D%2717080144%27&outFields=*&returnGeometry=true&outSR=4326&f=geojson',
    date: '2017-12-31',
    status: 'Public register record; snapshot fetched 2026-09-26',
    note: 'Names Motor Village Croydon, 121 Canterbury Road; publishes 0.346 ha, borough Croydon, 28 net dwellings and a polygon. Its source layer warns that GIS boundaries are indicative and should be confirmed with the borough. Open Government Licence v3.0.',
  },
  {
    id: 'gla-brownfield-layer-metadata',
    name: 'GLA Brownfield Register layer metadata',
    url: 'https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101',
    date: 'Layer metadata checked 2026-09-26',
    status: 'Official GLA GIS layer metadata',
    note: 'Identifies polygon geometry, OGL v3.0, and explicitly says boundaries are indicative and the relevant borough should be contacted to confirm accuracy.',
  },
  {
    id: 'croydon-local-plan-2024-site-8',
    name: 'Croydon Local Plan 2024, Appendix 7 proposal site 8',
    url: 'https://www.croydon.gov.uk/sites/default/files/2024-11/croydon-local-plan-2024-chapter-15-end.pdf',
    date: '2024',
    status: 'Proposed Croydon Local Plan 2024 partial-review schedule; not adopted',
    note: 'Lists Motor Village Croydon, 121 Canterbury Road, as a 0.36 ha car showroom/garage with mixed-use development including employment at ground floor and residential above; indicative capacity 95 homes and short-term phasing. This is a proposed site allocation in the partial review, not adopted policy; its separate proposal-site area is not substituted for the 0.346 ha register polygon.',
  },
  {
    id: 'croydon-local-plan-examination-status',
    name: 'Croydon Local Plan review examination status',
    url: 'https://www.croydon.gov.uk/planning-and-regeneration/planning-policy/local-plan-review/local-plan-review-examination',
    date: 'Page checked 2026-09-26',
    status: 'Submitted plan under examination; proposed main modifications stage',
    note: 'Council says the plan was submitted for examination on 2024-11-29, hearings ended 2025-10-23, and the Inspectorate requested a timetable to prepare proposed main modifications for later consultation. Do not present the 2024 site schedule/allocation as adopted policy.',
  },
  {
    id: 'london-plan-2021-h5',
    name: 'The London Plan 2021, Chapter 4, Policy H5',
    url: 'https://www.london.gov.uk/programmes-strategies/planning/london-plan/the-london-plan-2021-online/chapter-4-housing',
    date: '2021',
    status: 'Adopted London Plan policy',
    note: 'Baseline threshold approach: 35% affordable by habitable room; 50% for specified public-sector and industrial land cases. Fast Track also requires no public subsidy, compliant tenure, other policy/obligation compliance, and regard to the strategic 50% target plus a grant application. Model only after land type and all other criteria are checked.',
  },
  {
    id: 'shblpg-2026',
    name: 'Support for Housebuilding London Plan Guidance (March 2026)',
    url: 'https://www.london.gov.uk/media/112374/download?attachment=',
    date: '2026-03',
    status: 'Adopted time-limited London Plan Guidance; material consideration',
    note: 'Conditional alternative route, parallel to H5, for applications validated by 2028-03-31. Thresholds depend on land type; exclusions, tenure terms, and implementation review apply. This guidance does not guarantee permission or replace H5.',
  },
  {
    id: 'md3490-shblpg-adoption',
    name: 'GLA Mayoral Decision MD3490 adopting SHBLPG',
    url: 'https://www.london.gov.uk/md3490-support-housebuilding-london-plan-guidance-shblpg',
    date: '2026-03-24 signed; 2026-03-25 published',
    status: 'Official GLA adoption decision',
    note: 'MD3490 is dated 24 March 2026 and published 25 March 2026. The guidance is dated March 2026; it does not specify a separate commencement date. Confirms the new route is time-limited, departs from H5, and is a material consideration rather than statutory development-plan policy.',
  },
];

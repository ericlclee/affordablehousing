# CivisOpt P0 sources — checked 26 September 2026

## Selected site record

**Motor Village Croydon, 121 Canterbury Road, Croydon** is represented by GLA Brownfield Register feature `objectid=2862`, `sitereference=17080144`. The feature returns a polygon in WGS84 and gives an area of **0.346 ha**. Independently applying the shoelace formula to the same projected polygon ring (EPSG:27700) gives **3,456.969864 m²**; the snapshot rounds this to 3,456.97 m². Its record date is `firstaddeddate=2017-12-31`; the register has no last-updated date for this feature. WGS84 and projected rings from the same record are retained in [`snapshot.js`](../dist/civisopt/snapshot.js).

The feature is corroborated by Croydon Council’s 2024 Local Plan Appendix 7, which identifies the same site as a 0.36 ha car showroom and garage, with a mixed-use proposal (employment at ground floor, residential above), an indicative capacity of 95 homes, and short-term phasing. **This Appendix is part of the proposed Local Plan 2024 partial review and is not adopted policy.** The council’s examination page says the plan was submitted on 29 November 2024, hearings ended 23 October 2025, and it is progressing through proposed main modifications. The council’s current adopted plan remains the Croydon Local Plan 2018 unless and until the partial review is adopted. The **0.36 ha figure is from that separate proposed-plan schedule and is not the area of the 0.346 ha register polygon.** Use the geometry and 3,456.97 m² only as a brownfield-register site footprint; do not infer a buildable envelope, floorspace, or height from it.

The GLA GIS layer is published under the Open Government Licence v3.0. Its metadata explicitly cautions that GIS boundaries are indicative and says to contact the borough to confirm accuracy. The Council’s site-allocation policy text points to its Policies Map for detailed proposal boundaries. Accordingly, this snapshot records an **official-record corroboration**, not a surveyed boundary, legal parcel, or title check. Current ownership and land control remain unknown; an older register ownership label is not promoted as current evidence.

- [Single GLA Brownfield Register feature with geometry](https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101/query?where=sitereference%3D%2717080144%27&outFields=*&returnGeometry=true&outSR=4326&f=geojson)
- [GLA Brownfield Register layer metadata and boundary caveat](https://gis.london.gov.uk/arcgis/rest/services/apps/planning_data_map_02/MapServer/101)
- [Croydon Local Plan 2024, Appendix 7](https://www.croydon.gov.uk/sites/default/files/2024-11/croydon-local-plan-2024-chapter-15-end.pdf)
- [Croydon policy PW DM6 and site allocation 8](https://www.croydon.gov.uk/sites/default/files/2024-07/croydon-local-plan-%20detailed-policies-and-proposals-proposed-submission-draft-part-2.pdf)
- [Croydon Local Plan review examination status](https://www.croydon.gov.uk/planning-and-regeneration/planning-policy/local-plan-review/local-plan-review-examination)

The GLA record, proposed Local Plan schedule, and proposal-site boundary source describe different data products. Keep their area and boundary statements tied to their own source. The proposed plan schedule’s 95-home figure is indicative context, not an adopted allocation, independently verified development capacity, or a design envelope.

## Affordable-housing route conditions to model

The **adopted London Plan 2021 Policy H5 remains operative**. For major development triggering an affordable-housing requirement, the baseline Fast Track thresholds are measured by **habitable room**: 35% generally; 50% for public-sector land without a Mayoral portfolio agreement; and 50% for the specified industrial land categories where the scheme results in a net loss of industrial capacity. Threshold alone is insufficient. H5 Fast Track also requires on-site provision without public subsidy, H6-consistent tenure, compliance with relevant policies and obligations to the borough/Mayor’s satisfaction, and regard to the strategic 50% target plus a grant application. H5’s default H6 tenure mix is at least 30% low-cost rent, at least 30% intermediate, and the remaining 40% according to borough need. Present shares by rooms, units, and floorspace; the Plan says affordable and market rooms should be comparable in average size, otherwise habitable floorspace may be more appropriate. Schemes that fail Fast Track conditions follow the Viability Tested Route.

The March 2026 Support for Housebuilding London Plan Guidance adds a **conditional, time-limited route in parallel with H5**. It is a material consideration and departs from H4/H5/H6; it is not an adopted development-plan policy replacement and not a consent prediction. For planning applications **validated on or before 31 March 2028**, threshold is by habitable room and depends on site type:

- Private land: 20%.
- Public land: 35%.
- Industrial land with capacity not re-provided: 35%; if capacity is re-provided: 20%.
- Utilities sites: 20% only with evidence of substantial decontamination, enabling, and remediation costs.

The route also requires at least 60% of the affordable provision to be Social Rent, with the remainder intermediate (Build to Rent has its own tenure terms). It excludes Grey/Green Belt sites or land released from them; PBSA or large-scale shared-living schemes, or schemes where those uses comprise at least 50% of residential GIA; and schemes demolishing existing affordable housing. A qualifying route removes the upfront viability assessment; an early-stage review applies if the agreed implementation milestone is missed (default: first-floor slab within 30 months), with a five-year long-stop. Do not show the route as eligible until land category, use exclusions, threshold, tenure, and date window are all checked.

- [London Plan 2021, Chapter 4 / H5 / H6](https://www.london.gov.uk/programmes-strategies/planning/london-plan/the-london-plan-2021-online/chapter-4-housing)
- [Final Support for Housebuilding London Plan Guidance (March 2026), section 4](https://www.london.gov.uk/media/112374/download?attachment=)
- [Mayoral decision MD3490 adopting the guidance](https://www.london.gov.uk/md3490-support-housebuilding-london-plan-guidance-shblpg)

MD3490 shows **24 March 2026** as the date signed and **25 March 2026** as the publication date. The guidance itself is dated only “March 2026” and supplies no separate commencement date. For a conservative policy engine `valid_from`, use 25 March 2026 (the first verified publication date) unless a primary legal/policy notice establishes an earlier commencement. Do not invent 1 March from the month label.

## Attribution and limits

Attribute the boundary source as **Greater London Authority, Brownfield Register, Open Government Licence v3.0**. Keep the snapshot date and original record date distinct. The local-plan cross-check supports identifying the site and reporting the separate 0.36 ha proposal-site figure; it does not upgrade the GLA polygon to a legal boundary. No ownership/title, exact constraints, viability, buildable floor area, massing, or site-specific design envelope is established by these sources.

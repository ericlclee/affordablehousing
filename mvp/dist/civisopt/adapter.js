// Narrow, allowlisted boundary between CivisOpt scenarios and a future
// contributor-owned approval/S106 model. No scoring code lives here.

const bedroomKeys = ['studio', '1b', '2b', '3b_plus'];
const NOT_APPLICABLE = 'not_applicable';

function isNotApplicable(value) {
  return value === NOT_APPLICABLE || Boolean(value && typeof value === 'object' && (value.state === NOT_APPLICABLE || value.status === NOT_APPLICABLE));
}

function containsNotApplicable(value) {
  if (isNotApplicable(value)) return true;
  if (Array.isArray(value)) return value.some(containsNotApplicable);
  if (value && typeof value === 'object') return Object.values(value).some(containsNotApplicable);
  return false;
}

function featureState(mappedValue, ...sources) {
  if (sources.some(containsNotApplicable)) return NOT_APPLICABLE;
  return mappedValue === null ? 'unknown' : 'known';
}

function finiteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function nonNegativeNumber(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null;
}

function boolOrNull(value) {
  return typeof value === 'boolean' ? value : null;
}

function enumOrNull(value, allowed) {
  return typeof value === 'string' && allowed.includes(value) ? value : null;
}

function unitMix(allocation) {
  if (!Array.isArray(allocation) || allocation.length === 0) return null;

  const counts = Object.fromEntries(bedroomKeys.map(key => [key, 0]));
  let total = 0;
  for (const row of allocation) {
    if (!row || typeof row !== 'object') return null;
    const homes = nonNegativeNumber(row.homes);
    if (homes === null || !Number.isInteger(homes)) return null;

    const bedrooms = row.bedrooms;
    let key;
    if (bedrooms === 0 || bedrooms === 'studio' || bedrooms === 'Studio') key = 'studio';
    else if (bedrooms === 1 || bedrooms === '1' || bedrooms === '1b') key = '1b';
    else if (bedrooms === 2 || bedrooms === '2' || bedrooms === '2b') key = '2b';
    else if (Number.isInteger(bedrooms) && bedrooms >= 3 || ['3', '3+', '3b_plus'].includes(bedrooms)) key = '3b_plus';
    else return null;

    counts[key] += homes;
    total += homes;
  }

  if (total === 0) return null;
  return Object.fromEntries(bedroomKeys.map(key => [key, counts[key] / total * 100]));
}

function roomPct(affordableRooms, totalRooms) {
  const affordable = nonNegativeNumber(affordableRooms);
  const total = nonNegativeNumber(totalRooms);
  if (affordable === null || total === null || !Number.isInteger(affordable) || !Number.isInteger(total) || total === 0 || affordable > total) return null;
  return affordable / total * 100;
}

function socialRentShare(affordableRooms, socialRooms) {
  const affordable = nonNegativeNumber(affordableRooms);
  const social = nonNegativeNumber(socialRooms);
  if (affordable === null || social === null || !Number.isInteger(affordable) || !Number.isInteger(social) || affordable === 0 || social > affordable) return null;
  return social / affordable * 100;
}

function siteValue(siteFacts, key) {
  // Absence of a versioned contributor record is unknown context, not evidence
  // that a designation is false. Explicit booleans remain distinct from null.
  if (!siteFacts || typeof siteFacts !== 'object' || typeof siteFacts.version !== 'string' || !siteFacts.version.trim()) {
    return isNotApplicable(siteFacts?.[key]) ? siteFacts[key] : null;
  }
  return siteFacts[key] === undefined ? null : siteFacts[key];
}

/**
 * Map a canonical feasibility Scenario and versioned contributor SiteFacts
 * into the documented, pre-submission feature allowlist. Financial/policy
 * outputs, UI-only affordable targets, and post-submission fields are omitted.
 */
export function canonicalModelInput(scenario, siteFacts = null) {
  const s = scenario && typeof scenario === 'object' ? scenario : {};
  const geometry = s.geometry && typeof s.geometry === 'object' ? s.geometry : {};
  const allocation = s.allocation;
  const totalRooms = s.totalHabitableRooms;
  const affordableRooms = s.affordableHabitableRooms;
  const siteArea = nonNegativeNumber(geometry.siteAreaM2);
  const homes = nonNegativeNumber(s.homes);

  const mix = unitMix(allocation);
  const siteBoolean = key => boolOrNull(siteValue(siteFacts, key));
  const ptal = finiteNumber(siteValue(siteFacts, 'ptal2023'));
  const deprivation = finiteNumber(siteValue(siteFacts, 'deprivationDecile'));

  const input = {
    storeys: nonNegativeNumber(geometry.storeys),
    homes,
    height_m: nonNegativeNumber(geometry.heightM),
    site_area_m2: siteArea,
    coverage_ratio: nonNegativeNumber(geometry.coverageRatio),
    gia_m2: nonNegativeNumber(geometry.giaM2),
    density_homes_per_ha: siteArea !== null && siteArea > 0 && homes !== null ? homes / siteArea * 10000 : null,
    unit_mix_pct_by_bedrooms: mix,
    affordable_habitable_rooms_pct: roomPct(affordableRooms, totalRooms),
    social_rent_share_of_affordable_pct: socialRentShare(affordableRooms, s.socialHabitableRooms),
    development_type: enumOrNull(s.developmentType, ['new build', 'conversion', 'extension', 'change of use']),
    demolition: boolOrNull(s.demolition),
    amenities: {
      gym: boolOrNull(s.amenities?.gym),
      pool: boolOrNull(s.amenities?.pool),
      basement: boolOrNull(s.amenities?.basement),
      roof_terrace: boolOrNull(s.amenities?.roofTerrace),
      concierge: boolOrNull(s.amenities?.concierge),
      communal_amenity: boolOrNull(s.amenities?.communalAmenity),
    },
    non_residential_floor_area_m2: nonNegativeNumber(s.nonResidentialAreaM2),
    car_spaces: nonNegativeNumber(s.carSpaces),
    cycle_spaces: nonNegativeNumber(s.cycleSpaces),
    scheme_type: enumOrNull(s.schemeType, ['standard', 'co-living', 'student', 'HMO']),
    site_facts_version: siteFacts && typeof siteFacts.version === 'string' && siteFacts.version.trim() ? siteFacts.version : null,
    borough: typeof siteValue(siteFacts, 'borough') === 'string' ? siteValue(siteFacts, 'borough') : null,
    conservation_area: siteBoolean('conservationArea'),
    article_4_area: siteBoolean('article4Area'),
    listed_building_on_site: siteBoolean('listedBuildingOnSite'),
    tree_preservation_zone: siteBoolean('treePreservationZone'),
    flood_zone_2: siteBoolean('floodZone2'),
    flood_zone_3: siteBoolean('floodZone3'),
    green_belt: siteBoolean('greenBelt'),
    brownfield_register: siteBoolean('brownfieldRegister'),
    opportunity_area: siteBoolean('opportunityArea'),
    strategic_industrial_land: siteBoolean('strategicIndustrialLand'),
    town_centre: siteBoolean('townCentre'),
    ptal_2023: ptal,
    deprivation_decile: deprivation,
  };

  const rawSiteValue = key => siteFacts && typeof siteFacts === 'object' ? siteFacts[key] : undefined;
  const amenitySource = key => s.amenities && typeof s.amenities === 'object' ? s.amenities[key] : undefined;
  input.feature_states = {
    storeys: featureState(input.storeys, geometry.storeys),
    homes: featureState(input.homes, s.homes),
    height_m: featureState(input.height_m, geometry.heightM),
    site_area_m2: featureState(input.site_area_m2, geometry.siteAreaM2),
    coverage_ratio: featureState(input.coverage_ratio, geometry.coverageRatio),
    gia_m2: featureState(input.gia_m2, geometry.giaM2),
    density_homes_per_ha: featureState(input.density_homes_per_ha, s.homes, geometry.siteAreaM2),
    unit_mix_pct_by_bedrooms: featureState(input.unit_mix_pct_by_bedrooms, allocation),
    affordable_habitable_rooms_pct: featureState(input.affordable_habitable_rooms_pct, affordableRooms, totalRooms),
    social_rent_share_of_affordable_pct: featureState(input.social_rent_share_of_affordable_pct, affordableRooms, s.socialHabitableRooms),
    development_type: featureState(input.development_type, s.developmentType),
    demolition: featureState(input.demolition, s.demolition),
    'amenities.gym': featureState(input.amenities.gym, amenitySource('gym')),
    'amenities.pool': featureState(input.amenities.pool, amenitySource('pool')),
    'amenities.basement': featureState(input.amenities.basement, amenitySource('basement')),
    'amenities.roof_terrace': featureState(input.amenities.roof_terrace, amenitySource('roofTerrace')),
    'amenities.concierge': featureState(input.amenities.concierge, amenitySource('concierge')),
    'amenities.communal_amenity': featureState(input.amenities.communal_amenity, amenitySource('communalAmenity')),
    non_residential_floor_area_m2: featureState(input.non_residential_floor_area_m2, s.nonResidentialAreaM2),
    car_spaces: featureState(input.car_spaces, s.carSpaces),
    cycle_spaces: featureState(input.cycle_spaces, s.cycleSpaces),
    scheme_type: featureState(input.scheme_type, s.schemeType),
    borough: featureState(input.borough, rawSiteValue('borough')),
    conservation_area: featureState(input.conservation_area, rawSiteValue('conservationArea')),
    article_4_area: featureState(input.article_4_area, rawSiteValue('article4Area')),
    listed_building_on_site: featureState(input.listed_building_on_site, rawSiteValue('listedBuildingOnSite')),
    tree_preservation_zone: featureState(input.tree_preservation_zone, rawSiteValue('treePreservationZone')),
    flood_zone_2: featureState(input.flood_zone_2, rawSiteValue('floodZone2')),
    flood_zone_3: featureState(input.flood_zone_3, rawSiteValue('floodZone3')),
    green_belt: featureState(input.green_belt, rawSiteValue('greenBelt')),
    brownfield_register: featureState(input.brownfield_register, rawSiteValue('brownfieldRegister')),
    opportunity_area: featureState(input.opportunity_area, rawSiteValue('opportunityArea')),
    strategic_industrial_land: featureState(input.strategic_industrial_land, rawSiteValue('strategicIndustrialLand')),
    town_centre: featureState(input.town_centre, rawSiteValue('townCentre')),
    ptal_2023: featureState(input.ptal_2023, rawSiteValue('ptal2023')),
    deprivation_decile: featureState(input.deprivation_decile, rawSiteValue('deprivationDecile')),
  };

  return input;
}

/**
 * No artifact and evidence package has been authorized/evaluated for this
 * build. This deliberately cannot be enabled by passing truthy caller data.
 */
export function screeningAvailability() {
  return {
    status: 'unavailable',
    label: 'Approval screening unavailable',
    reasons: [
      'No authorized, versioned contributor model artifact is installed.',
      'The required validation manifest and integration review have not been accepted.',
    ],
  };
}

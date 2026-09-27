// CivisOpt P0: deterministic, indicative geometry, housing allocation and appraisal.
// All money is GBP; areas are m². No approval probability is calculated here.

export const ENGINE_VERSION = 'civisopt-engine-v1-2026-09-26';

export const POLICY_SOURCES = Object.freeze({
  h5: { version: 'London Plan 2021, Policy H5', url: 'https://www.london.gov.uk/programmes-strategies/planning/london-plan/the-london-plan-2021-online/chapter-4-housing' },
  temporary2026: { version: 'Support for Housebuilding London Plan Guidance, adopted March 2026', url: 'https://www.london.gov.uk/media/112374/download?attachment=' },
});

const assumption = (label, unit) => ({ label, unit, low: null, base: null, high: null, source: 'User evidence required' });

export const DEFAULT_INPUTS = Object.freeze({
  envelope: { storeys: 4, coverageRatio: 0.4, floorHeightM: 3, giaEfficiency: 0.85, saleableEfficiency: 0.8 },
  unitMix: [
    { bedrooms: 1, homes: 12, areaM2: 50, habitableRooms: 2 },
    { bedrooms: 2, homes: 18, areaM2: 70, habitableRooms: 3 },
    { bedrooms: 3, homes: 8, areaM2: 90, habitableRooms: 4 },
  ],
  assumptions: {
    marketValuePerM2: assumption('Market sale value', '£/market m²'),
    socialTransferPerM2: assumption('Social rent transfer value', '£/social m²'),
    intermediateTransferPerM2: assumption('Intermediate transfer value', '£/intermediate m²'),
    buildCostPerGiaM2: assumption('Construction cost', '£/GIA m²'),
    abnormalCosts: assumption('Abnormal costs', '£'),
    feesPctOfBuild: assumption('Professional fees', '% of build cost'),
    contingencyPctOfBuild: assumption('Contingency', '% of build cost'),
    financeCosts: assumption('Finance costs', '£'),
    cilCosts: assumption('Enacted CIL', '£'),
    s106Costs: assumption('Documented Section 106', '£'),
    landCost: assumption('Land cost or existing-use value plus premium', '£'),
    otherReceipts: assumption('Other receipts', '£'),
    targetReturn: assumption('Fixed target developer return', '£'),
  },
  policy: { landType: 'unknown', applicationDate: null, schemeType: 'sale', socialRentSharePct: 60, otherConditionsConfirmed: false },
  preferenceMinAffordablePct: 35,
});

const ASSUMPTION_KEYS = Object.keys(DEFAULT_INPUTS.assumptions);
const ROUTE_CHECKS = {
  h5FastTrack: ['noPublicSubsidy', 'boroughPolicyChecked', 'siteConstraintsChecked', 'otherObligationsChecked'],
  temporary2026: ['noExcludedLand', 'noAffordableDemolition', 'supportedResidentialUse', 'boroughPolicyChecked', 'siteConstraintsChecked', 'reviewMechanismChecked'],
};
const ROUTE_CHECK_LABELS = {
  noPublicSubsidy: 'no public subsidy', boroughPolicyChecked: 'borough policy',
  siteConstraintsChecked: 'site constraints', otherObligationsChecked: 'other obligations',
  noExcludedLand: 'no excluded Green Belt, Grey Belt or released land',
  noAffordableDemolition: 'no loss of existing affordable housing',
  supportedResidentialUse: 'eligible residential use', reviewMechanismChecked: 'required review mechanism',
};
const hasNumber = value => typeof value === 'number' && Number.isFinite(value);
const round = (value, places = 6) => value == null ? null : Number(value.toFixed(places));
const error = (field, message) => ({ field, message });

function validate(site, inputs) {
  const errors = [];
  const area = site?.areaM2;
  if (!hasNumber(area) || area <= 0) errors.push(error('site.areaM2', 'A positive published metric site area is required.'));
  const env = inputs?.envelope || {};
  if (!Number.isInteger(env.storeys) || env.storeys < 1) errors.push(error('envelope.storeys', 'Storeys must be a positive whole number.'));
  for (const [key, min, max, openMin] of [
    ['coverageRatio', 0, 1, true], ['floorHeightM', 0, Infinity, true],
    ['giaEfficiency', 0, 1, true], ['saleableEfficiency', 0, 1, true],
  ]) {
    const n = env[key];
    if (!hasNumber(n) || n < min || (openMin && n === min) || n > max) errors.push(error(`envelope.${key}`, `Enter ${key} as a number ${openMin ? 'above' : 'at least'} ${min} and at most ${max === Infinity ? 'a finite positive value' : max}.`));
  }
  if (!Array.isArray(inputs?.unitMix) || inputs.unitMix.length === 0) errors.push(error('unitMix', 'At least one dwelling type is required.'));
  else inputs.unitMix.forEach((row, i) => {
    if (!Number.isInteger(row?.bedrooms) || row.bedrooms < 0) errors.push(error(`unitMix.${i}.bedrooms`, 'Bedrooms must be a non-negative whole number.'));
    if (!Number.isInteger(row?.homes) || row.homes < 0) errors.push(error(`unitMix.${i}.homes`, 'Homes must be a non-negative whole number.'));
    if (!hasNumber(row?.areaM2) || row.areaM2 <= 0) errors.push(error(`unitMix.${i}.areaM2`, 'Dwelling area must be positive.'));
    if (!Number.isInteger(row?.habitableRooms) || row.habitableRooms < 1) errors.push(error(`unitMix.${i}.habitableRooms`, 'Habitable rooms must be a positive whole number.'));
  });
  if (Array.isArray(inputs?.unitMix) && !inputs.unitMix.some(row => row?.homes > 0)) errors.push(error('unitMix', 'The schedule must contain at least one home.'));
  if (Array.isArray(inputs?.unitMix)) {
    const homes = inputs.unitMix.reduce((sum, row) => sum + (Number.isInteger(row?.homes) && row.homes > 0 ? row.homes : 0), 0);
    const rooms = inputs.unitMix.reduce((sum, row) => sum + (Number.isInteger(row?.homes) && row.homes > 0 && Number.isInteger(row?.habitableRooms) && row.habitableRooms > 0 ? row.homes * row.habitableRooms : 0), 0);
    if (homes > 1000 || rooms > 10000) errors.push(error('unitMix', 'This indicative enumerator supports up to 1,000 homes and 10,000 habitable rooms.'));
  }
  const policy = inputs?.policy || {};
  if (!['unknown', 'private', 'public', 'industrial_reprovided', 'industrial_loss'].includes(policy.landType)) errors.push(error('policy.landType', 'Select a supported land classification.'));
  if (!['sale', 'build_to_rent'].includes(policy.schemeType)) errors.push(error('policy.schemeType', 'Select sale or build to rent.'));
  if (!hasNumber(policy.socialRentSharePct) || policy.socialRentSharePct < 0 || policy.socialRentSharePct > 100) errors.push(error('policy.socialRentSharePct', 'Social rent share must be between 0 and 100%.'));
  if (typeof policy.otherConditionsConfirmed !== 'boolean') errors.push(error('policy.otherConditionsConfirmed', 'State whether the other material route conditions were checked.'));
  if (policy.applicationDate !== null && policy.applicationDate !== undefined) {
    const date = policy.applicationDate;
    const valid = typeof date === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(date) && !Number.isNaN(Date.parse(`${date}T00:00:00Z`)) && new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) === date;
    if (!valid) errors.push(error('policy.applicationDate', 'Application date must be a real YYYY-MM-DD calendar date or unknown.'));
  }
  if (!hasNumber(inputs?.preferenceMinAffordablePct) || inputs.preferenceMinAffordablePct < 0 || inputs.preferenceMinAffordablePct > 100) errors.push(error('preferenceMinAffordablePct', 'Preference must be between 0 and 100%.'));
  for (const key of ASSUMPTION_KEYS) {
    const row = inputs?.assumptions?.[key];
    if (typeof row?.source !== 'string' || !row.source.trim() || row.source === 'User evidence required') errors.push(error(`assumptions.${key}.source`, `${row?.label || key}: identify the source or mark it as an illustrative user assumption.`));
    for (const band of ['low', 'base', 'high']) {
      const value = row?.[band];
      if (value === null || value === undefined || value === '') errors.push(error(`assumptions.${key}.${band}`, `${row?.label || key}: ${band} value is unknown.`));
      else if (!hasNumber(value) || value < 0 || (key.endsWith('PctOfBuild') && value > 100)) errors.push(error(`assumptions.${key}.${band}`, `${row?.label || key}: enter a non-negative finite value${key.endsWith('PctOfBuild') ? ' no greater than 100%' : ''}.`));
    }
    if (['low', 'base', 'high'].every(band => hasNumber(row?.[band])) && !(row.low <= row.base && row.base <= row.high)) errors.push(error(`assumptions.${key}`, `${row?.label || key}: low, base and high must be ordered.`));
  }
  return errors;
}

function geometry(site, env, mix) {
  const footprintM2 = site.areaM2 * env.coverageRatio;
  const geaM2 = footprintM2 * env.storeys;
  const giaM2 = geaM2 * env.giaEfficiency;
  const saleableCapacityM2 = giaM2 * env.saleableEfficiency;
  const scheduledAreaM2 = mix.reduce((sum, row) => sum + row.homes * row.areaM2, 0);
  return {
    siteAreaM2: site.areaM2, storeys: env.storeys, coverageRatio: env.coverageRatio,
    floorHeightM: env.floorHeightM, giaEfficiency: env.giaEfficiency, saleableEfficiency: env.saleableEfficiency,
    footprintM2: round(footprintM2), geaM2: round(geaM2),
    giaM2: round(giaM2), saleableCapacityM2: round(saleableCapacityM2),
    scheduledAreaM2: round(scheduledAreaM2), remainingSaleableM2: round(saleableCapacityM2 - scheduledAreaM2),
    heightM: round(env.storeys * env.floorHeightM),
  };
}

// Dynamic programming over exact integer room totals; each state keeps the most
// representative type mix. Thresholds are compared by integer cross multiplication.
function allocate(mix, numerator, denominator = 100) {
  const totalRooms = mix.reduce((sum, row) => sum + row.homes * row.habitableRooms, 0);
  let states = new Map([[0, { counts: [], penalty: 0 }]]);
  for (const row of mix) {
    const next = new Map();
    for (const [rooms, state] of states) {
      for (let count = 0; count <= row.homes; count++) {
        const newRooms = rooms + count * row.habitableRooms;
        const penalty = state.penalty + Math.abs(count - row.homes * numerator / denominator);
        const current = next.get(newRooms);
        if (!current || penalty < current.penalty - 1e-9) next.set(newRooms, { counts: [...state.counts, count], penalty });
      }
    }
    states = next;
  }
  const sums = [...states.keys()].sort((a, b) => a - b);
  const selectedRooms = sums.find(rooms => rooms * denominator >= numerator * totalRooms) ?? sums.at(-1);
  return { rooms: selectedRooms, counts: states.get(selectedRooms).counts };
}

function policyRoute(id, scenario, policy, site) {
  const source = id === 'temporary2026' ? POLICY_SOURCES.temporary2026 : POLICY_SOURCES.h5;
  const roomPct = scenario.affordableHabitableRoomsPct;
  const reasons = [];
  const land = policy.landType;
  let thresholdPct = null;
  if (id === 'h5FastTrack') thresholdPct = land === 'public' || land === 'industrial_loss' ? 50 : land === 'unknown' ? null : 35;
  if (id === 'temporary2026') thresholdPct = land === 'public' || land === 'industrial_loss' ? 35 : land === 'unknown' ? null : 20;
  if (id === 'h5ViabilityTested') {
    return { status: 'requires review', reasons: ['A viability-tested H5 application needs a scheme-specific viability assessment and borough review.'], thresholdPct: null, sourceUrl: source.url, policyVersion: source.version };
  }
  let fail = false;
  let review = false;
  if (thresholdPct === null) { review = true; reasons.push('Land classification is unknown; the applicable room threshold cannot be confirmed.'); }
  else if (scenario.affordableHabitableRooms * 100 < thresholdPct * scenario.totalHabitableRooms) { fail = true; reasons.push(`Exact affordable habitable-room share is below the ${thresholdPct}% route threshold.`); }
  if (id === 'h5FastTrack') {
    if (scenario.affordableHabitableRooms > 0 && (scenario.socialHabitableRooms * 100 < 30 * scenario.affordableHabitableRooms || scenario.intermediateHabitableRooms * 100 < 30 * scenario.affordableHabitableRooms)) {
      fail = true; reasons.push('The affordable room mix does not meet the H5 minimum 30% low-cost rent and 30% intermediate tenure shares.');
    }
    if (policy.schemeType === 'build_to_rent') { review = true; reasons.push('Build to rent tenure rules need a separate H5 review.'); }
  } else {
    if (policy.schemeType === 'build_to_rent') { fail = true; reasons.push('This temporary route is not supported for build to rent in this concept study.'); }
    if (policy.applicationDate == null) { review = true; reasons.push('The application date is unknown.'); }
    else if (policy.applicationDate < '2026-03-25') { review = true; reasons.push('Application date predates publication of the adopted March 2026 guidance; applicability to a pending case needs review.'); }
    else if (policy.applicationDate > '2028-03-31') { fail = true; reasons.push('Application date is after the 31 March 2028 temporary-route deadline.'); }
    if (scenario.affordableHabitableRooms > 0 && scenario.socialHabitableRooms * 100 < 60 * scenario.affordableHabitableRooms) { fail = true; reasons.push('Social rent is below 60% of affordable habitable rooms.'); }
    reasons.push('Grant is excluded from the appraisal; any grant-funded allocation requires separate programme and nil-grant evidence.');
  }
  if (!policy.otherConditionsConfirmed) { review = true; reasons.push('Other material site, borough and guidance conditions have not been confirmed.'); }
  if (scenario.homes < 10) { review = true; reasons.push('The concept has fewer than 10 homes, outside the core major-residential comparison scope.'); }
  if (!Array.isArray(site?.unknowns)) { review = true; reasons.push('The site snapshot has no explicit list of unresolved facts.'); }
  else if (site.unknowns.length) { review = true; reasons.push('The site snapshot has unresolved material facts: ' + site.unknowns.join(' ')); }
  const routeEvidence = site?.routeEvidence?.[id];
  if (typeof routeEvidence?.sourceUrl !== 'string' || !/^https?:\/\//.test(routeEvidence.sourceUrl)) {
    review = true; reasons.push('A source-linked check of this route’s material site conditions is missing.');
  }
  for (const condition of ROUTE_CHECKS[id]) {
    const label = ROUTE_CHECK_LABELS[condition];
    if (routeEvidence?.[condition] === false) { fail = true; reasons.push(`The ${label} condition is not met.`); }
    else if (routeEvidence?.[condition] !== true) { review = true; reasons.push(`The ${label} condition is unverified.`); }
  }
  if (!fail && !review) reasons.unshift('Meets the stated numerical and supplied route conditions; planning decision remains subject to review.');
  return { status: fail ? 'fails stated condition' : review ? 'requires review' : 'likely eligible', reasons, thresholdPct, sourceUrl: source.url, policyVersion: source.version };
}

function financeFor(scenario, assumptions, band) {
  const values = Object.fromEntries(ASSUMPTION_KEYS.map(key => [key, assumptions?.[key]?.[band]]));
  if (ASSUMPTION_KEYS.some(key => {
    const row = assumptions?.[key];
    return !hasNumber(values[key]) || values[key] < 0 || (key.endsWith('PctOfBuild') && values[key] > 100) ||
      (['low', 'base', 'high'].every(k => hasNumber(row?.[k])) && (row.low > row.base || row.base > row.high)) ||
      typeof row?.source !== 'string' || !row.source.trim() || row.source === 'User evidence required';
  })) {
    return Object.fromEntries(['gdv','marketReceipts','affordableReceipts','socialReceipts','intermediateReceipts','otherReceipts','grantReceipts','buildCost','abnormalCosts','fees','contingency','financeCosts','cilCosts','s106Costs','landCost','totalCost','developmentSurplus','profitOnCostPct','residualLandValue','breakEvenMarketValuePerM2','targetReturn'].map(key => [key, null]));
  }
  const g = scenario.geometry;
  const marketReceipts = scenario.tenure.marketAreaM2 * values.marketValuePerM2;
  const socialReceipts = scenario.tenure.socialAreaM2 * values.socialTransferPerM2;
  const intermediateReceipts = scenario.tenure.intermediateAreaM2 * values.intermediateTransferPerM2;
  const affordableReceipts = socialReceipts + intermediateReceipts;
  const grantReceipts = 0; // Never impute a grant or count it inside a transfer rate.
  const otherReceipts = values.otherReceipts;
  const gdv = marketReceipts + affordableReceipts + grantReceipts + otherReceipts;
  const buildCost = g.giaM2 * values.buildCostPerGiaM2;
  const fees = buildCost * values.feesPctOfBuild / 100;
  const contingency = buildCost * values.contingencyPctOfBuild / 100;
  const totalCost = buildCost + values.abnormalCosts + fees + contingency + values.financeCosts + values.cilCosts + values.s106Costs + values.landCost;
  const developmentSurplus = gdv - totalCost;
  const residualLandValue = gdv - (totalCost - values.landCost) - values.targetReturn;
  const breakEvenMarketValuePerM2 = scenario.tenure.marketAreaM2 === 0 ? null : (totalCost + values.targetReturn - affordableReceipts - grantReceipts - otherReceipts) / scenario.tenure.marketAreaM2;
  return {
    gdv: round(gdv), marketReceipts: round(marketReceipts), affordableReceipts: round(affordableReceipts),
    socialReceipts: round(socialReceipts), intermediateReceipts: round(intermediateReceipts), otherReceipts: round(otherReceipts), grantReceipts,
    buildCost: round(buildCost), abnormalCosts: values.abnormalCosts, fees: round(fees), contingency: round(contingency),
    financeCosts: values.financeCosts, cilCosts: values.cilCosts, s106Costs: values.s106Costs, landCost: values.landCost,
    totalCost: round(totalCost), developmentSurplus: round(developmentSurplus),
    profitOnCostPct: totalCost === 0 ? null : round(developmentSurplus / totalCost * 100),
    residualLandValue: round(residualLandValue), breakEvenMarketValuePerM2: round(breakEvenMarketValuePerM2),
    targetReturn: values.targetReturn,
  };
}

function scenarioFor(targetPct, mix, g, inputs, site) {
  const totalHabitableRooms = mix.reduce((sum, row) => sum + row.homes * row.habitableRooms, 0);
  const totalHomes = mix.reduce((sum, row) => sum + row.homes, 0);
  const selected = allocate(mix, targetPct);
  const affordableMix = mix.map((row, i) => ({ ...row, affordableHomes: selected.counts[i], marketHomes: row.homes - selected.counts[i] }));
  const socialSelection = allocate(affordableMix.map(row => ({ ...row, homes: row.affordableHomes })), inputs.policy.socialRentSharePct);
  const allocation = affordableMix.map((row, i) => ({ ...row, socialHomes: socialSelection.counts[i], intermediateHomes: row.affordableHomes - socialSelection.counts[i] }));
  const affordableHomes = allocation.reduce((sum, row) => sum + row.affordableHomes, 0);
  const socialHomes = allocation.reduce((sum, row) => sum + row.socialHomes, 0);
  const socialHabitableRooms = allocation.reduce((sum, row) => sum + row.socialHomes * row.habitableRooms, 0);
  const affordableAreaM2 = allocation.reduce((sum, row) => sum + row.affordableHomes * row.areaM2, 0);
  const socialAreaM2 = allocation.reduce((sum, row) => sum + row.socialHomes * row.areaM2, 0);
  const scenario = {
    id: `rooms-${targetPct}`, label: `${targetPct}% room target`, badges: [],
    schemeType: inputs.policy.schemeType,
    targetAffordablePct: targetPct, homes: totalHomes, affordableHomes, marketHomes: totalHomes - affordableHomes,
    totalHabitableRooms, affordableHabitableRooms: selected.rooms, affordableHabitableRoomsPct: round(selected.rooms / totalHabitableRooms * 100),
    socialHomes, intermediateHomes: affordableHomes - socialHomes, socialHabitableRooms, intermediateHabitableRooms: selected.rooms - socialHabitableRooms,
    geometry: g,
    tenure: { marketAreaM2: round(g.scheduledAreaM2 - affordableAreaM2), affordableAreaM2: round(affordableAreaM2), socialAreaM2: round(socialAreaM2), intermediateAreaM2: round(affordableAreaM2 - socialAreaM2) },
    allocation,
  };
  scenario.policy = {
    h5FastTrack: policyRoute('h5FastTrack', scenario, inputs.policy, site),
    h5ViabilityTested: policyRoute('h5ViabilityTested', scenario, inputs.policy, site),
    temporary2026: policyRoute('temporary2026', scenario, inputs.policy, site),
  };
  scenario.finance = Object.fromEntries(['low', 'base', 'high'].map(band => [band, financeFor(scenario, inputs.assumptions, band)]));
  return scenario;
}

function sensitivityFor(scenario, assumptions) {
  if (!scenario || scenario.finance.base.developmentSurplus === null) return [];
  return ASSUMPTION_KEYS.filter(key => hasNumber(assumptions[key]?.low) && hasNumber(assumptions[key]?.high)).map(key => {
    const lowInputs = structuredClone(assumptions);
    const highInputs = structuredClone(assumptions);
    lowInputs[key].base = assumptions[key].low;
    highInputs[key].base = assumptions[key].high;
    const lowSurplus = financeFor(scenario, lowInputs, 'base').developmentSurplus;
    const highSurplus = financeFor(scenario, highInputs, 'base').developmentSurplus;
    return { key, label: assumptions[key].label, source: assumptions[key].source, lowSurplus, baseSurplus: scenario.finance.base.developmentSurplus, highSurplus, swing: round(Math.abs(highSurplus - lowSurplus)) };
  }).sort((a, b) => b.swing - a.swing);
}

export function buildStudy(site, inputs = DEFAULT_INPUTS) {
  const errors = validate(site, inputs);
  const formulae = {
    geometry: 'footprint = site area × coverage; GEA = footprint × storeys; GIA = GEA × GIA efficiency; saleable capacity = GIA × saleable efficiency; scheduled dwelling area must fit capacity',
    rooms: 'affordable room share = integer affordable habitable rooms ÷ integer total habitable rooms; no rounding for route thresholds',
    gdv: 'market area × market £/m² + social area × social transfer £/m² + intermediate area × intermediate transfer £/m² + other receipts; grant excluded',
    totalCost: 'GIA × build £/m² + abnormal + build × fees% + build × contingency% + finance + CIL + S106 + land',
    developmentSurplus: 'GDV − total cost including land',
    profitOnCostPct: 'development surplus ÷ total cost including land × 100',
    residualLandValue: 'GDV − costs excluding land − fixed target return',
    breakEvenMarketValuePerM2: '(total cost including land + fixed target return − affordable receipts − other receipts) ÷ market saleable area; undefined if market area is zero',
    irr: 'Unavailable: no dated cash-flow schedule was supplied.',
  };
  const structuralErrors = errors.filter(item => !item.field.startsWith('assumptions.'));
  if (structuralErrors.length) return { scenarios: [], balancedId: null, errors, sensitivity: [], formulae, policySources: POLICY_SOURCES, assumptions: inputs?.assumptions ?? {}, geometry: null };
  const g = geometry(site, inputs.envelope, inputs.unitMix);
  if (g.scheduledAreaM2 > g.saleableCapacityM2 + 1e-8) {
    errors.push(error('unitMix', `Scheduled dwelling area ${g.scheduledAreaM2} m² exceeds ${g.saleableCapacityM2} m² saleable capacity. Increase a sourced envelope or reduce the dwelling schedule.`));
    return { scenarios: [], balancedId: null, errors, sensitivity: [], formulae, policySources: POLICY_SOURCES, assumptions: inputs.assumptions, geometry: g };
  }
  const scenarios = [20, 35, 50].map(target => scenarioFor(target, inputs.unitMix, g, inputs, site));
  const knownFinance = scenarios.every(s => s.finance.base.developmentSurplus !== null);
  const higherReturn = knownFinance ? [...scenarios].sort((a, b) => b.finance.base.developmentSurplus - a.finance.base.developmentSurplus || a.targetAffordablePct - b.targetAffordablePct)[0] : null;
  const moreAffordable = [...scenarios].sort((a, b) => b.affordableHabitableRooms - a.affordableHabitableRooms || b.targetAffordablePct - a.targetAffordablePct)[0];
  const qualifying = scenarios.filter(s => s.affordableHabitableRooms * 100 >= inputs.preferenceMinAffordablePct * s.totalHabitableRooms);
  const balanced = knownFinance && qualifying.length ? [...qualifying].sort((a, b) => b.finance.base.developmentSurplus - a.finance.base.developmentSurplus || a.affordableHabitableRooms - b.affordableHabitableRooms)[0] : null;
  const frontierIds = knownFinance ? scenarios.filter(s => !scenarios.some(other => other !== s && other.affordableHabitableRooms >= s.affordableHabitableRooms && other.finance.base.developmentSurplus >= s.finance.base.developmentSurplus && (other.affordableHabitableRooms > s.affordableHabitableRooms || other.finance.base.developmentSurplus > s.finance.base.developmentSurplus))).map(s => s.id) : [];
  if (higherReturn) higherReturn.badges.push('Higher return');
  moreAffordable.badges.push('More affordable rooms');
  if (balanced) balanced.badges.push('Balanced within supplied assumptions');
  for (const scenario of scenarios) scenario.nondominated = knownFinance ? frontierIds.includes(scenario.id) : null;
  return { scenarios, balancedId: balanced?.id ?? null, higherReturnId: higherReturn?.id ?? null, moreAffordableId: moreAffordable.id, frontierIds, errors, sensitivity: sensitivityFor(balanced, inputs.assumptions), formulae, policySources: POLICY_SOURCES, assumptions: inputs.assumptions, geometry: g, grantNote: 'Grant excluded: no verified eligible programme, tenure allocation and receipt schedule supplied.' };
}

import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_INPUTS, buildStudy } from '../dist/civisopt/engine.js';

const site = {
  areaM2: 1000,
  unknowns: [],
  routeEvidence: {
    h5FastTrack: { sourceUrl: 'https://example.org/verified-h5', noPublicSubsidy: true, boroughPolicyChecked: true, siteConstraintsChecked: true, otherObligationsChecked: true },
    temporary2026: { sourceUrl: 'https://example.org/verified-temporary', noExcludedLand: true, noAffordableDemolition: true, supportedResidentialUse: true, boroughPolicyChecked: true, siteConstraintsChecked: true, reviewMechanismChecked: true },
  },
};

function inputs() {
  const result = structuredClone(DEFAULT_INPUTS);
  result.envelope = { storeys: 2, coverageRatio: 0.5, floorHeightM: 3, giaEfficiency: 1, saleableEfficiency: 1 };
  result.unitMix = [{ bedrooms: 1, homes: 10, areaM2: 50, habitableRooms: 2 }];
  const values = {
    marketValuePerM2: 1000,
    socialTransferPerM2: 500,
    intermediateTransferPerM2: 800,
    buildCostPerGiaM2: 100,
    abnormalCosts: 10000,
    feesPctOfBuild: 10,
    contingencyPctOfBuild: 5,
    financeCosts: 2000,
    cilCosts: 3000,
    s106Costs: 4000,
    landCost: 50000,
    otherReceipts: 0,
    targetReturn: 20000,
  };
  for (const [key, value] of Object.entries(values)) Object.assign(result.assumptions[key], { low: value, base: value, high: value, source: 'Hand-calculation fixture' });
  result.policy = { landType: 'private', applicationDate: '2026-09-26', schemeType: 'sale', socialRentSharePct: 60, otherConditionsConfirmed: true };
  return result;
}

test('independent room, area and cost row matches hand arithmetic', () => {
  const study = buildStudy(site, inputs());
  assert.deepEqual(study.errors, []);
  const s = study.scenarios[1]; // 35% target: four two-room homes = 40% exact.
  assert.equal(s.homes, 10);
  assert.equal(s.affordableHomes, 4);
  assert.equal(s.affordableHabitableRooms, 8);
  assert.equal(s.totalHabitableRooms, 20);
  assert.equal(s.geometry.giaM2, 1000);
  assert.equal(s.geometry.saleableCapacityM2, 1000);
  assert.equal(s.geometry.scheduledAreaM2, 500);
  assert.deepEqual(s.tenure, { marketAreaM2: 300, affordableAreaM2: 200, socialAreaM2: 150, intermediateAreaM2: 50 });
  assert.equal(s.finance.base.marketReceipts, 300000);
  assert.equal(s.finance.base.socialReceipts, 75000);
  assert.equal(s.finance.base.intermediateReceipts, 40000);
  assert.equal(s.finance.base.gdv, 415000);
  assert.equal(s.finance.base.buildCost, 100000);
  assert.equal(s.finance.base.fees, 10000);
  assert.equal(s.finance.base.contingency, 5000);
  assert.equal(s.finance.base.totalCost, 184000);
  assert.equal(s.finance.base.developmentSurplus, 231000);
  assert.equal(s.finance.base.profitOnCostPct, 125.543478);
  assert.equal(s.finance.base.residualLandValue, 261000);
  assert.equal(s.finance.base.breakEvenMarketValuePerM2, 296.666667);
  assert.equal(s.finance.base.grantReceipts, 0);
  assert.equal(s.policy.h5ViabilityTested.status, 'requires review');
});

test('low/base/high ranges, costs, receipts and geometry changes all recompute', () => {
  const x = inputs();
  x.assumptions.marketValuePerM2.low = 900;
  x.assumptions.marketValuePerM2.high = 1100;
  x.assumptions.buildCostPerGiaM2.low = 90;
  x.assumptions.buildCostPerGiaM2.high = 110;
  const first = buildStudy(site, x);
  const s = first.scenarios[1];
  assert.equal(s.finance.low.marketReceipts, 270000);
  assert.equal(s.finance.high.marketReceipts, 330000);
  assert.equal(s.finance.low.buildCost, 90000);
  assert.equal(s.finance.high.buildCost, 110000);
  assert.equal(s.finance.low.developmentSurplus, 212500);
  assert.equal(s.finance.high.developmentSurplus, 249500);
  assert.ok(first.sensitivity.some(row => row.key === 'marketValuePerM2' && row.swing === 60000));
  x.envelope.storeys = 3;
  const second = buildStudy(site, x).scenarios[1];
  assert.equal(second.geometry.giaM2, 1500);
  assert.equal(second.geometry.heightM, 9);
  assert.equal(second.finance.base.buildCost, 150000);
  assert.equal(second.finance.base.developmentSurplus, 173500);
});

test('whole-home allocation respects exact room denominator and can differ from unit share', () => {
  const x = inputs();
  x.unitMix = [
    { bedrooms: 1, homes: 6, areaM2: 50, habitableRooms: 2 },
    { bedrooms: 3, homes: 4, areaM2: 90, habitableRooms: 4 },
  ];
  const s = buildStudy(site, x).scenarios[0];
  assert.equal(s.totalHabitableRooms, 28);
  assert.ok(Number.isInteger(s.affordableHabitableRooms));
  assert.ok(s.affordableHabitableRooms * 100 >= 20 * s.totalHabitableRooms);
  assert.notEqual(s.affordableHomes / s.homes * 100, s.affordableHabitableRoomsPct);
  for (const row of s.allocation) {
    assert.equal(row.affordableHomes + row.marketHomes, row.homes);
    assert.equal(row.socialHomes + row.intermediateHomes, row.affordableHomes);
    assert.ok(Number.isInteger(row.affordableHomes));
  }
});

test('policy uses exact room threshold and distinguishes H5, temporary scope and unresolved facts', () => {
  const x = inputs();
  const study = buildStudy(site, x);
  const low = study.scenarios[0];
  assert.equal(low.affordableHabitableRoomsPct, 20);
  assert.equal(low.policy.h5FastTrack.status, 'fails stated condition');
  assert.equal(low.policy.temporary2026.status, 'likely eligible');
  assert.equal(study.scenarios[2].policy.h5FastTrack.status, 'likely eligible');
  const publicStudy = buildStudy(site, { ...x, policy: { ...x.policy, landType: 'public' } });
  assert.equal(publicStudy.scenarios[0].policy.temporary2026.thresholdPct, 35);
  assert.equal(publicStudy.scenarios[0].policy.temporary2026.status, 'fails stated condition');
  assert.equal(publicStudy.scenarios[2].policy.h5FastTrack.thresholdPct, 50);
  assert.equal(publicStudy.scenarios[2].policy.h5FastTrack.status, 'likely eligible');
  assert.equal(buildStudy({ ...site, unknowns: ['Check local plan.'] }, x).scenarios[2].policy.h5FastTrack.status, 'requires review');
  assert.equal(buildStudy({ areaM2: 1000, unknowns: [] }, x).scenarios[2].policy.h5FastTrack.status, 'requires review');
  assert.equal(buildStudy(site, { ...x, policy: { ...x.policy, landType: 'unknown' } }).scenarios[2].policy.h5FastTrack.status, 'requires review');
  assert.equal(buildStudy(site, { ...x, policy: { ...x.policy, otherConditionsConfirmed: false } }).scenarios[2].policy.h5FastTrack.status, 'requires review');
});

test('temporary route date, tenure and build-to-rent conditions stay distinct', () => {
  const x = inputs();
  const route = (changes) => buildStudy(site, { ...x, policy: { ...x.policy, ...changes } }).scenarios[0].policy.temporary2026.status;
  assert.equal(route({ applicationDate: '2028-03-31' }), 'likely eligible');
  assert.equal(route({ applicationDate: '2028-04-01' }), 'fails stated condition');
  assert.equal(route({ applicationDate: '2026-03-24' }), 'requires review');
  assert.equal(route({ applicationDate: null }), 'requires review');
  assert.equal(route({ schemeType: 'build_to_rent' }), 'fails stated condition');
  assert.equal(route({ socialRentSharePct: 0 }), 'fails stated condition');
  assert.equal(route({ landType: 'industrial_reprovided' }), 'likely eligible');
  assert.equal(route({ landType: 'industrial_loss' }), 'fails stated condition');
});

test('a displayed 50% after whole-percent rounding remains below the exact public-land H5 threshold', () => {
  const x = inputs();
  x.unitMix = [
    { bedrooms: 1, homes: 1, areaM2: 50, habitableRooms: 50 },
    { bedrooms: 2, homes: 1, areaM2: 50, habitableRooms: 51 },
  ];
  x.policy.landType = 'public';
  const s = buildStudy(site, x).scenarios[1];
  assert.equal(s.affordableHabitableRooms, 50);
  assert.equal(s.totalHabitableRooms, 101);
  assert.equal(Math.round(s.affordableHabitableRoomsPct), 50);
  assert.equal(s.policy.h5FastTrack.status, 'fails stated condition');
});

test('missing values stay unknown while zero is valid; no market area has undefined break-even', () => {
  const blank = buildStudy({ ...site, areaM2: 4000 }, DEFAULT_INPUTS);
  assert.equal(blank.scenarios[0].finance.base.developmentSurplus, null);
  assert.equal(blank.balancedId, null);
  const x = inputs();
  x.assumptions.landCost.base = null;
  let result = buildStudy(site, x);
  assert.ok(result.errors.some(e => e.field === 'assumptions.landCost.base'));
  assert.equal(result.scenarios[0].finance.base.developmentSurplus, null);
  assert.equal(result.balancedId, null);
  x.assumptions.landCost.base = 0;
  x.assumptions.landCost.low = 0;
  result = buildStudy(site, x);
  assert.equal(result.scenarios[0].finance.base.landCost, 0);
  assert.notEqual(result.scenarios[0].finance.base.developmentSurplus, null);
  x.unitMix = [{ bedrooms: 1, homes: 1, areaM2: 50, habitableRooms: 2 }];
  const allAffordable = buildStudy(site, x).scenarios[0];
  assert.equal(allAffordable.tenure.marketAreaM2, 0);
  assert.equal(allAffordable.finance.base.breakEvenMarketValuePerM2, null);
  assert.equal(allAffordable.policy.temporary2026.status, 'requires review');
});

test('invalid ranges, dates, capacity and large schedules produce explicit errors', () => {
  const x = inputs();
  x.assumptions.landCost.high = -1;
  x.assumptions.marketValuePerM2.low = 1100;
  x.assumptions.marketValuePerM2.high = 900;
  x.assumptions.s106Costs.source = '';
  x.policy.applicationDate = '2026-02-30';
  const bad = buildStudy(site, x);
  assert.ok(bad.errors.some(e => e.field === 'assumptions.landCost.high'));
  assert.ok(bad.errors.some(e => e.field === 'assumptions.marketValuePerM2'));
  assert.ok(bad.errors.some(e => e.field === 'assumptions.s106Costs.source'));
  assert.ok(bad.errors.some(e => e.field === 'policy.applicationDate'));
  assert.equal(bad.scenarios.length, 0);
  x.policy.applicationDate = '2026-09-26';
  x.unitMix[0].homes = 21;
  const oversize = buildStudy(site, x);
  assert.equal(oversize.scenarios.length, 0);
  assert.ok(oversize.errors.some(e => e.field === 'unitMix' && e.message.includes('exceeds')));
  x.unitMix[0].homes = 1001;
  const tooLarge = buildStudy(site, x);
  assert.ok(tooLarge.errors.some(e => e.field === 'unitMix' && e.message.includes('1,000 homes')));
});

test('invalid provenance or an inverted band blocks financial conclusions', () => {
  const x = inputs();
  x.assumptions.landCost.source = 'User evidence required';
  let result = buildStudy(site, x);
  assert.equal(result.scenarios[0].finance.base.developmentSurplus, null);
  assert.equal(result.balancedId, null);
  x.assumptions.landCost.source = 'Hand-calculation fixture';
  x.assumptions.marketValuePerM2.low = 1200;
  result = buildStudy(site, x);
  assert.equal(result.scenarios[0].finance.base.developmentSurplus, null);
  assert.equal(result.balancedId, null);
});

test('preferred scenario follows actual surplus, requirement and Pareto frontier', () => {
  const x = inputs();
  let study = buildStudy(site, x);
  assert.equal(study.higherReturnId, 'rooms-20');
  assert.equal(study.balancedId, 'rooms-35');
  assert.ok(study.frontierIds.length > 1);
  x.assumptions.socialTransferPerM2.low = 1500;
  x.assumptions.socialTransferPerM2.base = 1500;
  x.assumptions.socialTransferPerM2.high = 1500;
  x.assumptions.intermediateTransferPerM2.low = 1500;
  x.assumptions.intermediateTransferPerM2.base = 1500;
  x.assumptions.intermediateTransferPerM2.high = 1500;
  study = buildStudy(site, x);
  assert.equal(study.higherReturnId, 'rooms-50');
  assert.equal(study.balancedId, 'rooms-50');
  assert.deepEqual(study.frontierIds, ['rooms-50']);
  x.preferenceMinAffordablePct = 100;
  study = buildStudy(site, x);
  assert.equal(study.balancedId, null);
});

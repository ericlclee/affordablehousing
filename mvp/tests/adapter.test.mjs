import test from 'node:test';
import assert from 'node:assert/strict';
import { canonicalModelInput, screeningAvailability } from '../dist/civisopt/adapter.js';

test('canonical model input maps engine geometry and its room schedule', () => {
  const scenario = {
    targetAffordablePct: 35,
    homes: 4,
    totalHabitableRooms: 13,
    affordableHabitableRooms: 5,
    geometry: { storeys: 4, coverageRatio: 0.4, heightM: 12, siteAreaM2: 2500, giaM2: 3400 },
    allocation: [
      { bedrooms: 0, homes: 1, habitableRooms: 1 },
      { bedrooms: 1, homes: 1, habitableRooms: 2 },
      { bedrooms: 2, homes: 1, habitableRooms: 3 },
      { bedrooms: 3, homes: 1, habitableRooms: 4 },
      { bedrooms: 4, homes: 0, habitableRooms: 5 },
    ],
    socialHabitableRooms: 2,
  };

  const input = canonicalModelInput(scenario);
  assert.equal(input.storeys, 4);
  assert.equal(input.height_m, 12);
  assert.equal(input.site_area_m2, 2500);
  assert.equal(input.coverage_ratio, 0.4);
  assert.equal(input.gia_m2, 3400);
  assert.equal(input.density_homes_per_ha, 16);
  assert.deepEqual(input.unit_mix_pct_by_bedrooms, { studio: 25, '1b': 25, '2b': 25, '3b_plus': 25 });
  assert.equal(input.affordable_habitable_rooms_pct, 5 / 13 * 100);
  assert.equal(input.social_rent_share_of_affordable_pct, 40);
  assert.equal(input.development_type, null);
  assert.equal(input.scheme_type, null);
});

test('unknown, false and zero remain distinct, and missing SiteFacts flags stay unknown', () => {
  const input = canonicalModelInput({
    homes: 0,
    totalHabitableRooms: 0,
    affordableHabitableRooms: 0,
    socialHabitableRooms: 0,
    geometry: { storeys: 0, siteAreaM2: 0, heightM: 0, giaM2: 0, coverageRatio: 0 },
    demolition: false,
    amenities: { gym: false },
    carSpaces: 0,
    allocation: [{ bedrooms: 1, homes: 0 }],
  });
  assert.equal(input.homes, 0);
  assert.equal(input.storeys, 0);
  assert.equal(input.height_m, 0);
  assert.equal(input.coverage_ratio, 0);
  assert.equal(input.gia_m2, 0);
  assert.equal(input.density_homes_per_ha, null);
  assert.equal(input.unit_mix_pct_by_bedrooms, null);
  assert.equal(input.affordable_habitable_rooms_pct, null);
  assert.equal(input.social_rent_share_of_affordable_pct, null);
  assert.equal(input.demolition, false);
  assert.equal(input.amenities.gym, false);
  assert.equal(input.amenities.pool, null);
  assert.equal(input.car_spaces, 0);
  assert.equal(input.conservation_area, null);
  assert.equal(input.borough, null);
  assert.equal(input.site_facts_version, null);
  assert.equal(input.feature_states.homes, 'known');
  assert.equal(input.feature_states.demolition, 'known');
  assert.equal(input.feature_states['amenities.gym'], 'known');
  assert.equal(input.feature_states['amenities.pool'], 'unknown');
  assert.equal(input.feature_states.conservation_area, 'unknown');
});

test('only versioned SiteFacts supply site flags; explicit false is retained', () => {
  const facts = {
    version: 'site-facts/1.0.0', borough: 'Croydon', conservationArea: false,
    article4Area: true, ptal2023: 0, deprivationDecile: 3,
  };
  const input = canonicalModelInput({}, facts);
  assert.equal(input.site_facts_version, 'site-facts/1.0.0');
  assert.equal(input.borough, 'Croydon');
  assert.equal(input.conservation_area, false);
  assert.equal(input.article_4_area, true);
  assert.equal(input.ptal_2023, 0);
  assert.equal(input.deprivation_decile, 3);
  assert.equal(input.listed_building_on_site, null);
  assert.equal(input.feature_states.conservation_area, 'known');
  assert.equal(input.feature_states.ptal_2023, 'known');
});

test('explicit not_applicable stays distinct from absent or null inputs', () => {
  const input = canonicalModelInput({
    homes: null,
    geometry: { storeys: 'not_applicable', heightM: { state: 'not_applicable' } },
    allocation: [{ bedrooms: 'not_applicable', homes: 2 }],
    totalHabitableRooms: null,
    affordableHabitableRooms: 'not_applicable',
    demolition: false,
  }, {
    conservationArea: 'not_applicable',
    ptal2023: null,
  });

  assert.equal(input.storeys, null);
  assert.equal(input.height_m, null);
  assert.equal(input.unit_mix_pct_by_bedrooms, null);
  assert.equal(input.affordable_habitable_rooms_pct, null);
  assert.equal(input.conservation_area, null);
  assert.equal(input.ptal_2023, null);
  assert.equal(input.feature_states.storeys, 'not_applicable');
  assert.equal(input.feature_states.height_m, 'not_applicable');
  assert.equal(input.feature_states.unit_mix_pct_by_bedrooms, 'not_applicable');
  assert.equal(input.feature_states.affordable_habitable_rooms_pct, 'not_applicable');
  assert.equal(input.feature_states.conservation_area, 'not_applicable');
  assert.equal(input.feature_states.ptal_2023, 'unknown');
  assert.equal(input.feature_states.homes, 'unknown');
  assert.equal(input.feature_states.demolition, 'known');
});

test('post-submission fields and policy/finance outputs are not passed to the model', () => {
  const scenario = {
    homes: 4,
    totalHabitableRooms: 10,
    affordableHabitableRooms: 4,
    socialHabitableRooms: 2,
    geometry: { siteAreaM2: 1000, storeys: 2, heightM: 6, giaM2: 800, coverageRatio: 0.5 },
    allocation: [{ bedrooms: 2, homes: 4 }],
    policy: { h5FastTrack: { status: 'likely eligible' } },
    finance: { base: { s106Costs: 12000 } },
    comments: ['post-submission comment'], decisionDate: '2025-01-01',
    decidedBy: 'borough', finalS106Terms: 'post-submission terms',
  };
  const before = structuredClone(scenario);
  const input = canonicalModelInput(scenario);
  assert.deepEqual(scenario, before);
  assert.equal(input.s106Costs, undefined);
  assert.equal(input.policy, undefined);
  assert.equal(input.comments, undefined);
  assert.equal(input.decisionDate, undefined);
  assert.equal(input.decidedBy, undefined);
  assert.equal(input.finalS106Terms, undefined);
  assert.equal(scenario.finance.base.s106Costs, 12000);
});

test('screening stays unavailable even when caller supplies truthy integration-looking data', () => {
  const result = screeningAvailability({ artifact: { version: '1', validated: true }, authorized: true });
  assert.equal(result.status, 'unavailable');
  assert.equal(result.label, 'Approval screening unavailable');
  assert.ok(result.reasons.length > 0);
  assert.ok(result.reasons.every(reason => typeof reason === 'string' && reason.trim()));
  assert.deepEqual(result, screeningAvailability());

});

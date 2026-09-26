import test from 'node:test';
import assert from 'node:assert/strict';
import { readStudySnapshot } from '../dist/civisopt/study-storage.js';
import { SITE, SOURCE_RECORDS } from '../dist/civisopt/snapshot.js';
import { DEFAULT_INPUTS, ENGINE_VERSION, POLICY_SOURCES, buildStudy } from '../dist/civisopt/engine.js';

function saved() {
  const inputs = structuredClone(DEFAULT_INPUTS);
  for (const row of Object.values(inputs.assumptions)) {
    Object.assign(row, { low: 1, base: 2, high: 3, source: 'Illustrative storage test' });
  }
  return { schema: 'civisopt-study-v1', engineVersion: ENGINE_VERSION,
    policySources: POLICY_SOURCES, site: SITE, sourceRecords: SOURCE_RECORDS,
    inputs, selectedScenarioId: 'rooms-35', result: { madeUpProfit: 999999999 } };
}

test('saved inputs reproduce the result and cannot inject cached results', () => {
  const snapshot = saved();
  const restored = readStudySnapshot(JSON.stringify(snapshot));
  assert.deepEqual(restored.inputs, snapshot.inputs);
  assert.equal(restored.selectedScenarioId, 'rooms-35');
  assert.equal(Object.hasOwn(restored, 'result'), false);
  assert.deepEqual(buildStudy(SITE, restored.inputs), buildStudy(SITE, snapshot.inputs));
});

test('incompatible engine, policy, geometry or source versions are rejected', () => {
  for (const field of ['engineVersion', 'policySources', 'site', 'sourceRecords', 'schema']) {
    const data = saved();
    data[field] = 'different';
    assert.throws(() => readStudySnapshot(JSON.stringify(data)));
  }
});

test('imports preserve unknown values, reject impossible schedules and cannot clear policy conditions', () => {
  const data = saved();
  data.inputs.assumptions.landCost.base = null;
  data.inputs.assumptions.financeCosts.source = '';
  data.inputs.policy.otherConditionsConfirmed = true;
  const restored = readStudySnapshot(JSON.stringify(data));
  assert.equal(restored.inputs.assumptions.landCost.base, null);
  assert.equal(restored.inputs.assumptions.financeCosts.source, '');
  assert.equal(restored.inputs.policy.otherConditionsConfirmed, false);
  const study = buildStudy(SITE, restored.inputs);
  assert.equal(study.balancedId, null);
  data.inputs.unitMix[0].homes = 1000000;
  assert.throws(() => readStudySnapshot(JSON.stringify(data)), /1,000 homes/);
});

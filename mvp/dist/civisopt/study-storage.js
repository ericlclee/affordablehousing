import { SITE, SOURCE_RECORDS } from './snapshot.js';
import { DEFAULT_INPUTS, ENGINE_VERSION, POLICY_SOURCES, buildStudy } from './engine.js';
const clone = value => JSON.parse(JSON.stringify(value));

function validImportedInputs(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('The file has no valid inputs object.');
  const result = clone(DEFAULT_INPUTS);
  for (const key of Object.keys(result.envelope)) {
    if (!Object.hasOwn(value.envelope || {}, key)) throw new Error(`Envelope input ${key} is missing.`);
    result.envelope[key] = value.envelope[key];
  }
  if (!Array.isArray(value.unitMix) || !value.unitMix.length || value.unitMix.length > 20) throw new Error('The room schedule is missing or too large.');
  result.unitMix = value.unitMix.map(row => ({ bedrooms: row.bedrooms, homes: row.homes, areaM2: row.areaM2, habitableRooms: row.habitableRooms }));
  for (const key of Object.keys(result.assumptions)) {
    const row = value.assumptions?.[key];
    if (!row || typeof row !== 'object') throw new Error(`Assumption ${key} is missing.`);
    for (const band of ['low','base','high']) {
      if (!Object.hasOwn(row, band)) throw new Error(`${key} ${band} is missing.`);
      const n = row[band];
      if (n !== null && (typeof n !== 'number' || !Number.isFinite(n) || n < 0)) throw new Error(`${key} ${band} must be a non-negative number or unknown.`);
      result.assumptions[key][band] = n;
    }
    result.assumptions[key].source = typeof row.source === 'string' ? row.source.slice(0, 200) : '';
  }
  for (const key of Object.keys(result.policy)) if (key !== 'otherConditionsConfirmed') result.policy[key] = value.policy?.[key] ?? null;
  result.policy.otherConditionsConfirmed = false; // P0 has no evidence fields to support confirmation.
  result.preferenceMinAffordablePct = value.preferenceMinAffordablePct;
  const audit = buildStudy(SITE, result);
  const structural = audit.errors.filter(e => !e.field.startsWith('assumptions.'));
  if (structural.length) throw new Error(structural[0].message);
  return result;
}


export function readStudySnapshot(text) {
  if (typeof text !== 'string' || text.length > 2_000_000) throw new Error('The study must be JSON text within the single-site size limit.');
  const data = JSON.parse(text);
  if (!data || typeof data !== 'object' || data.schema !== 'civisopt-study-v1') throw new Error('This is not a CivisOpt v1 study file.');
  if (data.engineVersion !== ENGINE_VERSION) throw new Error('The calculation version differs from this edition. Open the matching edition to reproduce the study.');
  if (JSON.stringify(data.policySources) !== JSON.stringify(POLICY_SOURCES)) throw new Error('The policy source versions differ from this edition.');
  if (JSON.stringify(data.site) !== JSON.stringify(SITE)) throw new Error('The pinned site or source metadata differs from this edition. Open the matching site snapshot to reproduce the study.');
  if (JSON.stringify(data.sourceRecords) !== JSON.stringify(SOURCE_RECORDS)) throw new Error('The source record manifest differs from this edition.');
  return { inputs: validImportedInputs(data.inputs), selectedScenarioId: typeof data.selectedScenarioId === 'string' ? data.selectedScenarioId : null };
}

// Regression check: blank numeric assumptions must not corrupt the appraisal.
import assert from 'node:assert/strict';
import fs from 'node:fs';
const html = fs.readFileSync(new URL('index.html', import.meta.url), 'utf8');
const engineCode = html.split('/* ENGINE-START */')[1].split('/* ENGINE-END */')[0];
const E = new Function(engineCode + '\nreturn {engine, withDefaults, BASE_ASSUMPTIONS};')();
const binding = html.slice(html.indexOf('function bindControls('), html.indexOf('function assInput('));
const params = {site_area_m2:5090,podium_coverage:.55,podium_storeys:6,tower_coverage:.15,tower_storeys:8,floor_to_floor_m:3.2,mix_b1:.4,mix_b2:.4,mix_b3:.2,affordable_hr_pct:35,social_rent_share:.6,land_type:'private'};
for (const [key, value, nullable, expected] of [
  ['sale_psm.base', '', false, 8000],
  ['sale_psm.low', '', false, 7200],
  ['sale_psm.high', '', false, 9000],
  ['sale_psm.base', '8500', false, 8500],
  ['land_value', '', false, E.BASE_ASSUMPTIONS.land_value],
  ['borough_cil_psm', '', true, null],
]) {
  const state = {assumptions:E.withDefaults({})};
  let listener;
  const input = {dataset:{a:key,nullable:nullable?'1':'0'},value,addEventListener:(_,f)=>listener=f};
  const root = {querySelectorAll:selector=>selector==='[data-a]'?[input]:[]};
  new Function('S','BASE_ASSUMPTIONS','refresh',binding+'\nreturn bindControls;')(state,E.BASE_ASSUMPTIONS,()=>{})(root);
  listener();
  const actual = key.split('.').reduce((obj,k)=>obj[k],state.assumptions);
  assert.equal(actual,expected,key);
  const result=E.engine(params,state.assumptions);
  assert.ok(Number.isFinite(result.appraisal.gdv),key+' GDV');
  assert.ok(Number.isFinite(result.appraisal.total_cost),key+' costs');
  assert.ok(Number.isFinite(result.surplus),key+' surplus');
}
console.log('PASS: blank/default, edited and nullable assumptions keep finite appraisal results.');

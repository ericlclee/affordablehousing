// Runs the exact engine block from index.html in Node and writes engine_check_inputs.json.
import fs from 'fs'; import path from 'path'; import { fileURLToPath } from 'url';
const dir = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(dir, 'index.html'), 'utf8');
const code = html.split('/* ENGINE-START */')[1].split('/* ENGINE-END */')[0];
const E = new Function(code + '\nreturn { engine, sweep, bestOffer, breakEvenCurve, neighbourStats, projector, ringArea, withDefaults, BASE_ASSUMPTIONS, RULES };')();
const site = JSON.parse(fs.readFileSync(path.join(dir, 'data/site.json'), 'utf8'));
const ctx = JSON.parse(fs.readFileSync(path.join(dir, 'data/context.json'), 'utf8'));
const P = E.projector(site.lat, site.lng);
const ring = site.polygon.map(p => P(p[0], p[1])); ring.pop();
const site_area_m2 = Math.round(E.ringArea(ring));
const ns = E.neighbourStats(ctx.elements, site.polygon, site.lat, site.lng);
const params = { site_area_m2, podium_coverage: 0.55, podium_storeys: 6, tower_coverage: 0.15, tower_storeys: 8, floor_to_floor_m: 3.2,
  mix_b1: 0.40, mix_b2: 0.40, mix_b3: 0.20, affordable_hr_pct: 35, social_rent_share: 0.60, land_type: 'private' };
const assumptions = Object.assign(E.withDefaults({}), { neighbour_median_m: ns.median_m, vision: { ...params } });
const slim = o => { const { breakeven_trace, ...rest } = o; return { ...rest, breakeven_trace }; };
const run = pct => slim(E.engine({ ...params, affordable_hr_pct: pct }, assumptions));
const closed = pct => { // independent closed-form break-even for comparison
  const o = E.engine({ ...params, affordable_hr_pct: pct }, assumptions), f = o.appraisal, a = assumptions;
  const fixed = f.build + f.fees + f.mcil + f.bcil + f.s106 + f.finance + f.land;
  return (fixed - (1 - a.target_return_pct_gdv) * f.affordable_receipts) / (o.market_nia_m2 * (1 - a.sales_pct_market_gdv - a.target_return_pct_gdv));
};
const walk = { dev: 0.6, plan: E.engine(params, assumptions).routes.route_min_pct / 50, res: 0.3, arch: 0.6 };
const t0 = Date.now(); const sw = E.sweep(params, assumptions, walk); const ms = Date.now() - t0;
const pickV = v => v && ({ params: v.params, U: v.U, homes: v.homes, storeys: v.storeys, affordable_hr_pct: v.affordable_hr_pct, surplus: v.surplus, profit_on_gdv: v.profit_on_gdv, V: v.V, route: v.route, nash: v.nash });
const out = {
  generated: new Date().toISOString(), generator: 'node engine_check.mjs (engine block extracted verbatim from index.html)', node: process.version,
  site: { entity: site.entity, polygon_area_m2: site_area_m2, register_hectares: site.hectares },
  neighbour_stats: ns,
  default_params: params,
  base_assumptions: assumptions,
  outputs: { default: run(35), affordable_20: run(20), affordable_35: run(35), affordable_50: run(50) },
  breakeven_closed_form_check: Object.fromEntries([20, 35, 50].map(p => [`affordable_${p}`, { iterated_5: run(p).breakeven_psm, closed_form: closed(p) }])),
  best_offer_base: E.bestOffer(params, assumptions),
  sweep_summary: { count: sw.count, feasible: sw.feasible, ms, walk, blockers: sw.blockers, best: sw.best, balanced: pickV(sw.balanced), higher_return: pickV(sw.higher_return), more_affordable: pickV(sw.more_affordable) }
};
fs.writeFileSync(path.join(dir, 'engine_check_inputs.json'), JSON.stringify(out, null, 1));
const brief = k => { const o = out.outputs[k]; return `${k}: homes ${o.homes} hab ${o.habitable_rooms} GIA ${o.gia_m2.toFixed(0)} GDV ${(o.appraisal.gdv/1e6).toFixed(2)}m cost ${(o.appraisal.total_cost/1e6).toFixed(2)}m surplus ${(o.surplus/1e6).toFixed(2)}m BE ${o.breakeven_psm.toFixed(0)} route ${o.routes.badge} SR ${o.social_rent_homes} U ${JSON.stringify(Object.fromEntries(Object.entries(o.U).map(([k,v])=>[k,+v.toFixed(3)])))}`; };
for (const k of Object.keys(out.outputs)) console.log(brief(k));
console.log('median', ns, 'area', site_area_m2);
console.log('BE check', JSON.stringify(out.breakeven_closed_form_check));
console.log('offer', JSON.stringify(out.best_offer_base));
console.log('sweep', sw.count, sw.feasible, ms + 'ms', JSON.stringify(pickV(sw.balanced)));
console.log('HR', JSON.stringify(pickV(sw.higher_return)));
console.log('MA', JSON.stringify(pickV(sw.more_affordable)));

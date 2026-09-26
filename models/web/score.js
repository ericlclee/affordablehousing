// Approval + S106 scorer for the browser (and Node). No dependencies.
//
//   import { loadModel, score } from "./score.js";
//   const model = await loadModel("./approval_model.json");
//   const out = score(model, { lpa: "Southwark", homes_net: 24, storeys: 6, site_area_m2: 1800, ... });
//
// Generated alongside approval_model.json by scripts/train_models.py. Input names match
// data/processed/features.parquet (see docs/DATA_DICTIONARY.md); any input can be omitted and is
// filled the same way as in training. The preprocessing below mirrors train_models.Preprocessor:
// if you change one, change the other and re-run models/web/check_parity.mjs.

export async function loadModel(url = "./approval_model.json") {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url}: ${res.status}`);
  return res.json();
}

const num = (v) => (v === null || v === undefined || v === "" || Number.isNaN(Number(v)) ? NaN : Number(v));
const flag = (v) => (v === true || v === 1 || v === "1" || v === "true" ? 1 : 0);
const fill = (v, f) => (Number.isNaN(v) ? f : v);
const sigmoid = (z) => 1 / (1 + Math.exp(-z));

// Plain-English names for the driver list
const LABELS = {
  borough: "Borough", avg_home_size_m2: "Average home size", scheme: "Scheme type (HMO / student / co-living)",
  unit_mix: "Unit mix", log_site_area: "Site area", space_std_share_below: "Homes below minimum space standards",
  log_homes_net: "Number of homes", log_ptal: "Public transport access (PTAL)", log_density: "Density",
  log_homes_lost: "Existing homes lost", affordable_pct_major: "Affordable housing %",
  social_rent_pct_major: "Social rent %", has_basement: "Basement", storeys: "Storeys", imd_decile: "Deprivation",
  has_demolition: "Demolition", in_article4_area: "Article 4 area", in_conservation_area: "Conservation area",
  development_type: "Development type", in_opportunity_area: "Opportunity Area", log_nonresi: "Non-residential floorspace",
  has_roof_terrace: "Roof terrace", has_commercial: "Commercial space", flood_zone: "Flood zone",
  premium_amenity: "Gym / pool / concierge", mayor_1c_height: "Height referable to the Mayor",
  in_green_belt: "Green Belt", is_major: "Major scheme (10+ homes)", mayor_1a_over_150_homes: "Over 150 homes",
  has_communal_amenity: "Communal amenity", is_outline: "Outline application", in_town_centre: "Town centre",
  statutory_major: "Statutory major development", listed_building_within_25m: "Listed building nearby",
  brownfield_site_within_50m: "Brownfield register site nearby", has_backland: "Backland / rear garden site",
  has_pub_loss: "Loss of a pub", has_studio: "Studio flats",
};
const groupOf = (f) =>
  f.startsWith("lpa_") ? "borough" : f.startsWith("mix_") ? "unit_mix" : f.startsWith("dev_") ? "development_type"
    : f.startsWith("flood_zone") ? "flood_zone" : f.startsWith("scheme_") ? "scheme" : f;

/** Derive the training-time raw fields (flags, density, height) from user inputs. */
function derive(p) {
  const homes = num(p.homes_net);
  const site = num(p.site_area_m2);
  const storeys = num(p.storeys);
  let height = num(p.height_m_est);
  if (Number.isNaN(height) && !Number.isNaN(storeys)) height = storeys * 3.2;
  let density = num(p.density_homes_per_ha);
  if (Number.isNaN(density) && homes > 0 && site > 0) density = homes / (site / 10000);
  if (density > 1000) density = NaN; // treated as bad data in training
  const premium = p.premium_amenity ?? (flag(p.has_gym) || flag(p.has_pool) || flag(p.has_concierge));
  return {
    ...p, homes, site, storeys, height, density, premium_amenity: premium,
    is_major: homes >= 10,
    statutory_major: homes >= 10 || site >= 5000,
    mayor_1a_over_150_homes: homes > 150,
    mayor_1c_height: p.lpa === "City of London" ? height > 150 : height > 30,
  };
}

/** Build the model's feature vector (object keyed by feature name). */
function features(model, p, pre = model.preprocess) {
  const d = derive(p);
  const x = {};
  const major = d.is_major ? 1 : 0;
  x.log_homes_net = Math.log1p(d.homes);
  x.log_homes_lost = Math.log1p(fill(num(d.homes_lost), 0));
  for (const f of model.preprocess.flags) x[f] = flag(d[f]);
  for (const f of ["mix_studio", "mix_1b", "mix_2b", "avg_home_size_m2", "space_std_share_below"]) x[f] = num(d[f]);
  x.affordable_pct_major = major ? num(d.affordable_pct_units) : 0;
  x.social_rent_pct_major = major ? num(d.social_rent_pct_units) : 0;
  x.storeys = Number.isNaN(d.storeys) ? NaN : Math.min(40, Math.max(1, d.storeys));
  x.log_site_area = d.site > 0 ? Math.log(d.site) : NaN;
  x.log_density = Math.log1p(d.density);
  x.log_nonresi = Math.log1p(Math.max(0, fill(num(d.nonresi_gia_gained_m2), 0)));
  x.log_ptal = Math.log1p(num(d.ptal_ai));
  x.imd_decile = num(d.imd_decile);
  const fz = num(d.flood_zone);
  x.flood_zone_2 = fz === 2 ? 1 : 0;
  x.flood_zone_3 = fz === 3 ? 1 : 0;
  const dev = !d.dev_type || d.dev_type === "other" ? "new_build" : d.dev_type;
  for (const t of ["change_of_use", "conversion", "extension"]) x[`dev_${t}`] = dev === t ? 1 : 0;
  x.scheme_hmo = d.scheme_type === "hmo" ? 1 : 0;
  x.scheme_student_coliving = d.scheme_type === "student" || d.scheme_type === "coliving" ? 1 : 0;

  // Fill gaps exactly as in training (training-year medians)
  for (const [k, v] of Object.entries(pre.medians)) x[k] = fill(x[k], v);
  if (major) {
    x.affordable_pct_major = fill(x.affordable_pct_major, pre.affordable_pct_major);
    x.social_rent_pct_major = fill(x.social_rent_pct_major, pre.social_rent_pct_major);
  }
  x.affordable_pct_major = fill(x.affordable_pct_major, 0);
  x.social_rent_pct_major = fill(x.social_rent_pct_major, 0);
  const grp = pre.storeys_by_dev_type_and_major[`${dev}|${major}`];
  x.storeys = fill(fill(x.storeys, grp ?? NaN), pre.storeys_overall);
  x.imd_decile = fill(x.imd_decile, 5);

  const lpaGrp = pre.small_lpas.includes(d.lpa) ? "Other small" : d.lpa;
  for (const l of pre.lpa_levels.slice(1)) x[`lpa_${l}`] = lpaGrp === l ? 1 : 0;
  x.storeys_x_conservation = x.storeys * x.in_conservation_area;
  x.density_x_ptal = x.log_density * x.log_ptal;
  return { x, known_borough: pre.lpa_levels.includes(lpaGrp) };
}

/** The approval model's feature vector for a proposal (for debugging and parity checks). */
export function featureVector(model, params) {
  const { x } = features(model, params);
  return Object.fromEntries(model.approval.features.map((f) => [f, x[f]]));
}

/** Walk the XGBoost trees; returns margin and per-feature path contributions (Saabas). */
function boost(model, vec) {
  const m = model.approval;
  const contrib = new Map();
  let margin = m.base_margin;
  for (const t of m.trees) {
    let n = 0;
    margin += t.w[0];
    contrib.set("__bias", (contrib.get("__bias") ?? 0) + t.w[0]);
    while (t.l[n] !== -1) {
      const v = vec[t.f[n]];
      // XGBoost compares in 32-bit floats; matching that exactly matters for values on a threshold
      const next = Number.isNaN(v) ? (t.d[n] ? t.l[n] : t.r[n]) : Math.fround(v) < Math.fround(t.t[n]) ? t.l[n] : t.r[n];
      const fname = m.features[t.f[n]];
      contrib.set(fname, (contrib.get(fname) ?? 0) + (t.w[next] - t.w[n]));
      margin += t.w[next] - t.w[n];
      n = next;
    }
  }
  return { margin, contrib };
}

/** Platt calibration on the model margin: p = sigmoid(a * margin + b). */
const calibrate = (model, margin) => sigmoid(model.approval.calibration.a * margin + model.approval.calibration.b);

function baselineRate(model, lpa, homes) {
  const b = model.baseline;
  const band = homes <= 9 ? "1-9" : homes <= 49 ? "10-49" : homes <= 149 ? "50-149" : "150+";
  const cell = b.by_borough_size[`${lpa}|${band}`];
  return cell ? (cell[0] + b.shrinkage * b.overall) / (cell[1] + b.shrinkage) : b.overall;
}

function s106(model, p) {
  const s = model.s106_given_approved;
  const pre = { ...model.preprocess, medians: s.fill_values.medians, affordable_pct_major: s.fill_values.affordable_pct_major,
    social_rent_pct_major: s.fill_values.social_rent_pct_major, storeys_overall: s.fill_values.storeys_overall,
    storeys_by_dev_type_and_major: s.fill_values.storeys_by_dev_type_and_major, lpa_levels: s.lpa_levels };
  const { x } = features(model, p, pre);
  let z = s.intercept;
  for (const f of s.features) z += s.coef_standardised[f] * (((x[f] ?? 0) - s.scaler_mean[f]) / s.scaler_scale[f]);
  return sigmoid(z);
}

/**
 * Score a proposal.
 * Returns { p_approved, p_approved_raw, baseline_rate, p_s106, p_approved_with_s106, drivers, warnings }.
 * drivers: grouped features ranked by their effect on this prediction, in approximate percentage points.
 */
export function score(model, params) {
  const { x, known_borough } = features(model, params);
  const vec = model.approval.features.map((f) => x[f]);
  const { margin, contrib } = boost(model, vec);
  const raw = sigmoid(margin);
  const p = calibrate(model, margin);

  // Group contributions (log-odds; they sum to margin - bias), then convert to approximate
  // percentage points at this prediction
  const slope = model.approval.calibration.a * p * (1 - p) * 100;
  const grouped = new Map();
  for (const [f, c] of contrib) {
    if (f === "__bias") continue;
    const g = groupOf(f);
    grouped.set(g, (grouped.get(g) ?? 0) + c);
  }
  const drivers = [...grouped.entries()]
    .map(([g, c]) => ({ feature: g, label: LABELS[g] ?? g, effect_pp: +(c * slope).toFixed(1) }))
    .filter((d) => Math.abs(d.effect_pp) >= 0.1)
    .sort((a, b) => Math.abs(b.effect_pp) - Math.abs(a.effect_pp));

  const warnings = [];
  if (!known_borough) warnings.push(`Borough "${params.lpa}" not in training data; using the reference borough.`);
  if (num(params.homes_net) >= 10) warnings.push("Few major schemes in the data (682): wider uncertainty for 10+ homes.");
  // S106: for 10+ homes an agreement is near-certain in practice (the affordable-housing threshold),
  // and the decision-text label under-records it (32% positive), so no model estimate is given.
  const major = num(params.homes_net) >= 10;
  const ps106 = major ? null : s106(model, params);
  return {
    p_approved: p,
    p_approved_raw: raw,
    baseline_rate: baselineRate(model, params.lpa, num(params.homes_net)),
    p_s106: ps106,
    p_approved_with_s106: major ? p : p * ps106,
    s106_note: major
      ? "10+ homes: an S106 agreement is expected (affordable housing and other obligations)."
      : `Indicative only. ${model.s106_given_approved.reliability}`,
    drivers,
    warnings,
  };
}

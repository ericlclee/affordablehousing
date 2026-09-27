import { readStudySnapshot } from './study-storage.js';
import { SITE, SOURCE_RECORDS } from './snapshot.js';
import { DEFAULT_INPUTS, POLICY_SOURCES, ENGINE_VERSION, buildStudy } from './engine.js';
import { screeningAvailability } from './adapter.js';

const $ = selector => document.querySelector(selector);
const fmt = (n, digits = 0) => Number.isFinite(n) ? new Intl.NumberFormat('en-GB', { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(n) : 'Unknown';
const money = n => Number.isFinite(n) ? `£${fmt(n)}` : 'Unknown';
const shortMoney = n => !Number.isFinite(n) ? 'Unknown' : Math.abs(n) >= 1000000 ? `£${fmt(n / 1000000, 2)}m` : Math.abs(n) >= 1000 ? `£${fmt(n / 1000, 0)}k` : money(n);
const escape = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[ch]);
const safeUrl = value => { try { const url = new URL(value, location.href); return ['http:', 'https:'].includes(url.protocol) ? url.href : '#'; } catch { return '#'; } };
const clone = value => JSON.parse(JSON.stringify(value));

// These values are deliberately illustrative. No public source in this demo
// provides a scheme-specific appraisal for this parcel.
const PRESETS = {
  marketValuePerM2: [5500, 6500, 7500],
  socialTransferPerM2: [1800, 2300, 2800],
  intermediateTransferPerM2: [2700, 3300, 3900],
  buildCostPerGiaM2: [2400, 2800, 3300],
  abnormalCosts: [200000, 400000, 800000],
  feesPctOfBuild: [8, 10, 12],
  contingencyPctOfBuild: [5, 7, 10],
  financeCosts: [350000, 500000, 750000],
  cilCosts: [100000, 200000, 300000],
  s106Costs: [100000, 200000, 350000],
  landCost: [1500000, 2000000, 2500000],
  otherReceipts: [0, 0, 0],
  targetReturn: [1000000, 1500000, 2000000],
};
const presetInputs = () => {
  const state = clone(DEFAULT_INPUTS);
  state.policy.applicationDate = null;
  state.policy.landType = 'unknown';
  state.policy.otherConditionsConfirmed = false;
  for (const [key, values] of Object.entries(PRESETS)) {
    const row = state.assumptions[key];
    [row.low, row.base, row.high] = values;
    row.source = key === 'otherReceipts' ? 'Illustrative zero: no other receipt included' : 'Illustrative demo input · replace with project evidence';
  }
  return state;
};
let inputs = presetInputs();
let study = null;
let selectedId = null;

function renderSite() {
  $('#site-name').textContent = SITE.name;
  $('#site-location').textContent = `${SITE.borough}, London · register site ${SITE.id}`;
  $('#site-area').textContent = `${fmt(SITE.areaM2, 0)} m²`;
  $('#site-source').textContent = SITE.sourceName;
  $('#site-date').textContent = SITE.recordDate || 'Unknown';
  $('#site-source-link').href = safeUrl(SITE.sourceUrl);
  $('#site-verification').textContent = 'Public record corroborated · boundary indicative';
  $('#site-unknowns').textContent = SITE.unknowns?.[0] || 'Site constraints and legal boundary require review.';
  const ring = SITE.geometry?.coordinates?.[0] || [];
  const metricRing = SITE.projectedGeometry?.coordinates?.[0];
  if (metricRing?.length > 2) {
    const xs = metricRing.map(p => p[0]), ys = metricRing.map(p => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const dx = maxX - minX || 1, dy = maxY - minY || 1;
    const scale = Math.min(276 / dx, 169 / dy);
    const offsetX = (340 - dx * scale) / 2, offsetY = (200 - dy * scale) / 2;
    const points = metricRing.map(([x, y]) => `${(offsetX + (x - minX) * scale).toFixed(1)} ${(offsetY + (maxY - y) * scale).toFixed(1)}`);
    $('#outline-path').setAttribute('d', `M${points.join(' L')} Z`);
  }
  const mapPanel = $('.map-panel');
  if (!window.L || ring.length < 3) { mapPanel.classList.add('map-fallback'); return; }
  try {
    const map = L.map('site-map', { zoomControl: false, scrollWheelZoom: false, attributionControl: true });
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '© OpenStreetMap contributors' }).addTo(map);
    const layer = L.geoJSON(SITE.geometry, { style: { color: '#225441', weight: 3, fillColor: '#b5d0ad', fillOpacity: .52 } }).addTo(map);
    map.fitBounds(layer.getBounds().pad(.65));
    L.control.zoom({ position: 'topleft' }).addTo(map);
    mapPanel.classList.remove('map-fallback');
  } catch { mapPanel.classList.add('map-fallback'); }
}

function renderInputs() {
  const form = $('#study-form');
  for (const [key, value] of Object.entries(inputs.envelope)) {
    const el = form.elements.namedItem(key);
    if (el) el.value = ['coverageRatio', 'giaEfficiency', 'saleableEfficiency'].includes(key) ? String(value == null ? '' : Number((value * 100).toFixed(10))) : value;
  }
  for (const [key, value] of Object.entries(inputs.policy)) {
    const el = form.elements.namedItem(key);
    if (el && key !== 'otherConditionsConfirmed') el.value = value ?? '';
  }
  form.elements.namedItem('preferenceMinAffordablePct').value = inputs.preferenceMinAffordablePct;
  $('#mix-rows').innerHTML = inputs.unitMix.map((row, i) => `<tr><th scope="row">${escape(row.bedrooms)} bed</th><td><input data-mix="${i}" data-key="homes" type="number" min="0" max="999" step="1" value="${escape(row.homes)}" aria-label="${escape(row.bedrooms)} bedroom homes"></td><td><input data-mix="${i}" data-key="areaM2" type="number" min="1" max="1000" step="1" value="${escape(row.areaM2)}" aria-label="${escape(row.bedrooms)} bedroom area in square metres"></td><td><input data-mix="${i}" data-key="habitableRooms" type="number" min="1" max="20" step="1" value="${escape(row.habitableRooms)}" aria-label="${escape(row.bedrooms)} bedroom habitable rooms per home"></td></tr>`).join('');
  $('#assumption-rows').innerHTML = Object.entries(inputs.assumptions).map(([key, row]) => `<tr class="${['low','base','high'].some(b => row[b] == null) || !row.source?.trim() ? 'missing' : ''}"><td><b>${escape(row.label)} <span class="unit">${escape(row.unit)}</span></b><input class="source-input" data-assumption="${escape(key)}" data-band="source" type="text" maxlength="200" value="${escape(row.source || '')}" aria-label="${escape(row.label)} source" placeholder="Evidence or illustrative assumption"></td>${['low','base','high'].map(b => `<td><input data-assumption="${escape(key)}" data-band="${b}" type="number" min="0" step="any" value="${row[b] ?? ''}" aria-label="${escape(row.label)} ${b}"></td>`).join('')}</tr>`).join('');
}

function readNumber(el) { return el.value.trim() === '' ? null : Number(el.value); }
function handleEdit(event) {
  const el = event.target;
  if (!(el instanceof HTMLInputElement || el instanceof HTMLSelectElement)) return;
  if (el.dataset.assumption) {
    inputs.assumptions[el.dataset.assumption][el.dataset.band] = el.dataset.band === 'source' ? el.value : readNumber(el);
  } else if (el.dataset.mix) {
    inputs.unitMix[Number(el.dataset.mix)][el.dataset.key] = readNumber(el);
  } else if (el.name in inputs.envelope) {
    const value = readNumber(el);
    inputs.envelope[el.name] = value == null ? null : ['coverageRatio','giaEfficiency','saleableEfficiency'].includes(el.name) ? value / 100 : value;
  } else if (el.name === 'preferenceMinAffordablePct') {
    inputs.preferenceMinAffordablePct = readNumber(el);
  } else if (el.name in inputs.policy && el.name !== 'otherConditionsConfirmed') {
    inputs.policy[el.name] = el.name === 'socialRentSharePct' ? readNumber(el) : el.value || null;
  }
  recalculate();
}

function showErrors(errors) {
  const box = $('#validation-errors');
  if (!errors.length) { box.hidden = true; box.innerHTML = ''; return; }
  box.hidden = false;
  const limited = errors.slice(0, 5);
  box.innerHTML = `<strong>${errors.length} input issue${errors.length === 1 ? '' : 's'} to resolve</strong><ul>${limited.map(e => `<li>${escape(e.message)}</li>`).join('')}${errors.length > 5 ? `<li>And ${errors.length - 5} more. Review highlighted or empty inputs.</li>` : ''}</ul>`;
}

const routes = [['h5FastTrack','London Plan H5 · Fast Track'],['h5ViabilityTested','London Plan H5 · viability tested'],['temporary2026','March 2026 temporary route']];
function renderScenarios() {
  const scenarios = study?.scenarios || [];
  $('#study-state').textContent = scenarios.length ? `${scenarios.length} concepts · fixed inputs` : 'Resolve inputs';
  if (!scenarios.length) {
    $('#scenario-cards').innerHTML = '<p class="field-help">The comparison needs a valid envelope and integer room schedule. Resolve the issues above to restore the three pinned concepts.</p>';
    $('#comparison-note').textContent = 'No preference is applied while the concept geometry or schedule is unresolved.';
    return;
  }
  if (!scenarios.some(s => s.id === selectedId)) selectedId = study.balancedId || scenarios[0].id;
  $('#scenario-cards').innerHTML = scenarios.map(s => {
    const f = s.finance.base;
    const capacity = s.geometry.remainingSaleableM2;
    const hasCosts = Number.isFinite(f.developmentSurplus);
    const route = s.policy.temporary2026;
    return `<article class="scenario-card ${s.id === study.balancedId ? 'balanced' : ''}"><div class="card-head"><h3>${escape(s.label)}</h3>${s.nondominated === true ? '<span class="card-badge">Trade-off frontier</span>' : ''}</div><div class="card-badges">${(s.badges || []).map(badge => `<span class="card-badge">${escape(badge)}</span>`).join('')}</div><div class="card-metric">${fmt(s.affordableHabitableRoomsPct, 1)}% <small>affordable rooms</small></div><p class="metric-label">${fmt(s.affordableHabitableRooms)} of ${fmt(s.totalHabitableRooms)} habitable rooms</p><div class="metric-list"><span>Homes</span><strong>${fmt(s.homes)}</strong><span>Affordable homes</span><strong>${fmt(s.affordableHomes)}</strong><span>GIA / height</span><strong>${fmt(s.geometry.giaM2)} m² / ${fmt(s.geometry.heightM, 1)} m</strong><span>Saleable headroom</span><strong>${fmt(capacity)} m²</strong><span>Base surplus</span><strong>${shortMoney(f.developmentSurplus)}</strong><span>Break-even sale value</span><strong>${Number.isFinite(f.breakEvenMarketValuePerM2) ? `${money(f.breakEvenMarketValuePerM2)}/m²` : s.tenure.marketAreaM2 === 0 ? 'Undefined: no market area' : 'Unknown'}</strong></div><div class="case-strip"><div><span>All low inputs</span><strong>${shortMoney(s.finance.low.developmentSurplus)}</strong></div><div><span>Base inputs</span><strong>${shortMoney(f.developmentSurplus)}</strong></div><div><span>All high inputs</span><strong>${shortMoney(s.finance.high.developmentSurplus)}</strong></div></div><p class="card-note">${!hasCosts ? 'Commercial result unknown until all required assumptions are supplied.' : `${escape(route.status)} on the 2026 route. All material site conditions need review.`}</p><button class="card-select" data-scenario="${escape(s.id)}" type="button" aria-pressed="${selectedId === s.id}">${selectedId === s.id ? 'Selected for detail' : 'Inspect this concept'}</button></article>`;
  }).join('');
  const preference = inputs.preferenceMinAffordablePct;
  const preferred = scenarios.find(s => s.id === study.balancedId);
  $('#comparison-note').textContent = preferred ? `Balanced marks the highest base surplus among pinned concepts meeting your ${fmt(preference)}% minimum affordable-room preference. “Higher return” and “More affordable rooms” can overlap with it. The green frontier marker means no other pinned concept has both more affordable rooms and a higher base surplus. These are comparisons, not planning recommendations. Low and high pair the input bands; they are not probability bounds.` : `No pinned concept has a complete financial result and meets your ${fmt(preference)}% room preference. All raw comparisons remain visible. Low and high pair the input bands; they are not probability bounds.`;
}

function selectedScenario() { return study?.scenarios?.find(s => s.id === selectedId) || study?.scenarios?.[0]; }
function renderChart() {
  const chart = $('#break-even-chart');
  const scenarios = study?.scenarios || [];
  if (!scenarios.length) { chart.textContent = 'Awaiting a valid concept.'; $('#break-even-note').textContent = ''; return; }
  const baseline = inputs.assumptions.marketValuePerM2.base;
  const values = scenarios.map(s => s.finance.base.breakEvenMarketValuePerM2).filter(Number.isFinite);
  if (!values.length || !Number.isFinite(baseline)) { chart.textContent = 'Break-even is unknown until the base financial inputs and market area are complete.'; $('#break-even-note').textContent = ''; return; }
  const max = Math.max(baseline, ...values) * 1.13 || 1;
  chart.innerHTML = scenarios.map(s => {
    const value = s.finance.base.breakEvenMarketValuePerM2;
    return `<div class="chart-row"><strong>${escape(s.label)}</strong><div class="chart-track"><div class="chart-bar" style="width:${Math.max(0, Math.min(100, value / max * 100))}%"></div><span class="chart-baseline" style="left:${baseline / max * 100}%"></span></div><span class="chart-value">${money(value)}</span></div>`;
  }).join('') + `<div class="chart-key"><i></i>Entered base market value: ${money(baseline)}/m²</div>`;
  $('#break-even-note').textContent = 'The break-even equation uses the selected cost and fixed return inputs. It does not estimate a lender IRR.';
}

function renderSensitivity() {
  const view = $('#sensitivity-view');
  const s = selectedScenario();
  if (!s || !Number.isFinite(s.finance.base.developmentSurplus)) { view.textContent = 'Supply every required commercial assumption to see sensitivity.'; return; }
  // The engine returns sensitivity for its preference concept; calculate the same
  // simple one-input-at-a-time surplus swing for a manually selected card by
  // rebuilding with adjusted base values, never by changing the stored inputs.
  let rows = study.sensitivity || [];
  if (s.id !== study.balancedId) {
    rows = Object.entries(inputs.assumptions).map(([key, row]) => {
      const changedLow = clone(inputs), changedHigh = clone(inputs);
      changedLow.assumptions[key].base = row.low;
      changedHigh.assumptions[key].base = row.high;
      const lowScenario = buildStudy(SITE, changedLow).scenarios.find(item => item.id === s.id);
      const highScenario = buildStudy(SITE, changedHigh).scenarios.find(item => item.id === s.id);
      const lowSurplus = lowScenario?.finance.base.developmentSurplus;
      const highSurplus = highScenario?.finance.base.developmentSurplus;
      return { key, label: row.label, lowSurplus, highSurplus, swing: Math.abs(highSurplus - lowSurplus) };
    }).sort((a, b) => b.swing - a.swing);
  }
  view.innerHTML = rows.slice(0, 5).map(row => `<div class="sensitivity-row"><span>${escape(row.label)}</span><b>${shortMoney(row.lowSurplus)} → ${shortMoney(row.highSurplus)}</b></div>`).join('') || 'Sensitivity unknown.';
}

function renderSelectedDetail() {
  const target = $('#selected-detail');
  const s = selectedScenario();
  if (!s) { target.innerHTML = ''; return; }
  const metrics = [
    ['Gross development value', 'gdv', money],
    ['Total costs including land', 'totalCost', money],
    ['Development surplus', 'developmentSurplus', money],
    ['Profit on cost, including land', 'profitOnCostPct', n => Number.isFinite(n) ? `${fmt(n, 1)}%` : 'Unknown'],
    ['Residual land value after fixed target return', 'residualLandValue', money],
    ['Break-even market value / m²', 'breakEvenMarketValuePerM2', n => Number.isFinite(n) ? `${money(n)}/m²` : s.tenure.marketAreaM2 === 0 ? 'Undefined' : 'Unknown'],
  ];
  const rows = metrics.map(([label, key, format]) => `<tr><th scope="row">${escape(label)}</th>${['low','base','high'].map(band => `<td>${format(s.finance[band][key])}</td>`).join('')}</tr>`).join('');
  const mix = s.allocation.map(row => `<tr><th scope="row">${escape(row.bedrooms)} bed</th><td>${fmt(row.marketHomes)}</td><td>${fmt(row.socialHomes)}</td><td>${fmt(row.intermediateHomes)}</td></tr>`).join('');
  target.innerHTML = `<div><h3>${escape(s.label)} · financial detail</h3><p>Every column pairs the assumptions in that band; these are not probability bounds. Grant is excluded. The fixed target return is ${money(inputs.assumptions.targetReturn.base)} in the base case.</p><div class="table-scroll"><table class="detail-table"><thead><tr><th>Measure</th><th>All low inputs</th><th>Base inputs</th><th>All high inputs</th></tr></thead><tbody>${rows}</tbody></table></div></div><div><h3>Exact home allocation</h3><p>${fmt(s.affordableHabitableRooms)} of ${fmt(s.totalHabitableRooms)} habitable rooms (${fmt(s.affordableHabitableRoomsPct, 1)}%); ${fmt(s.affordableHomes)} of ${fmt(s.homes)} homes (${fmt(s.affordableHomes / s.homes * 100, 1)}%). Social rent: ${fmt(s.socialHabitableRooms)} of ${fmt(s.affordableHabitableRooms)} affordable rooms (${fmt(s.socialHabitableRooms / s.affordableHabitableRooms * 100, 1)}%).</p><div class="table-scroll"><table class="detail-table"><thead><tr><th>Home type</th><th>Market</th><th>Social rent</th><th>Intermediate</th></tr></thead><tbody>${mix}</tbody></table></div></div>`;
}

function renderEvidence() {
  const s = selectedScenario();
  $('#policy-checks').innerHTML = s ? routes.map(([key, label]) => {
    const route = s.policy[key];
    return `<div class="policy-item"><h4>${escape(label)}<span>${escape(route.status)}</span></h4><p>${(route.reasons || []).map(escape).join(' ')}</p><a href="${safeUrl(route.sourceUrl)}" target="_blank" rel="noopener noreferrer">Read policy source ↗</a></div>`;
  }).join('') : '<p class="field-help">Route checks appear after the concept inputs are valid.</p>';
  const screening = screeningAvailability();
  const readiness = [
    ['Validation documents', 'Unverified', 'Borough validation list, ownership certificates, plans and fee must be checked for this application.'],
    ['Conditional statutory assessments', 'Unknown trigger', 'Flood, ecology, transport, daylight and other assessment triggers need a site-level review.'],
    ['Planning merits and local policy', 'Requires review', 'The room thresholds do not resolve design, local-plan, affordable tenure or site-allocation issues.'],
    ['Mayor referral', 'Unknown trigger', 'Check whether strategic referral thresholds and exceptions apply to the final scheme.'],
    ['Post-permission conditions', 'Not applicable yet', 'Reserved matters, conditions and obligations arise only after an actual decision.'],
  ];
  $('#readiness-checks').innerHTML = readiness.map(([name, status, note]) => `<div class="policy-item"><h4>${escape(name)}<span>${escape(status)}</span></h4><p>${escape(note)}</p></div>`).join('') + `<p class="readiness-note">Provisional checklist only: the companion rule register is unavailable for this build. ${escape(screening.label)}. ${escape(screening.reasons.join(' '))}</p>`;
  $('#source-records').innerHTML = `<p class="readiness-note">Comparable decisions: insufficient verified major residential records for this pinned study. None is used in the calculations.</p>` + SOURCE_RECORDS.map(record => `<div class="source-item"><a href="${safeUrl(record.url)}" target="_blank" rel="noopener noreferrer">${escape(record.name)} ↗</a><p>${escape(record.date || 'Date unknown')} · ${escape(record.status || 'Status unknown')}</p><p>${escape(record.note || '')}</p></div>`).join('');
  const unknowns = [...(SITE.unknowns || []), 'Site-specific construction, transfer values, land cost, CIL and Section 106 figures are illustrative until supported by project evidence.', 'Confirm borough Local Plan policies and all conditions for any affordable-housing route.', 'No dated cash-flow schedule has been supplied, so IRR is unavailable.'];
  $('#open-questions').innerHTML = unknowns.map(item => `<li>${escape(item)}</li>`).join('');
  $('#formulae-content').innerHTML = Object.entries(study?.formulae || {}).map(([name, formula]) => `<p><strong>${escape(name.replace(/([A-Z])/g, ' $1'))}:</strong> ${escape(formula)}</p>`).join('');
}

function renderPrint() {
  const s = selectedScenario();
  $('#print-meta').textContent = `${SITE.name} · ${SITE.borough} · ${fmt(SITE.areaM2)} m² · Source snapshot ${SITE.sourceSnapshotAt}`;
  const scenarios = study?.scenarios || [];
  const polygon = escape($('#outline-path').getAttribute('d') || '');
  const image = `<svg class="print-outline" viewBox="0 0 340 220" role="img" aria-label="Site boundary from the pinned source polygon"><rect width="340" height="220" fill="#e9eee8"/><path d="${polygon}" fill="#d7e5d7" stroke="#225441" stroke-width="4"/></svg>`;
  const conceptRows = scenarios.map(item => `<tr><td>${escape(item.label)}</td><td>${fmt(item.affordableHabitableRooms)} / ${fmt(item.totalHabitableRooms)} (${fmt(item.affordableHabitableRoomsPct, 1)}%)</td><td>${fmt(item.affordableHomes)}</td><td>${shortMoney(item.finance.base.developmentSurplus)}</td><td>${Number.isFinite(item.finance.base.breakEvenMarketValuePerM2) ? `${money(item.finance.base.breakEvenMarketValuePerM2)}/m²` : 'Unknown'}</td><td>${escape(item.policy.h5FastTrack.status)} / ${escape(item.policy.temporary2026.status)}</td></tr>`).join('');
  const assumptionRows = Object.values(inputs.assumptions).map(row => `<tr><td>${escape(row.label)} (${escape(row.unit)})</td><td>${[row.low,row.base,row.high].map(value => value == null ? 'Unknown' : row.unit.includes('%') ? `${fmt(value)}%` : money(value)).join(' / ')}</td><td>${escape(row.source || 'Source unknown')}</td></tr>`).join('');
  $('#print-summary').innerHTML = `${image}<h3>Site and concept</h3><p>GLA Brownfield Register site ${escape(SITE.id)}; indicative polygon and ${fmt(SITE.areaM2)} m² projected area. ${fmt(inputs.envelope.storeys)} storeys, ${fmt(inputs.envelope.coverageRatio * 100)}% site coverage. Room schedule: ${inputs.unitMix.map(row => `${fmt(row.homes)} × ${escape(row.bedrooms)} bed (${fmt(row.habitableRooms)} habitable rooms)`).join('; ')}. Application validation date: ${escape(inputs.policy.applicationDate || 'unknown')}.</p><h3>Three pinned concepts</h3><table><thead><tr><th>Concept</th><th>Affordable rooms</th><th>Affordable homes</th><th>Base surplus</th><th>Break-even sale</th><th>H5 Fast Track / 2026 route</th></tr></thead><tbody>${conceptRows}</tbody></table><p>H5 viability-tested route: requires a scheme-specific viability review for every concept. All policy states are provisional. Low/base/high pair the entered input bands and are not confidence intervals. Grant excluded; no cash-flow IRR. Comparable decisions: none verified for this study.</p><h3>Low / base / high inputs and provenance</h3><table><thead><tr><th>Assumption</th><th>Low / base / high</th><th>Source</th></tr></thead><tbody>${assumptionRows}</tbody></table><h3>Sources and unresolved evidence</h3><p>${SOURCE_RECORDS.map(r => `<a href="${safeUrl(r.url)}">${escape(r.name)}</a> (${escape(r.date)}; ${escape(r.status)})`).join(' · ')}</p><p>${(SITE.unknowns || []).slice(0, 3).map(escape).join(' ')}</p>`;
}

function recalculate() {
  try {
    study = buildStudy(SITE, inputs);
    showErrors(study.errors || []);
    const g = study.geometry;
    $('#capacity-line').textContent = g ? `${fmt(g.scheduledAreaM2)} m² scheduled / ${fmt(g.saleableCapacityM2)} m² saleable capacity · ${fmt(g.remainingSaleableM2)} m² remaining` : 'Capacity pending valid envelope and room schedule.';
    renderScenarios(); renderChart(); renderSensitivity(); renderSelectedDetail(); renderEvidence(); renderPrint();
    $('#screen-error').hidden = true;
  } catch (error) {
    $('#screen-error').hidden = false;
    $('#screen-error').textContent = `The concept could not be recalculated: ${error.message}. Review your inputs or reload the page.`;
  }
}


function saveSnapshot() {
  const payload = { schema: 'civisopt-study-v1', engineVersion: ENGINE_VERSION, policySources: POLICY_SOURCES, savedAt: new Date().toISOString(), site: SITE, sourceRecords: SOURCE_RECORDS, inputs, selectedScenarioId: selectedId, result: study };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a'); link.href = url; link.download = `civisopt-${SITE.id}-${new Date().toISOString().slice(0, 10)}.json`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('#snapshot-status').textContent = 'Study JSON saved.';
}
async function loadSnapshot(event) {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 2_000_000) throw new Error('The JSON file is too large for a single-site study.');
    const restored = readStudySnapshot(await file.text());
    inputs = restored.inputs;
    selectedId = restored.selectedScenarioId;
    renderInputs(); recalculate();
    $('#snapshot-status').textContent = `Loaded ${file.name}. Results recalculated from saved inputs.`;
  } catch (error) { $('#snapshot-status').textContent = `Could not load study: ${error.message}`; }
  event.target.value = '';
}

renderSite(); renderInputs(); recalculate();
$('#study-form').addEventListener('input', handleEdit);
$('#study-form').addEventListener('change', handleEdit);
$('#assumption-rows').addEventListener('input', handleEdit);
$('#scenario-cards').addEventListener('click', event => { const button = event.target.closest('[data-scenario]'); if (!button) return; selectedId = button.dataset.scenario; renderScenarios(); renderSensitivity(); renderSelectedDetail(); renderEvidence(); renderPrint(); });
$('#reset-assumptions').addEventListener('click', () => { const defaults = presetInputs(); inputs.assumptions = defaults.assumptions; renderInputs(); recalculate(); });
$('#print-brief').addEventListener('click', () => { renderPrint(); window.print(); });
$('#download-json').addEventListener('click', saveSnapshot);
$('#load-json').addEventListener('change', loadSnapshot);

// Standalone, offline brief for browsers where a native print dialog is unavailable.
$('#download-brief').addEventListener('click', () => {
  renderPrint();
  const sheet = [...document.styleSheets].find(item => item.href?.endsWith('/civisopt/ui.css'));
  const printCss = [...sheet.cssRules].filter(rule => rule.type === CSSRule.MEDIA_RULE && rule.conditionText === 'print').map(rule => [...rule.cssRules].map(item => item.cssText).join('\n')).join('\n');
  const html = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CivisOpt evidence brief</title><style>*{box-sizing:border-box}body{font-family:Arial,sans-serif;width:188mm;margin:10mm auto}a{color:#225441}h2,h3{font-family:Arial,sans-serif}' + printCss + '@media print{body{width:auto;margin:0}}</style><body>' + $('#print-sheet').outerHTML + '</body></html>';
  const url = URL.createObjectURL(new Blob([html], {type:'text/html'}));
  const link = document.createElement('a'); link.href = url; link.download = `civisopt-brief-${SITE.id}.html`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('#snapshot-status').textContent = 'Evidence brief downloaded. Open it in a browser to print or save as PDF.';
});

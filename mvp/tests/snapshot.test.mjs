import assert from 'node:assert/strict';
import { SITE } from '../dist/civisopt/snapshot.js';

const ring = SITE.projectedGeometry.coordinates[0];
let twiceArea = 0;

for (let i = 0; i < ring.length - 1; i += 1) {
  const [x1, y1] = ring[i];
  const [x2, y2] = ring[i + 1];
  twiceArea += x1 * y2 - x2 * y1;
}

const shoelaceAreaM2 = Math.abs(twiceArea) / 2;
assert.ok(Math.abs(shoelaceAreaM2 - SITE.areaM2) < 0.01,
  `projected polygon area ${shoelaceAreaM2} should match SITE.areaM2 ${SITE.areaM2}`);

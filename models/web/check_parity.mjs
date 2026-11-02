// Checks score.js against the Python model on held-out test rows.
//   node models/web/check_parity.mjs
import { readFile } from "node:fs/promises";
import { score } from "./score.js";

const dir = new URL(".", import.meta.url);
const model = JSON.parse(await readFile(new URL("approval_model.json", dir)));
const samples = JSON.parse(await readFile(new URL("parity_samples.json", dir)));
let maxA = 0, maxS = 0, guarded = 0, guardMismatch = 0;
for (const s of samples) {
  const out = score(model, s.input);
  if ((out.status !== "ok") !== s.expected_guarded) guardMismatch++;
  if (out.status !== "ok") { guarded++; continue; }
  maxA = Math.max(maxA, Math.abs(out.p_approved - s.expected_p_approved));
  if (out.p_s106 !== null) maxS = Math.max(maxS, Math.abs(out.p_s106 - s.expected_p_s106));
}
console.log(`${samples.length} samples (${guarded} stopped, ${guardMismatch} stop mismatches) | max |JS - Python|: p_approved ${maxA.toExponential(2)}, p_s106 ${maxS.toExponential(2)}`);
const ok = maxA < 1e-4 && maxS < 1e-4 && guardMismatch === 0;
console.log(ok ? "PARITY OK" : "PARITY FAILED");
process.exit(ok ? 0 : 1);

// Server-side AI for the agents chat. index.html POSTs { agent, messages, system } here when no
// browser key is connected. The Groq key lives only in the Vercel env var GROQ_API_KEY.
// Guards: only this site's pages may call it (Origin/Referer check), a small per-IP rate limit,
// and a 12 s timeout on every Groq request, so the endpoint cannot be used as an open AI relay.
const BASE = 'https://api.groq.com/openai/v1';
const PREFER = [/qwen/i, /kimi/i, /llama-3\.3/i, /gpt-oss/i, /llama/i];  // same order as the Connect AI panel
const ALLOWED = [/^https:\/\/project106\.vercel\.app$/, /^https:\/\/proposal106-submission(-[a-z0-9-]+)?\.vercel\.app$/, /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/];
const HITS = new Map();            // ip -> recent request times (per function instance)
const LIMIT = 20, WINDOW_MS = 60000;
let cachedModel = process.env.GROQ_MODEL || '';

function originOf(req) {
  const o = req.headers.origin;
  if (o) return o;
  try { return new URL(req.headers.referer || '').origin; } catch (e) { return ''; }
}
function limited(ip) {
  const now = Date.now(), list = (HITS.get(ip) || []).filter(t => now - t < WINDOW_MS);
  list.push(now); HITS.set(ip, list);
  if (HITS.size > 5000) HITS.clear();
  return list.length > LIMIT;
}
async function groq(path, key, body) {
  const ctl = new AbortController(), timer = setTimeout(() => ctl.abort(), 12000);
  try {
    return await fetch(BASE + path, body
      ? { method: 'POST', headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' }, body: JSON.stringify(body), signal: ctl.signal }
      : { headers: { Authorization: 'Bearer ' + key }, signal: ctl.signal });
  } finally { clearTimeout(timer); }
}
async function pickModel(key) {
  if (cachedModel) return cachedModel;
  const r = await groq('/models', key);
  if (!r.ok) throw new Error('models ' + r.status);
  const ids = ((await r.json()).data || []).filter(m => m.active !== false).map(m => m.id)
    .filter(id => !/whisper|tts|guard|embed|vision|prompt/i.test(id));
  for (const re of PREFER) { const hit = ids.find(id => re.test(id)); if (hit) return (cachedModel = hit); }
  return (cachedModel = ids[0]);
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  if (!ALLOWED.some(re => re.test(originOf(req)))) return res.status(403).json({ error: 'This endpoint only serves the Project 106 site' });
  const ip = String(req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'unknown';
  if (limited(ip)) return res.status(429).json({ error: 'Too many requests, try again in a minute' });
  const key = process.env.GROQ_API_KEY;
  if (!key) return res.status(503).json({ error: 'GROQ_API_KEY not set' });

  const { messages, system } = req.body || {};
  const msgs = [{ role: 'system', content: String(system || '').slice(0, 8000) }].concat(
    (Array.isArray(messages) ? messages : []).slice(-12).map(m => ({
      role: m.role === 'assistant' ? 'assistant' : 'user',
      content: String(m.role === 'assistant' && m.name ? '[' + m.name + '] ' + m.content : m.content || '').slice(0, 2000)
    }))
  );

  try {
    const model = await pickModel(key);
    const r = await groq('/chat/completions', key, { model, messages: msgs, temperature: 0.6, max_tokens: 220 });
    if (!r.ok) { cachedModel = process.env.GROQ_MODEL || ''; return res.status(502).json({ error: 'Groq ' + r.status, model }); }
    const d = await r.json();
    const text = ((((d.choices || [])[0] || {}).message || {}).content || '')
      .replace(/<think>[\s\S]*?(<\/think>|$)/gi, '')
      .replace(/^\s*\[(planning|developer|residents)\]\s*/i, '')
      .trim();
    return res.status(200).json({ text });
  } catch (e) {
    return res.status(502).json({ error: 'AI request failed' });
  }
};

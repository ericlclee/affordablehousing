// Server-side AI for the agents chat. index.html POSTs { agent, messages, system } here when no
// browser key is connected. The Groq key lives only in the Vercel env var GROQ_API_KEY.
const BASE = 'https://api.groq.com/openai/v1';
const PREFER = [/qwen/i, /kimi/i, /llama-3\.3/i, /gpt-oss/i, /llama/i];  // same order as the Connect AI panel
let cachedModel = process.env.GROQ_MODEL || '';

async function pickModel(key) {
  if (cachedModel) return cachedModel;
  const r = await fetch(BASE + '/models', { headers: { Authorization: 'Bearer ' + key } });
  if (!r.ok) throw new Error('models ' + r.status);
  const ids = ((await r.json()).data || []).filter(m => m.active !== false).map(m => m.id)
    .filter(id => !/whisper|tts|guard|embed|vision|prompt/i.test(id));
  for (const re of PREFER) { const hit = ids.find(id => re.test(id)); if (hit) return (cachedModel = hit); }
  return (cachedModel = ids[0]);
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
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
    const r = await fetch(BASE + '/chat/completions', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + key, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages: msgs, temperature: 0.6, max_tokens: 220 })
    });
    if (!r.ok) { cachedModel = process.env.GROQ_MODEL || ''; return res.status(502).json({ error: 'Groq ' + r.status, model }); }
    const d = await r.json();
    const text = ((((d.choices || [])[0] || {}).message || {}).content || '')
      .replace(/<think>[\s\S]*?<\/think>/gi, '')
      .replace(/^\s*\[(planning|developer|residents)\]\s*/i, '')
      .trim();
    return res.status(200).json({ text });
  } catch (e) {
    return res.status(502).json({ error: 'AI request failed' });
  }
};

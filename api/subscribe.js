// Labor Vector email signup (2026-10-29), the same code as machinemediation.org's and provenanceerasure.org's, writing to the same private store (mmrs-subscribers) with site "laborvector". Stores one private record per signup in the project's Vercel Blob store
// (private access: no URL serves it; only code holding BLOB_READ_WRITE_TOKEN can read it). Nothing is published.
const { put } = require('@vercel/blob');
const crypto = require('crypto');

const EMAIL = /^[^\s@<>()\[\],;:"]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,24}$/;
const SLUG = /^[a-z0-9-]{1,80}$/;

module.exports = async (req, res) => {
  const wantsJson = String(req.headers.accept || '').includes('application/json');
  const reply = (code, msg) => {
    if (wantsJson) return res.status(code).json(msg);
    if (code === 200) { res.statusCode = 303; res.setHeader('Location', '/subscribed'); return res.end(); }
    res.status(code).setHeader('Content-Type', 'text/plain; charset=utf-8'); return res.end(msg.error || 'Error');
  };
  if (req.method !== 'POST') { res.setHeader('Allow', 'POST'); return reply(405, { error: 'POST only' }); }
  const b = req.body || {};
  if (b.website) return reply(200, { ok: true });             // the hidden trap field: bots fill it, people never see it
  const email = String(b.email || '').trim().toLowerCase();
  if (email.length > 254 || !EMAIL.test(email)) return reply(400, { error: 'That email address does not look right.' });
  if (!(b.consent === 'yes' || b.consent === true || b.consent === 'on')) return reply(400, { error: 'Tick the box to agree to the emails.' });
  const follow = b.follow && SLUG.test(String(b.follow)) ? String(b.follow) : null;
  const at = new Date().toISOString();
  const id = crypto.createHash('sha256').update(email).digest('hex').slice(0, 32);
  const record = { email, site: 'laborvector', list: follow ? 'follow' : 'digest', follow, consent: true, at,
                   page: String(b.page || '').slice(0, 200) };
  try {
    await put(`subscribers/${id}/${at.replace(/[:.]/g, '-')}.json`, JSON.stringify(record), {
      access: 'private', contentType: 'application/json', addRandomSuffix: true });
  } catch (e) {
    console.error('signup store failed', e && e.message);
    return reply(503, { error: 'The signup could not be saved just now. Please try again later.' });
  }
  return reply(200, { ok: true });
};

import express from 'express';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 3000);
const BACKEND_URL = (process.env.BACKEND_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
const MBTA_API_BASE = 'https://api-v3.mbta.com';
const MBTA_API_KEY = process.env.MBTA_API_KEY || '';
const DIST = path.join(__dirname, 'dist');
const SETTINGS_PATH = process.env.TRAINS_SETTINGS_PATH || path.join(__dirname, 'data', 'visibility.json');

/** South Side CR route allowlist (must match the frontend). */
const SOUTH_SIDE_ROUTES = [
  'CR-Fairmount',
  'CR-Foxboro',
  'CR-Franklin',
  'CR-Greenbush',
  'CR-Kingston',
  'CR-Needham',
  'CR-NewBedford',
  'CR-Providence',
  'CR-Worcester',
];

const app = express();
app.set('strict routing', true);
app.use(express.json({ limit: '32kb' }));

app.get('/health', (_req, res) => {
  res.type('text').send('ok');
});

async function readVisibility() {
  try {
    const raw = await fs.readFile(SETTINGS_PATH, 'utf8');
    const parsed = JSON.parse(raw);
    const ids = Array.isArray(parsed.routeIds) ? parsed.routeIds : [];
    const filtered = ids.filter((id) => SOUTH_SIDE_ROUTES.includes(id));
    if (!filtered.length) return [...SOUTH_SIDE_ROUTES];
    return filtered;
  } catch (err) {
    if (err && err.code === 'ENOENT') return [...SOUTH_SIDE_ROUTES];
    console.error('read visibility failed', err);
    return [...SOUTH_SIDE_ROUTES];
  }
}

async function writeVisibility(routeIds) {
  await fs.mkdir(path.dirname(SETTINGS_PATH), { recursive: true });
  const payload = {
    routeIds,
    updatedAt: new Date().toISOString(),
  };
  await fs.writeFile(SETTINGS_PATH, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
  return payload;
}

async function requireAuth(req, res, next) {
  if (!req.path.startsWith('/trains')) return next();

  try {
    const cookie = req.headers.cookie || '';
    const probe = await fetch(`${BACKEND_URL}/api/auth/me/`, {
      headers: { cookie, accept: 'application/json' },
      redirect: 'manual',
    });
    if (probe.status === 401 || probe.status === 403) {
      if (req.path.startsWith('/trains/api/') || req.headers.accept?.includes('application/json')) {
        return res.status(401).json({ detail: 'Authentication required' });
      }
      return res.redirect(302, '/login');
    }
    if (!probe.ok) {
      return res.status(502).json({ detail: 'Auth service unavailable' });
    }
    const me = await probe.json();
    req.trainsUser = { username: me.username, role: me.role };
    return next();
  } catch (err) {
    console.error('auth probe failed', err);
    return res.status(502).json({ detail: 'Auth service unavailable' });
  }
}

app.use(requireAuth);

app.get('/trains/api/session', (req, res) => {
  res.json(req.trainsUser || { username: null, role: null });
});

app.get('/trains/api/visibility', async (_req, res) => {
  const routeIds = await readVisibility();
  res.json({ routeIds, availableRouteIds: SOUTH_SIDE_ROUTES });
});

app.put('/trains/api/visibility', async (req, res) => {
  if (req.trainsUser?.role !== 'dm') {
    return res.status(403).json({ detail: 'Only the DM can change visible routes' });
  }
  const incoming = req.body?.routeIds;
  if (!Array.isArray(incoming)) {
    return res.status(400).json({ detail: 'routeIds must be an array' });
  }
  const routeIds = [...new Set(incoming.map(String))].filter((id) => SOUTH_SIDE_ROUTES.includes(id));
  if (!routeIds.length) {
    return res.status(400).json({ detail: 'Select at least one south-side route' });
  }
  const saved = await writeVisibility(routeIds);
  return res.json(saved);
});

app.use('/trains/api/mbta', async (req, res) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    return res.status(405).json({ detail: 'Method not allowed' });
  }

  const mbtaPath = req.path.replace(/^\/+/, '');
  if (!mbtaPath || mbtaPath.includes('..')) {
    return res.status(400).json({ detail: 'Invalid MBTA path' });
  }

  const q = req.url.includes('?') ? req.url.slice(req.url.indexOf('?') + 1) : '';
  const upstream = new URL(`${MBTA_API_BASE}/${mbtaPath}${q ? `?${q}` : ''}`);

  const headers = {
    accept: 'application/vnd.api+json',
    'user-agent': 'npc-catalog-trains/1.0',
  };
  if (MBTA_API_KEY) headers['x-api-key'] = MBTA_API_KEY;

  try {
    const upstreamRes = await fetch(upstream, { headers });
    const body = Buffer.from(await upstreamRes.arrayBuffer());
    res.status(upstreamRes.status);
    const contentType = upstreamRes.headers.get('content-type');
    if (contentType) res.setHeader('content-type', contentType);
    res.setHeader('cache-control', 'private, max-age=30');
    return res.send(body);
  } catch (err) {
    console.error('mbta proxy failed', err);
    return res.status(502).json({ detail: 'MBTA upstream unavailable' });
  }
});

app.get('/trains', (_req, res) => {
  res.redirect(302, '/trains/');
});

app.use(
  '/trains/',
  express.static(DIST, {
    index: 'index.html',
    fallthrough: false,
  }),
);

app.listen(PORT, '0.0.0.0', () => {
  console.log(`trains listening on :${PORT} (auth via ${BACKEND_URL})`);
});

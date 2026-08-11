/** South Side MBTA Commuter Rail route IDs (type 2). */
export const SOUTH_SIDE_ROUTES = [
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

export const ROUTE_COLORS = {
  'CR-Fairmount': '#80276c',
  'CR-Foxboro': '#b34d8e',
  'CR-Franklin': '#6b2d5c',
  'CR-Greenbush': '#00843d',
  'CR-Kingston': '#1a6b4a',
  'CR-Needham': '#c44d2a',
  'CR-NewBedford': '#0b3d91',
  'CR-Providence': '#5c2d91',
  'CR-Worcester': '#003da5',
};

const API_BASE = '/trains/api/mbta';

export async function mbtaFetch(path, params = {}) {
  const url = new URL(`${API_BASE}/${path.replace(/^\//, '')}`, window.location.origin);
  for (const [key, value] of Object.entries(params)) {
    if (value == null || value === '') continue;
    url.searchParams.set(key, String(value));
  }
  const res = await fetch(url.toString(), { credentials: 'same-origin' });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    throw new Error(`MBTA proxy ${res.status}: ${path}`);
  }
  return res.json();
}

/** Decode Google encoded polyline into [lat, lon] pairs. */
export function decodePolyline(encoded) {
  if (!encoded) return [];
  let index = 0;
  const len = encoded.length;
  let lat = 0;
  let lng = 0;
  const coordinates = [];

  while (index < len) {
    let b;
    let shift = 0;
    let result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlat = result & 1 ? ~(result >> 1) : result >> 1;
    lat += dlat;

    shift = 0;
    result = 0;
    do {
      b = encoded.charCodeAt(index++) - 63;
      result |= (b & 0x1f) << shift;
      shift += 5;
    } while (b >= 0x20);
    const dlng = result & 1 ? ~(result >> 1) : result >> 1;
    lng += dlng;

    coordinates.push([lat / 1e5, lng / 1e5]);
  }
  return coordinates;
}

export function indexIncluded(payload) {
  const map = new Map();
  for (const item of payload.included || []) {
    map.set(`${item.type}:${item.id}`, item);
  }
  return map;
}

export function getRel(resource, name) {
  return resource?.relationships?.[name]?.data ?? null;
}

export function lookup(included, ref) {
  if (!ref) return null;
  return included.get(`${ref.type}:${ref.id}`) ?? null;
}

/** Today's date in America/New_York as YYYY-MM-DD. */
export function bostonDate(now = new Date()) {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/New_York',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(now);
}

export function parseTime(iso) {
  if (!iso) return null;
  const t = Date.parse(iso);
  return Number.isNaN(t) ? null : t;
}

export function formatClock(ms) {
  if (ms == null) return '—';
  return new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(ms));
}

export function minutesUntil(ms, now = Date.now()) {
  if (ms == null) return null;
  return Math.round((ms - now) / 60000);
}

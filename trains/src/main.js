import {
  loadNetwork,
  loadSchedules,
  estimateTrainPosition,
  buildArrivalBoard,
} from './data.js';
import { createMap, drawNetwork, drawTrains } from './map.js';
import { SOUTH_SIDE_ROUTES, formatClock, minutesUntil } from './mbta.js';
import './style.css';

const SCHEDULE_REFRESH_MS = 5 * 60 * 1000;
const POSITION_TICK_MS = 15_000;
const VISIBILITY_POLL_MS = 30_000;

const els = {
  clock: document.getElementById('clock'),
  status: document.getElementById('refresh-status'),
  arrivals: document.getElementById('arrivals'),
  visibilityList: document.getElementById('route-visibility-list'),
  visibilityNote: document.getElementById('route-visibility-note'),
};

let network = null;
let trips = new Map();
let session = { username: null, role: null };
/** @type {Set<string>} */
let visibleRouteIds = new Set(SOUTH_SIDE_ROUTES);
let visibilitySignature = '';
let savingVisibility = false;

const { map, layers } = createMap('map');

function setStatus(text, isError = false) {
  els.status.textContent = text;
  els.status.classList.toggle('error', isError);
}

function tickClock() {
  els.clock.textContent = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    weekday: 'short',
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit',
  }).format(new Date());
}

async function apiJson(url, options = {}) {
  const res = await fetch(url, {
    credentials: 'same-origin',
    ...options,
    headers: {
      accept: 'application/json',
      ...(options.body ? { 'content-type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

function signatureFor(ids) {
  return [...ids].sort().join(',');
}

function applyVisibility(routeIds, { refreshSchedules: shouldRefresh } = { refreshSchedules: true }) {
  const next = new Set(
    (routeIds?.length ? routeIds : SOUTH_SIDE_ROUTES).filter((id) => SOUTH_SIDE_ROUTES.includes(id)),
  );
  if (!next.size) {
    for (const id of SOUTH_SIDE_ROUTES) next.add(id);
  }
  const nextSig = signatureFor(next);
  const changed = nextSig !== visibilitySignature;
  visibleRouteIds = next;
  visibilitySignature = nextSig;
  renderVisibilityControls();
  if (network) {
    drawNetwork(layers, network, visibleRouteIds);
    fitVisibleBounds();
  }
  renderBoard();
  renderTrainIcons();
  if (changed && shouldRefresh) {
    void refreshSchedules();
  }
  return changed;
}

function fitVisibleBounds() {
  if (!network) return;
  const bounds = [];
  for (const [routeId, shapes] of network.shapesByRoute.entries()) {
    if (!visibleRouteIds.has(routeId)) continue;
    for (const shape of shapes) bounds.push(...shape.polyline);
  }
  if (bounds.length) map.fitBounds(bounds, { padding: [24, 24] });
}

function renderVisibilityControls() {
  if (!network) return;
  const isDm = session.role === 'dm';
  els.visibilityNote.hidden = isDm;
  els.visibilityNote.textContent = isDm
    ? ''
    : 'Visible lines are set by the DM.';

  const sorted = [...network.routes.values()].sort((a, b) => a.name.localeCompare(b.name));
  els.visibilityList.innerHTML = '';
  for (const route of sorted) {
    const id = `route-${route.id}`;
    const label = document.createElement('label');
    label.className = 'route-toggle';
    label.htmlFor = id;

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = id;
    input.value = route.id;
    input.checked = visibleRouteIds.has(route.id);
    input.disabled = !isDm || savingVisibility;
    input.addEventListener('change', () => {
      void onVisibilityToggle();
    });

    const swatch = document.createElement('span');
    swatch.className = 'route-swatch';
    swatch.style.background = route.color;

    const text = document.createElement('span');
    text.textContent = route.name;

    label.append(input, swatch, text);
    els.visibilityList.appendChild(label);
  }
}

async function onVisibilityToggle() {
  if (session.role !== 'dm' || savingVisibility) return;
  const checked = [...els.visibilityList.querySelectorAll('input[type="checkbox"]:checked')].map(
    (el) => el.value,
  );
  if (!checked.length) {
    renderVisibilityControls();
    setStatus('Keep at least one line visible', true);
    return;
  }

  savingVisibility = true;
  renderVisibilityControls();
  try {
    const saved = await apiJson('/trains/api/visibility', {
      method: 'PUT',
      body: JSON.stringify({ routeIds: checked }),
    });
    applyVisibility(saved.routeIds, { refreshSchedules: true });
    setStatus('Visible lines updated');
  } catch (err) {
    console.error(err);
    setStatus(err.message || 'Could not save visible lines', true);
    await loadVisibility({ refreshSchedules: false });
  } finally {
    savingVisibility = false;
    renderVisibilityControls();
  }
}

async function loadVisibility({ refreshSchedules: shouldRefresh } = { refreshSchedules: true }) {
  const data = await apiJson('/trains/api/visibility');
  return applyVisibility(data.routeIds, { refreshSchedules: shouldRefresh });
}

async function pollVisibility() {
  if (savingVisibility) return;
  try {
    const data = await apiJson('/trains/api/visibility');
    applyVisibility(data.routeIds, { refreshSchedules: true });
  } catch (err) {
    console.error(err);
  }
}

function renderBoard() {
  const now = Date.now();
  const rows = buildArrivalBoard(trips, now, visibleRouteIds);
  els.arrivals.innerHTML = '';
  if (!rows.length) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = 'No upcoming arrivals for the visible lines.';
    els.arrivals.appendChild(empty);
    return;
  }

  for (const row of rows) {
    const route = network.routes.get(row.routeId);
    const li = document.createElement('li');
    li.className = 'arrival';
    const mins = minutesUntil(row.when, now);
    const eta =
      mins == null ? '—' : mins <= 0 ? 'Due' : mins === 1 ? '1 min' : `${mins} min`;
    li.innerHTML = `
      <div class="arrival-line" style="--route-color:${route?.color || '#80276c'}">
        <span class="swatch" aria-hidden="true"></span>
        <div class="arrival-text">
          <div class="arrival-primary">
            <strong>${row.stopName}</strong>
            <span class="eta">${eta}</span>
          </div>
          <div class="arrival-secondary">
            <span>${route?.name || row.routeId}</span>
            <span>·</span>
            <span>${row.headsign || row.tripName}</span>
            <span>·</span>
            <span>${formatClock(row.when)}${row.predicted ? ' live' : ''}</span>
          </div>
        </div>
      </div>
    `;
    els.arrivals.appendChild(li);
  }
}

function renderTrainIcons() {
  if (!network) return;
  const now = Date.now();
  const positions = [];
  for (const trip of trips.values()) {
    if (!visibleRouteIds.has(trip.routeId)) continue;
    const pos = estimateTrainPosition(trip, now);
    if (pos) positions.push(pos);
  }
  drawTrains(layers, positions, network.routes);
}

async function refreshSchedules() {
  if (!network) return;
  setStatus('Refreshing schedules…');
  try {
    trips = await loadSchedules(network.stops, [...visibleRouteIds]);
    const at = new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/New_York',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date());
    setStatus(`Schedules updated ${at} · next in 5 min`);
    renderBoard();
    renderTrainIcons();
  } catch (err) {
    console.error(err);
    setStatus(err.message || 'Schedule refresh failed', true);
  }
}

async function boot() {
  tickClock();
  setInterval(tickClock, 1000);

  setStatus('Loading routes & shapes…');
  try {
    session = await apiJson('/trains/api/session');
    network = await loadNetwork();
    await loadVisibility({ refreshSchedules: false });
    drawNetwork(layers, network, visibleRouteIds);
    fitVisibleBounds();
    await refreshSchedules();
  } catch (err) {
    console.error(err);
    setStatus(err.message || 'Failed to load network', true);
    return;
  }

  setInterval(refreshSchedules, SCHEDULE_REFRESH_MS);
  setInterval(pollVisibility, VISIBILITY_POLL_MS);
  setInterval(() => {
    renderBoard();
    renderTrainIcons();
  }, POSITION_TICK_MS);
}

boot();

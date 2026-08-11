import {
  loadNetwork,
  loadSchedules,
  estimateTrainPosition,
  buildArrivalBoard,
} from './data.js';
import { createMap, drawNetwork, drawTrains } from './map.js';
import { formatClock, minutesUntil } from './mbta.js';
import './style.css';

const SCHEDULE_REFRESH_MS = 5 * 60 * 1000;
const POSITION_TICK_MS = 15_000;

const els = {
  clock: document.getElementById('clock'),
  status: document.getElementById('refresh-status'),
  arrivals: document.getElementById('arrivals'),
  routeFilter: document.getElementById('route-filter'),
};

let network = null;
let trips = new Map();
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

function populateRouteFilter(routes) {
  const current = els.routeFilter.value;
  els.routeFilter.innerHTML = '<option value="">All south side</option>';
  const sorted = [...routes.values()].sort((a, b) => a.name.localeCompare(b.name));
  for (const route of sorted) {
    const opt = document.createElement('option');
    opt.value = route.id;
    opt.textContent = route.name;
    els.routeFilter.appendChild(opt);
  }
  els.routeFilter.value = current;
}

function renderBoard() {
  const now = Date.now();
  const rows = buildArrivalBoard(trips, now, els.routeFilter.value);
  els.arrivals.innerHTML = '';
  if (!rows.length) {
    const empty = document.createElement('li');
    empty.className = 'empty';
    empty.textContent = 'No upcoming south-side arrivals in the current schedule window.';
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
    if (els.routeFilter.value && trip.routeId !== els.routeFilter.value) continue;
    const pos = estimateTrainPosition(trip, now);
    if (pos) positions.push(pos);
  }
  drawTrains(layers, positions, network.routes);
}

async function refreshSchedules() {
  if (!network) return;
  setStatus('Refreshing schedules…');
  try {
    trips = await loadSchedules(network.stops);
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
    network = await loadNetwork();
    populateRouteFilter(network.routes);
    drawNetwork(layers, network);

    const bounds = [];
    for (const shapes of network.shapesByRoute.values()) {
      for (const shape of shapes) bounds.push(...shape.polyline);
    }
    if (bounds.length) map.fitBounds(bounds, { padding: [24, 24] });

    await refreshSchedules();
  } catch (err) {
    console.error(err);
    setStatus(err.message || 'Failed to load network', true);
    return;
  }

  els.routeFilter.addEventListener('change', () => {
    renderBoard();
    renderTrainIcons();
  });

  setInterval(refreshSchedules, SCHEDULE_REFRESH_MS);
  setInterval(() => {
    renderBoard();
    renderTrainIcons();
  }, POSITION_TICK_MS);
}

boot();

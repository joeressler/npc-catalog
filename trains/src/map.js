import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { ROUTE_COLORS } from './mbta.js';

// Vite-friendly default marker assets (we use divIcons for trains).
delete L.Icon.Default.prototype._getIconUrl;

/**
 * Create the Leaflet map and draw CR shapes + stop dots.
 */
export function createMap(containerId) {
  const map = L.map(containerId, {
    zoomControl: true,
    attributionControl: true,
  }).setView([42.24, -71.12], 10);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    maxZoom: 19,
  }).addTo(map);

  const layers = {
    routes: L.layerGroup().addTo(map),
    stops: L.layerGroup().addTo(map),
    trains: L.layerGroup().addTo(map),
  };

  return { map, layers };
}

export function drawNetwork(layers, { routes, shapesByRoute, stops }) {
  layers.routes.clearLayers();
  layers.stops.clearLayers();

  for (const [routeId, shapes] of shapesByRoute.entries()) {
    const color = routes.get(routeId)?.color || ROUTE_COLORS[routeId] || '#80276c';
    for (const shape of shapes) {
      L.polyline(shape.polyline, {
        color,
        weight: 3,
        opacity: 0.75,
        lineJoin: 'round',
      }).addTo(layers.routes);
    }
  }

  // Prefer parent-station points; fall back to child platforms when needed.
  const seen = new Set();
  const byParent = new Map();
  for (const stop of stops.values()) {
    const key = stop.parentStation || stop.id;
    if (!byParent.has(key)) byParent.set(key, stop);
  }
  for (const stop of byParent.values()) {
    const dedupe = `${stop.name}|${stop.lat.toFixed(3)}|${stop.lon.toFixed(3)}`;
    if (seen.has(dedupe)) continue;
    seen.add(dedupe);
    L.circleMarker([stop.lat, stop.lon], {
      radius: 3,
      color: '#e8eef7',
      weight: 1,
      fillColor: '#1a2332',
      fillOpacity: 0.9,
    })
      .bindTooltip(stop.name, { direction: 'top', opacity: 0.9 })
      .addTo(layers.stops);
  }
}

function trainIcon(routeColor, label) {
  return L.divIcon({
    className: 'train-marker',
    html: `<div class="train-icon" style="--train-color:${routeColor}" title="${label}">
      <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
        <path fill="#fff" d="M12 2c-4 0-7 1.2-7 4v9c0 1.7 1.3 3 3 3l-1.5 2h2.2l1.3-2h3l1.3 2h2.2L16 18c1.7 0 3-1.3 3-3V6c0-2.8-3-4-7-4zm-3.5 14a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm7 0a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zM7 11V7h10v4H7z"/>
      </svg>
    </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

export function drawTrains(layers, positions, routes) {
  layers.trains.clearLayers();
  for (const pos of positions) {
    const route = routes.get(pos.routeId);
    const color = route?.color || ROUTE_COLORS[pos.routeId] || '#80276c';
    const label = `${route?.name || pos.routeId} · ${pos.headsign || pos.tripId}`;
    const marker = L.marker([pos.lat, pos.lon], {
      icon: trainIcon(color, label),
      zIndexOffset: 500,
    }).bindTooltip(
      `<strong>${label}</strong><br/>${
        pos.phase === 'dwell'
          ? `At ${pos.atStop?.name || 'stop'}`
          : `Toward ${pos.nextStop?.name || 'next stop'}`
      }`,
      { direction: 'top' },
    );
    marker.addTo(layers.trains);
  }
}

import {
  SOUTH_SIDE_ROUTES,
  decodePolyline,
  indexIncluded,
  getRel,
  lookup,
  parseTime,
  mbtaFetch,
  bostonDate,
} from './mbta.js';

/**
 * Load route metadata + shape polylines for south-side CR lines.
 * Shapes are cached for the page lifetime; schedules refresh separately.
 */
export async function loadNetwork() {
  const routeFilter = SOUTH_SIDE_ROUTES.join(',');
  const [routesPayload, shapesPayload, stopsPayload] = await Promise.all([
    mbtaFetch('routes', { 'filter[id]': routeFilter }),
    mbtaFetch('shapes', { 'filter[route]': routeFilter }),
    mbtaFetch('stops', {
      'filter[route]': routeFilter,
      'filter[route_type]': '2',
    }),
  ]);

  const routes = new Map();
  for (const route of routesPayload.data || []) {
    routes.set(route.id, {
      id: route.id,
      name: route.attributes.long_name || route.attributes.short_name || route.id,
      color: `#${route.attributes.color || '80276c'}`,
      textColor: `#${route.attributes.text_color || 'ffffff'}`,
      directionNames: route.attributes.direction_names || ['Outbound', 'Inbound'],
      directionDestinations: route.attributes.direction_destinations || [],
    });
  }

  const shapesByRoute = new Map();
  for (const shape of shapesPayload.data || []) {
    const routeRef = getRel(shape, 'route');
    const routeId = routeRef?.id;
    if (!routeId || !routes.has(routeId)) continue;
    const polyline = decodePolyline(shape.attributes.polyline);
    if (polyline.length < 2) continue;
    if (!shapesByRoute.has(routeId)) shapesByRoute.set(routeId, []);
    shapesByRoute.get(routeId).push({
      id: shape.id,
      name: shape.attributes.name || shape.id,
      polyline,
    });
  }

  const stops = new Map();
  for (const stop of stopsPayload.data || []) {
    const attrs = stop.attributes;
    // Prefer parent stations / platforms with coordinates.
    if (attrs.latitude == null || attrs.longitude == null) continue;
    stops.set(stop.id, {
      id: stop.id,
      name: attrs.name,
      lat: attrs.latitude,
      lon: attrs.longitude,
      platformCode: attrs.platform_code,
      parentStation: getRel(stop, 'parent_station')?.id || null,
    });
  }

  return { routes, shapesByRoute, stops };
}

/**
 * Pull today's schedules for south-side routes and build trip timelines.
 */
export async function loadSchedules(stops) {
  const routeFilter = SOUTH_SIDE_ROUTES.join(',');
  const now = new Date();
  const date = bostonDate(now);
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(now);
  const hour = Number(parts.find((p) => p.type === 'hour')?.value || 0);
  const minute = Number(parts.find((p) => p.type === 'minute')?.value || 0);
  const minsNow = hour * 60 + minute;
  const minTime = formatHhMm(Math.max(0, minsNow - 45));
  const maxTime = formatHhMm(Math.min(24 * 60 - 1, minsNow + 180));

  const pages = [];
  let offset = 0;
  const pageLimit = 500;
  for (;;) {
    const page = await mbtaFetch('schedules', {
      'filter[route]': routeFilter,
      'filter[date]': date,
      'filter[min_time]': minTime,
      'filter[max_time]': maxTime,
      include: 'trip,stop,prediction,route',
      sort: 'departure_time',
      'page[limit]': String(pageLimit),
      'page[offset]': String(offset),
    });
    pages.push(page);
    const got = page.data?.length || 0;
    if (got < pageLimit) break;
    offset += pageLimit;
    if (offset > 5000) break;
  }

  return buildTripModel(mergeJsonApiPages(pages), stops);
}

function formatHhMm(totalMinutes) {
  const h = Math.floor(totalMinutes / 60);
  const m = totalMinutes % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function mergeJsonApiPages(pages) {
  const data = [];
  const included = [];
  const seenIncluded = new Set();
  for (const page of pages) {
    data.push(...(page.data || []));
    for (const item of page.included || []) {
      const key = `${item.type}:${item.id}`;
      if (seenIncluded.has(key)) continue;
      seenIncluded.add(key);
      included.push(item);
    }
  }
  return { data, included };
}

function buildTripModel(payload, stopsCatalog) {
  const included = indexIncluded(payload);
  /** @type {Map<string, {id:string, routeId:string, headsign:string, directionId:number, name:string, stops:Array}>} */
  const trips = new Map();

  for (const sched of payload.data || []) {
    const tripRef = getRel(sched, 'trip');
    const routeRef = getRel(sched, 'route');
    const stopRef = getRel(sched, 'stop');
    if (!tripRef || !routeRef || !stopRef) continue;

    const trip = lookup(included, tripRef);
    const stop = lookup(included, stopRef) || null;
    const prediction = lookup(included, getRel(sched, 'prediction'));

    let tripState = trips.get(tripRef.id);
    if (!tripState) {
      tripState = {
        id: tripRef.id,
        routeId: routeRef.id,
        headsign: trip?.attributes?.headsign || '',
        directionId: trip?.attributes?.direction_id ?? sched.attributes.direction_id,
        name: trip?.attributes?.name || tripRef.id,
        stops: [],
      };
      trips.set(tripRef.id, tripState);
    }

    const stopId = stopRef.id;
    const catalog = stopsCatalog.get(stopId);
    const stopAttrs = stop?.attributes;
    const lat = catalog?.lat ?? stopAttrs?.latitude ?? null;
    const lon = catalog?.lon ?? stopAttrs?.longitude ?? null;
    const name = catalog?.name || stopAttrs?.name || stopId;

    const arrival = parseTime(prediction?.attributes?.arrival_time) ?? parseTime(sched.attributes.arrival_time);
    const departure =
      parseTime(prediction?.attributes?.departure_time) ?? parseTime(sched.attributes.departure_time);
    const status = prediction?.attributes?.status || null;
    const scheduleRelationship = prediction?.attributes?.schedule_relationship || null;

    tripState.stops.push({
      stopId,
      name,
      lat,
      lon,
      stopSequence: sched.attributes.stop_sequence,
      arrival,
      departure,
      status,
      scheduleRelationship,
      predicted: Boolean(prediction),
    });
  }

  for (const trip of trips.values()) {
    trip.stops.sort((a, b) => a.stopSequence - b.stopSequence);
  }

  return trips;
}

/**
 * Estimate where a trip should be right now from its schedule timeline.
 * Returns null if the trip is not currently active.
 */
export function estimateTrainPosition(trip, now = Date.now()) {
  const stops = trip.stops.filter((s) => s.lat != null && s.lon != null);
  if (stops.length < 2) return null;

  const firstDep = stops[0].departure ?? stops[0].arrival;
  const lastArr = stops[stops.length - 1].arrival ?? stops[stops.length - 1].departure;
  if (firstDep == null || lastArr == null) return null;
  if (now < firstDep || now > lastArr + 2 * 60 * 1000) return null;

  // Dwelling at a stop.
  for (const stop of stops) {
    const arr = stop.arrival;
    const dep = stop.departure;
    if (arr != null && dep != null && now >= arr && now <= dep) {
      return {
        tripId: trip.id,
        routeId: trip.routeId,
        headsign: trip.headsign,
        lat: stop.lat,
        lon: stop.lon,
        phase: 'dwell',
        atStop: stop,
        nextStop: null,
        progress: 0,
      };
    }
  }

  for (let i = 0; i < stops.length - 1; i++) {
    const a = stops[i];
    const b = stops[i + 1];
    const start = a.departure ?? a.arrival;
    const end = b.arrival ?? b.departure;
    if (start == null || end == null || end <= start) continue;
    if (now < start || now > end) continue;
    const progress = (now - start) / (end - start);
    return {
      tripId: trip.id,
      routeId: trip.routeId,
      headsign: trip.headsign,
      lat: a.lat + (b.lat - a.lat) * progress,
      lon: a.lon + (b.lon - a.lon) * progress,
      phase: 'enroute',
      atStop: a,
      nextStop: b,
      progress,
    };
  }

  return null;
}

/**
 * Flat arrival board rows for stops still ahead of now.
 */
export function buildArrivalBoard(trips, now = Date.now(), routeFilter = '') {
  const rows = [];
  for (const trip of trips.values()) {
    if (routeFilter && trip.routeId !== routeFilter) continue;
    for (const stop of trip.stops) {
      const when = stop.arrival ?? stop.departure;
      if (when == null || when < now - 60_000) continue;
      rows.push({
        tripId: trip.id,
        routeId: trip.routeId,
        headsign: trip.headsign,
        tripName: trip.name,
        stopId: stop.stopId,
        stopName: stop.name,
        when,
        predicted: stop.predicted,
        status: stop.status,
        directionId: trip.directionId,
      });
    }
  }
  rows.sort((a, b) => a.when - b.when);
  return rows.slice(0, 120);
}

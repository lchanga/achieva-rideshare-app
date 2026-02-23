/* global L */

import { optimizeTours } from "./api.js";

let currentRequest = null;

function $(id) {
  return document.getElementById(id);
}

function toRfc3339Z(datetimeLocalValue) {
  // datetime-local returns "YYYY-MM-DDTHH:mm" (local time).
  // Convert to Zulu RFC3339 via Date -> toISOString().
  if (!datetimeLocalValue) return null;
  const d = new Date(datetimeLocalValue);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString();
}

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function shipmentRowTemplate(index, initial = {}) {
  const label = initial.label ?? `rider_${index + 1}`;
  return `
    <div class="shipment" data-index="${index}">
      <div class="shipmentHeader">
        <h4 class="shipmentTitle">Shipment ${index + 1}</h4>
        <button class="btnSecondary danger" type="button" data-action="removeShipment">Remove</button>
      </div>

      <div class="grid2">
        <div class="field">
          <label>Shipment label</label>
          <input type="text" data-field="label" value="${label}" required />
        </div>
        <div class="field help">
          <label>Rules</label>
          <div class="helpText">Fake optimizer orders by pickup time windows, then deliveries.</div>
        </div>
      </div>

      <div class="divider"></div>
      <div class="row"><span class="sectionTitle">Pickup</span></div>

      <div class="grid2">
        <div class="field">
          <label>Pickup latitude</label>
          <input type="number" step="0.000001" data-field="pickupLat" value="${initial.pickupLat ?? 40.31}" required />
        </div>
        <div class="field">
          <label>Pickup longitude</label>
          <input type="number" step="0.000001" data-field="pickupLng" value="${initial.pickupLng ?? -79.54}" required />
        </div>
      </div>

      <div class="grid2">
        <div class="field">
          <label>Pickup window start</label>
          <input type="datetime-local" data-field="pickupStart" required />
        </div>
        <div class="field">
          <label>Pickup window end</label>
          <input type="datetime-local" data-field="pickupEnd" required />
        </div>
      </div>

      <div class="divider"></div>
      <div class="row"><span class="sectionTitle">Dropoff (delivery)</span></div>

      <div class="grid2">
        <div class="field">
          <label>Dropoff latitude</label>
          <input type="number" step="0.000001" data-field="dropoffLat" value="${initial.dropoffLat ?? 40.33}" required />
        </div>
        <div class="field">
          <label>Dropoff longitude</label>
          <input type="number" step="0.000001" data-field="dropoffLng" value="${initial.dropoffLng ?? -79.5}" required />
        </div>
      </div>

      <div class="grid2">
        <div class="field">
          <label>Dropoff window start</label>
          <input type="datetime-local" data-field="dropoffStart" required />
        </div>
        <div class="field">
          <label>Dropoff window end</label>
          <input type="datetime-local" data-field="dropoffEnd" required />
        </div>
      </div>
    </div>
  `;
}

function addShipment(initial) {
  const container = $("shipments");
  const index = container.children.length;
  const wrap = document.createElement("div");
  wrap.innerHTML = shipmentRowTemplate(index, initial);
  const node = wrap.firstElementChild;
  container.appendChild(node);
  return node;
}

function reindexShipments() {
  const container = $("shipments");
  [...container.children].forEach((el, idx) => {
    el.dataset.index = String(idx);
    const title = el.querySelector(".shipmentTitle");
    if (title) title.textContent = `Shipment ${idx + 1}`;
    const label = el.querySelector('[data-field="label"]');
    if (label && !label.value) label.value = `rider_${idx + 1}`;
  });
}

function buildOptimizeToursRequestFromForm() {
  const reqLabel = $("requestLabel").value.trim();
  const timeout = $("timeout").value;
  const globalStart = toRfc3339Z($("globalStart").value);
  const globalEnd = toRfc3339Z($("globalEnd").value);

  const vehicleLabel = $("vehicleLabel").value.trim();
  const vehicleStart = toRfc3339Z($("vehicleStart").value);
  const vehicleStartEnd = toRfc3339Z($("vehicleStartEnd").value);

  if (!globalStart || !globalEnd) throw new Error("Global start/end time is required.");
  if (!vehicleLabel) throw new Error("Vehicle label is required.");
  if (!vehicleStart || !vehicleStartEnd) throw new Error("Vehicle start window is required.");

  const shipmentEls = [...$("shipments").children];
  if (shipmentEls.length === 0) throw new Error("Add at least one shipment.");

  const shipments = shipmentEls.map((el) => {
    const label = el.querySelector('[data-field="label"]').value.trim();
    const pickupLat = num(el.querySelector('[data-field="pickupLat"]').value);
    const pickupLng = num(el.querySelector('[data-field="pickupLng"]').value);
    const pickupStart = toRfc3339Z(el.querySelector('[data-field="pickupStart"]').value);
    const pickupEnd = toRfc3339Z(el.querySelector('[data-field="pickupEnd"]').value);

    const dropoffLat = num(el.querySelector('[data-field="dropoffLat"]').value);
    const dropoffLng = num(el.querySelector('[data-field="dropoffLng"]').value);
    const dropoffStart = toRfc3339Z(el.querySelector('[data-field="dropoffStart"]').value);
    const dropoffEnd = toRfc3339Z(el.querySelector('[data-field="dropoffEnd"]').value);

    if (!label) throw new Error("Each shipment must have a label.");
    if (pickupLat === null || pickupLng === null) throw new Error("Pickup lat/lng is required.");
    if (!pickupStart || !pickupEnd) throw new Error("Pickup time window is required.");
    if (dropoffLat === null || dropoffLng === null) throw new Error("Dropoff lat/lng is required.");
    if (!dropoffStart || !dropoffEnd) throw new Error("Dropoff time window is required.");

    return {
      label,
      pickups: [
        {
          arrivalWaypoint: { location: { latLng: { latitude: pickupLat, longitude: pickupLng } } },
          timeWindows: [{ startTime: pickupStart, endTime: pickupEnd }],
        },
      ],
      deliveries: [
        {
          arrivalWaypoint: { location: { latLng: { latitude: dropoffLat, longitude: dropoffLng } } },
          timeWindows: [{ startTime: dropoffStart, endTime: dropoffEnd }],
        },
      ],
    };
  });

  const req = {
    timeout,
    ...(reqLabel ? { label: reqLabel } : {}),
    model: {
      globalStartTime: globalStart,
      globalEndTime: globalEnd,
      shipments,
      vehicles: [
        {
          label: vehicleLabel,
          startTimeWindows: [{ startTime: vehicleStart, endTime: vehicleStartEnd }],
        },
      ],
    },
  };

  return req;
}

function getLatLngFromVisit(visit) {
  const shipment = currentRequest?.model?.shipments?.[visit.shipmentIndex];
  if (!shipment) return null;
  const reqIndex = visit.visitRequestIndex ?? 0;
  const vr = visit.isPickup ? shipment.pickups?.[reqIndex] : shipment.deliveries?.[reqIndex];
  const ll = vr?.arrivalWaypoint?.location?.latLng;
  if (!ll) return null;
  return [ll.latitude, ll.longitude];
}

function formatVisitLabel(visit) {
  const shipment = currentRequest?.model?.shipments?.[visit.shipmentIndex];
  const who = shipment?.label ?? `shipment_${visit.shipmentIndex}`;
  const kind = visit.isPickup ? "Pickup" : "Dropoff";
  return `${kind}: ${who} @ ${visit.startTime}`;
}

async function runOptimizer() {
  const status = $("status");
  status.textContent = "Calling optimizer...";

  try {
    currentRequest = buildOptimizeToursRequestFromForm();
    $("request").textContent = JSON.stringify(currentRequest, null, 2);

    const json = await optimizeTours(currentRequest);
    status.textContent = "Success. Rendering map...";
    $("response").textContent = JSON.stringify(json, null, 2);
    return json;
  } catch (e) {
    status.textContent = `Error: ${e.message}`;
    $("response").textContent = JSON.stringify(e.data ?? { error: e.message }, null, 2);
    return null;
  }
}

function renderStopsList(optimizeResponse) {
  const list = $("stopsList");
  list.innerHTML = "";

  const route0 = optimizeResponse?.routes?.[0];
  const visits = route0?.visits ?? [];

  for (const v of visits) {
    const li = document.createElement("li");
    li.textContent = formatVisitLabel(v);
    list.appendChild(li);
  }

  if (visits.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No visits returned.";
    list.appendChild(li);
  }
}

function renderMap(optimizeResponse, mapState) {
  const route0 = optimizeResponse?.routes?.[0];
  const visits = route0?.visits ?? [];

  mapState.layers.forEach((layer) => mapState.map.removeLayer(layer));
  mapState.layers = [];

  const basePoints = [];
  const keyFor = (latlng) => `${latlng[0].toFixed(6)},${latlng[1].toFixed(6)}`;

  // First pass: collect points and count duplicates.
  const counts = new Map();
  const visitPoints = visits.map((visit) => {
    const latlng = getLatLngFromVisit(visit);
    if (!latlng) return null;
    const k = keyFor(latlng);
    counts.set(k, (counts.get(k) ?? 0) + 1);
    return latlng;
  });

  // Track how many we've placed for each coordinate key.
  const placed = new Map();

  function offsetLatLng(latlng, ordinal, total) {
    // If unique, no offset.
    if (total <= 1) return latlng;

    // Spread duplicates in a small circle around the true point.
    // Radius is in degrees; keep it small but visible at city-level zoom.
    const radiusDeg = 0.00045; // ~50m latitude-ish
    const angle = (2 * Math.PI * ordinal) / total;
    const lat = latlng[0];
    const lng = latlng[1];

    // Compensate longitude degrees by latitude so the circle is roughly round.
    const lngScale = Math.max(0.2, Math.cos((lat * Math.PI) / 180));
    const dLat = radiusDeg * Math.cos(angle);
    const dLng = (radiusDeg * Math.sin(angle)) / lngScale;
    return [lat + dLat, lng + dLng];
  }

  function numberedIcon(n) {
    return L.divIcon({
      className: "marker-badge-wrapper",
      html: `<div class="marker-badge">${n}</div>`,
      iconSize: [28, 28],
      iconAnchor: [14, 28],
      popupAnchor: [0, -24],
    });
  }

  visits.forEach((visit, idx) => {
    const latlng = visitPoints[idx];
    if (!latlng) return;

    const k = keyFor(latlng);
    const ord = placed.get(k) ?? 0;
    const total = counts.get(k) ?? 1;
    placed.set(k, ord + 1);

    const plotted = offsetLatLng(latlng, ord, total);
    basePoints.push(plotted);

    const marker = L.marker(plotted, { icon: numberedIcon(idx + 1) }).bindPopup(
      `<strong>${idx + 1}. ${visit.isPickup ? "Pickup" : "Dropoff"}</strong><br/>` +
        `${currentRequest?.model?.shipments?.[visit.shipmentIndex]?.label ?? ""}<br/>` +
        `<code>${visit.startTime}</code>`
    );
    marker.addTo(mapState.map);
    mapState.layers.push(marker);
  });

  if (basePoints.length >= 2) {
    const line = L.polyline(basePoints, { color: "#4c7dff", weight: 4, opacity: 0.9 });
    line.addTo(mapState.map);
    mapState.layers.push(line);
    mapState.map.fitBounds(line.getBounds().pad(0.25));
  } else if (basePoints.length === 1) {
    mapState.map.setView(basePoints[0], 13);
  }
}

function initMap() {
  const map = L.map("map", { zoomControl: true }).setView([40.31, -79.54], 12);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  return { map, layers: [] };
}

async function main() {
  const mapState = initMap();
  $("response").textContent = "Fill out inputs and click “Run optimizer”.";

  // Default times + 2 example shipments.
  const now = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  const toLocalInput = (d) =>
    `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;

  const day = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 7, 7, 0, 0);
  $("globalStart").value = toLocalInput(day);
  $("globalEnd").value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 19, 0, 0));
  $("vehicleStart").value = toLocalInput(day);
  $("vehicleStartEnd").value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 7, 15, 0));

  const s1 = addShipment({ label: "rider_1", pickupLat: 40.31, pickupLng: -79.54, dropoffLat: 40.33, dropoffLng: -79.5 });
  s1.querySelector('[data-field="pickupStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 8, 0, 0));
  s1.querySelector('[data-field="pickupEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 9, 0, 0));
  s1.querySelector('[data-field="dropoffStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 10, 0, 0));
  s1.querySelector('[data-field="dropoffEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 11, 0, 0));

  const s2 = addShipment({ label: "rider_2", pickupLat: 40.3, pickupLng: -79.55, dropoffLat: 40.33, dropoffLng: -79.5 });
  s2.querySelector('[data-field="pickupStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 8, 15, 0));
  s2.querySelector('[data-field="pickupEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 9, 15, 0));
  s2.querySelector('[data-field="dropoffStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 10, 0, 0));
  s2.querySelector('[data-field="dropoffEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 11, 30, 0));

  reindexShipments();

  $("addShipmentBtn").addEventListener("click", () => {
    const el = addShipment();
    // Give reasonable default windows.
    el.querySelector('[data-field="pickupStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 9, 0, 0));
    el.querySelector('[data-field="pickupEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 10, 0, 0));
    el.querySelector('[data-field="dropoffStart"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 11, 0, 0));
    el.querySelector('[data-field="dropoffEnd"]').value = toLocalInput(new Date(day.getFullYear(), day.getMonth(), day.getDate(), 12, 0, 0));
    reindexShipments();
  });

  $("shipments").addEventListener("click", (e) => {
    const btn = e.target?.closest?.("button[data-action='removeShipment']");
    if (!btn) return;
    const shipmentEl = btn.closest(".shipment");
    shipmentEl?.remove();
    reindexShipments();
  });

  $("runBtn").addEventListener("click", async () => {
    $("runBtn").disabled = true;
    try {
      const result = await runOptimizer();
      if (result) {
        renderStopsList(result);
        renderMap(result, mapState);
        $("status").textContent = "Rendered.";
      }
    } finally {
      $("runBtn").disabled = false;
    }
  });
}

main();


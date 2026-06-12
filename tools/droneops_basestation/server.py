#!/usr/bin/env python3
"""DroneOps local basestation web map."""

import argparse
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_sim"))

import droneops_planner  # noqa: E402
import sim_server  # noqa: E402


HOST = "127.0.0.1"
PORT = 8088
DEFAULT_BUCHAREST_ROUTE = [
    {"label": "START", "lat": 44.405700, "lon": 26.301900, "alt": 80},
    {"label": "WP1", "lat": 44.407400, "lon": 26.307800, "alt": 90},
    {"label": "END", "lat": 44.410200, "lon": 26.314000, "alt": 80},
]
BUCHAREST_REFERENCE_ZONES = [
    {
        "name": "Baneasa Airport reference area",
        "lat": 44.5032,
        "lon": 26.1021,
        "radiusMeters": 6000,
    },
    {
        "name": "Otopeni Airport reference area",
        "lat": 44.5711,
        "lon": 26.0850,
        "radiusMeters": 8000,
    },
]


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DroneOps Basestation</title>
  <style>
    :root {
      color-scheme: dark;
      font-family: Arial, Helvetica, sans-serif;
      background: #151719;
      color: #eceff1;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      grid-template-rows: auto 1fr;
      background: #151719;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 12px 16px;
      border-bottom: 1px solid #30363b;
      background: #1d2125;
    }
    h1 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      letter-spacing: 0;
    }
    main {
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      min-height: 0;
    }
    aside {
      padding: 14px;
      border-right: 1px solid #30363b;
      overflow: auto;
      background: #191d21;
    }
    label {
      display: block;
      margin-bottom: 8px;
      color: #b8c0c8;
      font-size: 13px;
    }
    textarea, input {
      width: 100%;
      box-sizing: border-box;
      border: 1px solid #3b444c;
      border-radius: 6px;
      padding: 10px;
      background: #111417;
      color: #f4f7f9;
      font: inherit;
    }
    textarea {
      min-height: 104px;
      resize: vertical;
      line-height: 1.35;
    }
    button {
      width: 100%;
      margin-top: 10px;
      border: 0;
      border-radius: 6px;
      padding: 10px 12px;
      background: #2f7d61;
      color: #ffffff;
      font-weight: 700;
      cursor: pointer;
    }
    button:disabled {
      opacity: .55;
      cursor: progress;
    }
    .toolbar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 10px;
    }
    .toolbar button {
      margin-top: 0;
    }
    .secondary {
      background: #374553;
    }
    .danger {
      background: #7a3a3a;
    }
    .compact {
      padding: 8px 9px;
      font-size: 12px;
    }
    .field-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 82px 34px;
      gap: 6px;
      align-items: end;
    }
    .field-grid input {
      padding: 8px;
      font-size: 12px;
    }
    .field-grid button {
      margin-top: 0;
      padding: 8px 0;
    }
    .hint {
      margin-top: 8px;
      color: #9aa4ad;
      font-size: 12px;
      line-height: 1.35;
    }
    .counter {
      display: grid;
      grid-template-columns: 44px 1fr 44px;
      gap: 8px;
      align-items: center;
    }
    .counter input {
      text-align: center;
    }
    .counter button {
      margin-top: 0;
    }
    .status {
      margin-top: 12px;
      padding: 10px;
      border-radius: 6px;
      background: #22282d;
      color: #d7dee5;
      font-size: 13px;
      line-height: 1.35;
      white-space: pre-wrap;
    }
    .section {
      margin-top: 14px;
    }
    .rows {
      display: grid;
      gap: 8px;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      padding: 8px 0;
      border-bottom: 1px solid #2a3035;
      font-size: 13px;
    }
    #map, #fallbackMap {
      min-height: 0;
      width: 100%;
      height: 100%;
    }
    #mapShell {
      position: relative;
      min-height: 0;
      background: #0d1114;
    }
    #fallbackMap {
      display: none;
    }
    .badge {
      color: #9bd4ff;
      font-size: 12px;
    }
    @media (max-width: 800px) {
      main {
        grid-template-columns: 1fr;
        grid-template-rows: auto 55vh;
      }
      aside {
        border-right: 0;
        border-bottom: 1px solid #30363b;
      }
    }
  </style>
</head>
<body>
  <header>
    <h1>DroneOps Basestation</h1>
    <div class="badge" id="modeBadge">SIMULATION_ONLY</div>
  </header>
  <main>
    <aside>
      <label for="order">Mission order</label>
      <textarea id="order">fly the route shown on the map and report position updates</textarea>
      <div class="toolbar">
        <button id="planBtn" class="secondary">Interpret Order</button>
        <button id="simulateBtn">Simulate</button>
      </div>
      <div class="status" id="status">Ready. Click the map to add waypoints, edit coordinates, then press Simulate.</div>

      <div class="section">
        <label>Drone Count</label>
        <div class="counter">
          <button id="removeDroneBtn" class="secondary compact">-</button>
          <input id="droneCount" type="number" min="1" max="12" step="1" value="3" />
          <button id="addDroneBtn" class="secondary compact">+</button>
        </div>
      </div>

      <div class="section">
        <label>Route Waypoints</label>
        <div class="hint">Default start is on Bucharest's eastern outskirts for simulation. Verify official UAS geographical zones before any real flight.</div>
        <div class="rows" id="waypoints"></div>
        <div class="toolbar">
          <button id="addWaypointBtn" class="secondary">Add Waypoint</button>
          <button id="resetRouteBtn" class="secondary">Reset Bucharest Route</button>
        </div>
      </div>

      <div class="section">
        <label>Fleet</label>
        <div class="rows" id="fleet"></div>
      </div>
    </aside>
    <section id="mapShell">
      <div id="map"></div>
      <canvas id="fallbackMap"></canvas>
    </section>
  </main>
  <script>
    window.DRONEOPS_CONFIG = __CONFIG__;
  </script>
  <script>
    const state = {
      map: null,
      polyline: null,
      routeMarkers: [],
      droneMarkers: {},
      route: [],
      googleReady: false,
      fallbackCanvas: document.getElementById('fallbackMap'),
      mapDiv: document.getElementById('map'),
      restrictionCircles: []
    };

    function setStatus(text) {
      document.getElementById('status').textContent = text;
    }

    function initGoogleMap() {
      state.googleReady = true;
      state.mapDiv.style.display = 'block';
      state.fallbackCanvas.style.display = 'none';
      const start = window.DRONEOPS_CONFIG.defaultRoute[0];
      state.map = new google.maps.Map(state.mapDiv, {
        center: { lat: Number(start.lat), lng: Number(start.lon) },
        zoom: 15,
        mapTypeId: 'satellite',
        disableDefaultUI: false,
        fullscreenControl: true,
        streetViewControl: false,
        mapTypeControl: true
      });
      state.map.addListener('click', event => {
        addWaypoint({
          label: 'WP' + state.route.length,
          lat: Number(event.latLng.lat().toFixed(6)),
          lon: Number(event.latLng.lng().toFixed(6)),
          alt: state.route.length ? state.route[state.route.length - 1].alt : 80
        });
      });
      drawReferenceZones();
      setRoute(window.DRONEOPS_CONFIG.defaultRoute);
      refreshFleet();
    }

    function useFallbackMap() {
      state.googleReady = false;
      state.mapDiv.style.display = 'none';
      state.fallbackCanvas.style.display = 'block';
      setRoute(window.DRONEOPS_CONFIG.defaultRoute);
      drawFallback();
      setStatus('Google Maps key not configured. Running local fallback visualization.');
    }

    function loadGoogleMaps() {
      const key = window.DRONEOPS_CONFIG.googleMapsApiKey;
      if (!key) {
        useFallbackMap();
        return;
      }
      window.initDroneOpsGoogleMap = initGoogleMap;
      const script = document.createElement('script');
      script.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(key) + '&callback=initDroneOpsGoogleMap';
      script.async = true;
      script.defer = true;
      script.onerror = useFallbackMap;
      document.head.appendChild(script);
    }

    function routeLatLngs(route) {
      return route.map(p => ({ lat: Number(p.lat), lng: Number(p.lon) }));
    }

    function normalizeRoute(route) {
      return route.map((point, index) => ({
        label: index === 0 ? 'START' : (index === route.length - 1 ? 'END' : 'WP' + index),
        lat: Number(point.lat),
        lon: Number(point.lon),
        alt: Number(point.alt || 80)
      }));
    }

    function setRoute(route) {
      state.route = normalizeRoute(route);
      renderWaypointList(state.route);
      redrawRoute();
      drawFallback();
    }

    function addWaypoint(point) {
      const next = state.route.slice();
      next.push(point);
      setRoute(next);
      setStatus('Waypoint added. Press Simulate to run the edited route.');
    }

    function updateWaypoint(index, key, value) {
      const next = state.route.slice();
      next[index] = { ...next[index], [key]: Number(value) };
      setRoute(next);
    }

    function removeWaypoint(index) {
      if (state.route.length <= 2) {
        setStatus('A route needs at least a start and end waypoint.');
        return;
      }
      const next = state.route.filter((_, rowIndex) => rowIndex !== index);
      setRoute(next);
    }

    function resetRoute() {
      setRoute(window.DRONEOPS_CONFIG.defaultRoute);
      setStatus('Bucharest outskirts demo route restored.');
    }

    function drawReferenceZones() {
      if (!state.googleReady || !state.map) return;
      for (const circle of state.restrictionCircles) circle.setMap(null);
      state.restrictionCircles = [];
      for (const zone of window.DRONEOPS_CONFIG.referenceZones) {
        state.restrictionCircles.push(new google.maps.Circle({
          strokeColor: '#ff6b6b',
          strokeOpacity: 0.85,
          strokeWeight: 2,
          fillColor: '#ff6b6b',
          fillOpacity: 0.12,
          map: state.map,
          center: { lat: Number(zone.lat), lng: Number(zone.lon) },
          radius: Number(zone.radiusMeters)
        }));
      }
    }

    function redrawRoute() {
      if (!(state.googleReady && state.map)) return;
      for (const marker of state.routeMarkers) marker.setMap(null);
      state.routeMarkers = [];
      const path = routeLatLngs(state.route);
      if (state.polyline) state.polyline.setMap(null);
      state.polyline = new google.maps.Polyline({
        path,
        geodesic: true,
        strokeColor: '#35c486',
        strokeOpacity: 1,
        strokeWeight: 4,
        map: state.map
      });
      const bounds = new google.maps.LatLngBounds();
      state.route.forEach((point, index) => {
        const pos = { lat: Number(point.lat), lng: Number(point.lon) };
        bounds.extend(pos);
        const marker = new google.maps.Marker({
          position: pos,
          map: state.map,
          draggable: true,
          label: String(index + 1),
          title: point.label || ('WP' + (index + 1))
        });
        marker.addListener('dragend', event => {
          const next = state.route.slice();
          next[index] = {
            ...next[index],
            lat: Number(event.latLng.lat().toFixed(6)),
            lon: Number(event.latLng.lng().toFixed(6))
          };
          setRoute(next);
        });
        state.routeMarkers.push(marker);
      });
      if (!bounds.isEmpty()) state.map.fitBounds(bounds, 64);
    }

    function updateRoute(intent) {
      setRoute(intent.routeWaypoints || []);
    }

    function renderWaypointList(route) {
      const el = document.getElementById('waypoints');
      el.innerHTML = '';
      route.forEach((point, index) => {
        const row = document.createElement('div');
        row.className = 'field-grid';
        row.innerHTML = `
          <input aria-label="${point.label} latitude" type="number" step="0.000001" value="${Number(point.lat).toFixed(6)}">
          <input aria-label="${point.label} longitude" type="number" step="0.000001" value="${Number(point.lon).toFixed(6)}">
          <input aria-label="${point.label} altitude" type="number" min="0" max="120" step="1" value="${Number(point.alt || 80).toFixed(0)}">
          <button class="danger compact" title="Remove waypoint">x</button>
        `;
        const inputs = row.querySelectorAll('input');
        inputs[0].addEventListener('change', event => updateWaypoint(index, 'lat', event.target.value));
        inputs[1].addEventListener('change', event => updateWaypoint(index, 'lon', event.target.value));
        inputs[2].addEventListener('change', event => updateWaypoint(index, 'alt', event.target.value));
        row.querySelector('button').addEventListener('click', () => removeWaypoint(index));
        el.appendChild(row);
      });
    }

    async function planMission() {
      const button = document.getElementById('planBtn');
      button.disabled = true;
      try {
        setStatus('Interpreting order with local planner...');
        const response = await fetch('/api/plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ order: document.getElementById('order').value })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'planning failed');
        updateRoute(payload.intent);
        setStatus('Order interpreted into editable waypoints. Press Simulate to run it.');
      } catch (error) {
        setStatus('Error: ' + error.message);
      } finally {
        button.disabled = false;
      }
    }

    async function simulateMission() {
      const button = document.getElementById('simulateBtn');
      button.disabled = true;
      try {
        if (state.route.length < 2) throw new Error('add at least two waypoints');
        setStatus('Starting local simulation...');
        const response = await fetch('/api/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            routeWaypoints: state.route,
            droneCount: Number(document.getElementById('droneCount').value || 1),
            objective: document.getElementById('order').value
          })
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'simulation failed');
        updateRoute(payload.intent);
        setStatus('Simulation running. Live execution is disabled.');
        await refreshFleet();
      } catch (error) {
        setStatus('Error: ' + error.message);
      } finally {
        button.disabled = false;
      }
    }

    async function refreshFleet() {
      try {
        const response = await fetch('/api/fleet');
        const fleet = await response.json();
        renderFleet(fleet.drones || []);
      } catch (error) {
        setStatus('Fleet refresh failed: ' + error.message);
      }
    }

    function renderFleet(drones) {
      const el = document.getElementById('fleet');
      el.innerHTML = '';
      const seen = new Set();
      for (const drone of drones) {
        seen.add(drone.id);
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `<span>${drone.id}</span><span>${drone.state} ${Number(drone.batteryPercent).toFixed(0)}%</span>`;
        el.appendChild(row);

        if (state.googleReady && state.map) {
          const pos = { lat: Number(drone.latitude), lng: Number(drone.longitude) };
          if (!state.droneMarkers[drone.id]) {
            state.droneMarkers[drone.id] = new google.maps.Marker({
              position: pos,
              map: state.map,
              label: 'D',
              title: drone.id
            });
          } else {
            state.droneMarkers[drone.id].setPosition(pos);
          }
        }
      }
      if (state.googleReady && state.map) {
        for (const [id, marker] of Object.entries(state.droneMarkers)) {
          if (!seen.has(id)) {
            marker.setMap(null);
            delete state.droneMarkers[id];
          }
        }
      }
      drawFallback(drones);
    }

    function projectPoint(point, bounds, rect) {
      const lat = Number(point.lat ?? point.latitude);
      const lon = Number(point.lon ?? point.longitude);
      const x = ((lon - bounds.minLon) / Math.max(0.000001, bounds.maxLon - bounds.minLon)) * rect.width + rect.x;
      const y = rect.y + rect.height - ((lat - bounds.minLat) / Math.max(0.000001, bounds.maxLat - bounds.minLat)) * rect.height;
      return { x, y };
    }

    function drawFallback(drones = []) {
      if (state.googleReady) return;
      const canvas = state.fallbackCanvas;
      const shell = document.getElementById('mapShell');
      canvas.width = shell.clientWidth || 800;
      canvas.height = shell.clientHeight || 600;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#0d1114';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const all = [...state.route, ...drones];
      if (!all.length) {
        ctx.fillStyle = '#9aa4ad';
        ctx.font = '16px Arial';
        ctx.fillText('Plan a mission to draw the route.', 24, 36);
        return;
      }

      const lats = all.map(p => Number(p.lat ?? p.latitude));
      const lons = all.map(p => Number(p.lon ?? p.longitude));
      const pad = 0.0005;
      const bounds = {
        minLat: Math.min(...lats) - pad,
        maxLat: Math.max(...lats) + pad,
        minLon: Math.min(...lons) - pad,
        maxLon: Math.max(...lons) + pad
      };
      const rect = { x: 48, y: 48, width: canvas.width - 96, height: canvas.height - 96 };

      ctx.strokeStyle = '#26323a';
      ctx.lineWidth = 1;
      for (let i = 0; i < 8; i++) {
        const x = rect.x + rect.width * (i / 7);
        const y = rect.y + rect.height * (i / 7);
        ctx.beginPath(); ctx.moveTo(x, rect.y); ctx.lineTo(x, rect.y + rect.height); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(rect.x, y); ctx.lineTo(rect.x + rect.width, y); ctx.stroke();
      }

      if (state.route.length) {
        ctx.strokeStyle = '#35c486';
        ctx.lineWidth = 4;
        ctx.beginPath();
        state.route.forEach((point, index) => {
          const p = projectPoint(point, bounds, rect);
          if (index === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
        state.route.forEach((point, index) => {
          const p = projectPoint(point, bounds, rect);
          ctx.fillStyle = '#ffffff';
          ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, Math.PI * 2); ctx.fill();
          ctx.fillStyle = '#111417';
          ctx.font = '12px Arial';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(String(index + 1), p.x, p.y);
        });
      }

      drones.forEach(drone => {
        const p = projectPoint(drone, bounds, rect);
        ctx.fillStyle = '#65a7ff';
        ctx.beginPath(); ctx.arc(p.x, p.y, 10, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#eaf2ff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(drone.id, p.x + 14, p.y + 4);
      });
    }

    function changeDroneCount(delta) {
      const input = document.getElementById('droneCount');
      const value = Math.min(12, Math.max(1, Number(input.value || 1) + delta));
      input.value = String(value);
    }

    document.getElementById('planBtn').addEventListener('click', planMission);
    document.getElementById('simulateBtn').addEventListener('click', simulateMission);
    document.getElementById('addWaypointBtn').addEventListener('click', () => {
      const last = state.route[state.route.length - 1] || window.DRONEOPS_CONFIG.defaultRoute[0];
      addWaypoint({
        lat: Number(last.lat) + 0.001,
        lon: Number(last.lon) + 0.001,
        alt: Number(last.alt || 80)
      });
    });
    document.getElementById('resetRouteBtn').addEventListener('click', resetRoute);
    document.getElementById('addDroneBtn').addEventListener('click', () => changeDroneCount(1));
    document.getElementById('removeDroneBtn').addEventListener('click', () => changeDroneCount(-1));
    window.addEventListener('resize', () => drawFallback());
    loadGoogleMaps();
    setInterval(refreshFleet, 1000);
  </script>
</body>
</html>
"""


class BasestationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html()
            return
        if parsed.path == "/api/fleet":
            self._json(200, sim_server.STATE.snapshot())
            return
        if parsed.path == "/api/health":
            self._json(200, {
                "service": "DroneOps Basestation",
                "mode": "SIMULATION_ONLY",
                "googleMapsConfigured": bool(self.server.google_maps_api_key),
            })
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(body.decode("utf-8"))
            if parsed.path == "/api/plan":
                order = payload.get("order", "")
                intent = self.server.plan_order(order)
                self._json(200, {"intent": intent})
                return
            if parsed.path == "/api/simulate":
                intent = self.server.intent_from_route(payload)
                drone_count = int(payload.get("droneCount", 1))
                sim_server.STATE.configure_fleet(drone_count, intent["routeWaypoints"][0])
                response = sim_server.STATE.accept_mission_intent(intent)
                self._json(200, {"intent": intent, "droneopsResponse": response})
                return
            self._json(404, {"error": "not_found"})
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args))

    def _html(self):
        config = {
            "googleMapsApiKey": self.server.google_maps_api_key,
            "mode": "SIMULATION_ONLY",
            "defaultRoute": DEFAULT_BUCHAREST_ROUTE,
            "referenceZones": BUCHAREST_REFERENCE_ZONES,
        }
        body = HTML.replace("__CONFIG__", json.dumps(config))
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status, payload):
        data = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class BasestationServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, google_maps_api_key, model, use_ollama):
        super().__init__(server_address, handler_class)
        self.google_maps_api_key = google_maps_api_key
        self.model = model
        self.use_ollama = use_ollama

    def plan_order(self, order):
        droneops_planner.validate_order_text(order)
        if self.use_ollama:
            intent = droneops_planner.call_ollama(
                order,
                self.model,
                droneops_planner.DEFAULT_OLLAMA_URL,
                30.0,
            )
        else:
            intent = droneops_planner.mock_intent(order)
        return droneops_planner.validate_intent(intent)

    def intent_from_route(self, payload):
        route = payload.get("routeWaypoints")
        if not isinstance(route, list) or len(route) < 2:
            raise ValueError("routeWaypoints must contain at least 2 points")

        normalized_route = []
        for index, point in enumerate(route):
            lat = float(point.get("lat"))
            lon = float(point.get("lon"))
            alt = float(point.get("alt", 80))
            label = "START" if index == 0 else ("END" if index == len(route) - 1 else "WP{}".format(index))
            normalized_route.append({
                "label": label,
                "lat": lat,
                "lon": lon,
                "alt": alt,
            })

        lats = [point["lat"] for point in normalized_route]
        lons = [point["lon"] for point in normalized_route]
        pad = 0.001
        operating_area = [
            {"lat": min(lats) - pad, "lon": min(lons) - pad},
            {"lat": max(lats) + pad, "lon": min(lons) - pad},
            {"lat": max(lats) + pad, "lon": max(lons) + pad},
            {"lat": min(lats) - pad, "lon": max(lons) + pad},
        ]
        objective = str(payload.get("objective") or "simulate interactive waypoint route").strip()
        intent = {
            "id": "intent-{}".format(int(time.time())),
            "mode": "simulation",
            "liveExecution": False,
            "requiresHumanApproval": True,
            "objective": objective,
            "operatingArea": operating_area,
            "routeWaypoints": normalized_route,
            "maxSpeedMetersPerSecond": 15.0,
            "constraints": {
                "geofenceRequired": True,
                "lostLinkAction": "return_to_launch",
                "maxAltitudeMeters": 100.0,
                "minBatteryPercent": 35.0,
            },
            "tasks": [
                {
                    "type": "route",
                    "priority": 1,
                    "description": "Fly the simulated route through the supplied interactive waypoints.",
                }
            ],
        }
        return droneops_planner.validate_intent(intent)


def run_server(host, port, google_maps_api_key, model, use_ollama):
    server = BasestationServer(
        (host, port),
        BasestationHandler,
        google_maps_api_key,
        model,
        use_ollama,
    )
    print("DroneOps basestation listening on http://{}:{}".format(host, port))
    if not google_maps_api_key:
        print("GOOGLE_MAPS_API_KEY not set; fallback map will be used.")
    print("Mission execution mode: SIMULATION_ONLY")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def self_test(model, use_ollama):
    server = BasestationServer(("127.0.0.1", 0), BasestationHandler, "", model, use_ollama)
    intent = server.intent_from_route({
        "objective": "simulate Bucharest outskirts waypoint route",
        "routeWaypoints": DEFAULT_BUCHAREST_ROUTE,
        "droneCount": 3,
    })
    sim_server.STATE.configure_fleet(3, intent["routeWaypoints"][0])
    response = sim_server.STATE.accept_mission_intent(intent)
    fleet = sim_server.STATE.snapshot()
    print(json.dumps({
        "intent": intent,
        "droneopsResponse": response,
        "fleet": fleet,
    }, indent=2, sort_keys=True))
    server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run the DroneOps basestation web map.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--ollama", action="store_true", help="Use local Ollama instead of deterministic mock parsing.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    google_maps_api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if args.self_test:
        self_test(args.model, args.ollama)
    else:
        run_server(args.host, args.port, google_maps_api_key, args.model, args.ollama)


if __name__ == "__main__":
    main()

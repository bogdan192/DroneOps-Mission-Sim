#!/usr/bin/env python3
"""Live web view for mocked DroneOps missions."""

import argparse
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))

from atak_tracking.tracker import AtakDroneTracker  # noqa: E402
from controller_adapters import simulated_controller  # noqa: E402
from fleet_protocol import messages  # noqa: E402
from mock_runtime import mission_simulator  # noqa: E402
from onboard_node.node import DEFAULT_ROUTE, OnboardNode  # noqa: E402


HOST = "127.0.0.1"
PORT = 8092


class LiveMissionState:
    def __init__(self):
        self.lock = threading.Lock()
        self.tracker = AtakDroneTracker()
        self.reset()

    def reset(self):
        self.order = "coordinate with peers and simulate the Bucharest outskirts route"
        self.node_count = 4
        self.total_ticks = 18
        self.tick_seconds = 0.7
        self.started_at = None
        self.mission = None
        self.assignment_plan = None
        self.controller_programs = []
        self.runtimes = []
        self.network = None
        self.latest_telemetry = []
        self.status = "idle"

    def start(self, order=None, node_count=4, ticks=18, tick_seconds=0.7):
        with self.lock:
            self.reset()
            self.order = str(order or self.order)
            self.node_count = max(1, min(12, int(node_count)))
            self.total_ticks = max(2, min(300, int(ticks)))
            self.tick_seconds = max(0.1, min(10.0, float(tick_seconds)))

            self.network = mission_simulator.MockTakNetwork()
            fleet_status = mission_simulator.build_mock_fleet(self.node_count)
            leader = OnboardNode(fleet_status[0]["nodeId"], position=fleet_status[0]["position"])
            self.network.publish("order.intent", messages.order_intent("order-web-001", self.order, route_waypoints=DEFAULT_ROUTE))
            for status in fleet_status:
                self.network.publish("node.status", status)

            onboard_result = leader.handle_order(self.order, route_waypoints=DEFAULT_ROUTE, fleet_status=fleet_status)
            self.mission = onboard_result["mission"]
            self.assignment_plan = onboard_result["assignmentPlan"]
            self.network.publish("mission.proposal", {
                "type": "mission.proposal",
                "schemaVersion": "0.1",
                "timestamp": messages.timestamp(),
                "missionId": self.mission["missionId"],
                "source": leader.node_id,
                "liveExecution": False,
                "assignmentCount": self.assignment_plan["assignmentCount"],
            })

            for assignment in self.assignment_plan["assignments"]:
                self.network.publish("mission.assignment", assignment)
                program = simulated_controller.compile_simulation_program(
                    assignment["nodeId"],
                    self.mission,
                    assignment,
                )
                self.controller_programs.append(program)
                self.runtimes.append(mission_simulator.MockDroneRuntime(assignment["nodeId"], program))

            self.started_at = time.time()
            self.status = "running"
            self._advance_locked()
            return self.snapshot_locked()

    def snapshot(self):
        with self.lock:
            self._advance_locked()
            return self.snapshot_locked()

    def atak_snapshot(self):
        with self.lock:
            self._advance_locked()
            return self.tracker.snapshot()

    def snapshot_locked(self):
        return {
            "mode": "SIMULATION_ONLY",
            "liveExecution": False,
            "status": self.status,
            "order": self.order,
            "nodeCount": self.node_count,
            "totalTicks": self.total_ticks,
            "currentTick": self.current_tick_locked(),
            "mission": self.mission,
            "assignmentPlan": self.assignment_plan,
            "controllerPrograms": self.controller_programs,
            "telemetry": self.latest_telemetry,
            "atakDrones": self.tracker.snapshot()["drones"],
            "networkTopics": self.network_topics_locked(),
            "safety": {
                "llmDirectControllerAccess": False,
                "rawControllerCommands": False,
                "realDroneCommands": False,
            },
        }

    def _advance_locked(self):
        if not self.started_at or not self.runtimes:
            return
        tick = self.current_tick_locked()
        telemetry = []
        for runtime in self.runtimes:
            item = runtime.telemetry_at(tick, self.total_ticks)
            telemetry.append(item)
            self.network.publish("mission.telemetry", item)
        self.latest_telemetry = telemetry
        self.tracker.update_from_telemetry(telemetry)
        if tick >= self.total_ticks - 1:
            self.status = "complete"

    def current_tick_locked(self):
        if not self.started_at:
            return 0
        return min(self.total_ticks - 1, int((time.time() - self.started_at) / self.tick_seconds))

    def network_topics_locked(self):
        if not self.network:
            return []
        return sorted(set(event["topic"] for event in self.network.events))


STATE = LiveMissionState()


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DroneOps Live Mission</title>
  <style>
    :root { color-scheme: dark; font-family: Arial, Helvetica, sans-serif; background: #121416; color: #edf2f7; }
    body { margin: 0; min-height: 100vh; display: grid; grid-template-rows: auto 1fr; background: #121416; }
    header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; background: #1c2227; border-bottom: 1px solid #303941; }
    h1 { margin: 0; font-size: 18px; letter-spacing: 0; }
    main { display: grid; grid-template-columns: 360px 1fr; min-height: 0; }
    aside { padding: 14px; overflow: auto; border-right: 1px solid #303941; background: #181d22; }
    label { display: block; margin-top: 12px; margin-bottom: 6px; color: #b9c4ce; font-size: 13px; }
    textarea, input { width: 100%; box-sizing: border-box; border: 1px solid #3c4650; border-radius: 6px; padding: 9px; background: #101316; color: #f8fbfd; font: inherit; }
    textarea { min-height: 96px; resize: vertical; line-height: 1.35; }
    button { width: 100%; margin-top: 12px; border: 0; border-radius: 6px; padding: 10px 12px; background: #2f7d61; color: white; font-weight: 700; cursor: pointer; }
    .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .status { margin-top: 12px; padding: 10px; border-radius: 6px; background: #222a31; color: #dbe4ec; font-size: 13px; line-height: 1.35; }
    .rows { display: grid; gap: 8px; margin-top: 10px; }
    .row { display: grid; grid-template-columns: 1fr auto; gap: 8px; padding: 8px; border: 1px solid #303941; border-radius: 6px; background: #151a1f; font-size: 13px; }
    #mapShell { position: relative; min-height: 0; background: #0b0f12; }
    #map, #fallbackMap { width: 100%; height: 100%; min-height: 0; }
    #fallbackMap { display: none; }
    .badge { color: #9bd4ff; font-size: 12px; }
    @media (max-width: 820px) { main { grid-template-columns: 1fr; grid-template-rows: auto 55vh; } aside { border-right: 0; border-bottom: 1px solid #303941; } }
  </style>
</head>
<body>
  <header>
    <h1>DroneOps Live Mission</h1>
    <div class="badge">SIMULATION_ONLY</div>
  </header>
  <main>
    <aside>
      <label for="order">Order</label>
      <textarea id="order">coordinate with peers and simulate the Bucharest outskirts route</textarea>
      <div class="grid2">
        <div>
          <label for="nodes">Drones</label>
          <input id="nodes" type="number" min="1" max="12" value="4" />
        </div>
        <div>
          <label for="ticks">Ticks</label>
          <input id="ticks" type="number" min="2" max="300" value="36" />
        </div>
      </div>
      <button id="startBtn">Start Live Simulation</button>
      <div class="status" id="status">Ready. Start a mocked mission to track ATAK-style drone nodes.</div>
      <label>Tracked ATAK Drones</label>
      <div class="rows" id="drones"></div>
      <label>Network Topics</label>
      <div class="status" id="topics">none</div>
    </aside>
    <section id="mapShell">
      <div id="map"></div>
      <canvas id="fallbackMap"></canvas>
    </section>
  </main>
  <script>window.DRONEOPS_CONFIG = __CONFIG__;</script>
  <script>
    const state = { map: null, googleReady: false, routeLine: null, routeMarkers: [], droneMarkers: {}, canvas: document.getElementById('fallbackMap') };

    function setStatus(text) { document.getElementById('status').textContent = text; }

    function initGoogleMap() {
      state.googleReady = true;
      document.getElementById('map').style.display = 'block';
      state.canvas.style.display = 'none';
      const start = window.DRONEOPS_CONFIG.defaultRoute[0];
      state.map = new google.maps.Map(document.getElementById('map'), {
        center: { lat: start.lat, lng: start.lon },
        zoom: 15,
        mapTypeId: 'satellite',
        streetViewControl: false
      });
      drawRoute(window.DRONEOPS_CONFIG.defaultRoute);
      poll();
    }

    function useFallbackMap() {
      state.googleReady = false;
      document.getElementById('map').style.display = 'none';
      state.canvas.style.display = 'block';
      drawFallback([]);
      poll();
    }

    function loadMap() {
      const key = window.DRONEOPS_CONFIG.googleMapsApiKey;
      if (!key) { useFallbackMap(); return; }
      window.initDroneOpsLiveMap = initGoogleMap;
      const script = document.createElement('script');
      script.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(key) + '&callback=initDroneOpsLiveMap';
      script.async = true;
      script.defer = true;
      script.onerror = useFallbackMap;
      document.head.appendChild(script);
    }

    function drawRoute(route) {
      if (!state.googleReady || !state.map) return;
      for (const marker of state.routeMarkers) marker.setMap(null);
      state.routeMarkers = [];
      if (state.routeLine) state.routeLine.setMap(null);
      const path = route.map(p => ({ lat: Number(p.lat), lng: Number(p.lon) }));
      state.routeLine = new google.maps.Polyline({ path, geodesic: true, strokeColor: '#35c486', strokeOpacity: 1, strokeWeight: 4, map: state.map });
      const bounds = new google.maps.LatLngBounds();
      path.forEach((pos, index) => {
        bounds.extend(pos);
        state.routeMarkers.push(new google.maps.Marker({ position: pos, map: state.map, label: String(index + 1) }));
      });
      if (!bounds.isEmpty()) state.map.fitBounds(bounds, 64);
    }

    async function startMission() {
      const body = {
        order: document.getElementById('order').value,
        nodeCount: Number(document.getElementById('nodes').value || 4),
        ticks: Number(document.getElementById('ticks').value || 36),
        tickSeconds: 0.6
      };
      const response = await fetch('/api/mission/start', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
      const payload = await response.json();
      if (!response.ok) { setStatus('Error: ' + (payload.error || 'start failed')); return; }
      if (payload.mission) drawRoute(payload.mission.routeWaypoints || window.DRONEOPS_CONFIG.defaultRoute);
      render(payload);
    }

    async function poll() {
      try {
        const response = await fetch('/api/mission');
        const payload = await response.json();
        render(payload);
      } catch (error) {
        setStatus('Tracker polling failed: ' + error.message);
      }
      setTimeout(poll, 600);
    }

    function render(payload) {
      setStatus(`Mission: ${payload.status || 'idle'} | tick ${payload.currentTick || 0}/${Math.max(0, (payload.totalTicks || 1) - 1)} | liveExecution=${payload.liveExecution}`);
      document.getElementById('topics').textContent = (payload.networkTopics || []).join(', ') || 'none';
      renderDrones(payload.atakDrones || []);
      drawFallback(payload.atakDrones || []);
    }

    function renderDrones(drones) {
      const el = document.getElementById('drones');
      el.innerHTML = '';
      const seen = new Set();
      for (const drone of drones) {
        seen.add(drone.nodeId);
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `<span>${drone.nodeId}<br>${drone.state}</span><span>${Number(drone.lat).toFixed(5)}, ${Number(drone.lon).toFixed(5)}<br>${Number(drone.batteryPercent).toFixed(0)}%</span>`;
        el.appendChild(row);
        if (state.googleReady && state.map) {
          const pos = { lat: Number(drone.lat), lng: Number(drone.lon) };
          if (!state.droneMarkers[drone.nodeId]) {
            state.droneMarkers[drone.nodeId] = new google.maps.Marker({ position: pos, map: state.map, label: 'D', title: drone.nodeId });
          } else {
            state.droneMarkers[drone.nodeId].setPosition(pos);
          }
        }
      }
      if (state.googleReady && state.map) {
        for (const [id, marker] of Object.entries(state.droneMarkers)) {
          if (!seen.has(id)) { marker.setMap(null); delete state.droneMarkers[id]; }
        }
      }
    }

    function drawFallback(drones) {
      if (state.googleReady) return;
      const shell = document.getElementById('mapShell');
      const canvas = state.canvas;
      canvas.width = shell.clientWidth || 900;
      canvas.height = shell.clientHeight || 600;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#0b0f12';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      const route = window.DRONEOPS_CONFIG.defaultRoute;
      const all = [...route, ...drones.map(d => ({ lat: d.lat, lon: d.lon }))];
      const lats = all.map(p => Number(p.lat));
      const lons = all.map(p => Number(p.lon));
      const bounds = { minLat: Math.min(...lats) - .001, maxLat: Math.max(...lats) + .001, minLon: Math.min(...lons) - .001, maxLon: Math.max(...lons) + .001 };
      const rect = { x: 52, y: 52, width: canvas.width - 104, height: canvas.height - 104 };
      const project = p => ({ x: rect.x + ((Number(p.lon) - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * rect.width, y: rect.y + rect.height - ((Number(p.lat) - bounds.minLat) / (bounds.maxLat - bounds.minLat)) * rect.height });
      ctx.strokeStyle = '#26323a'; ctx.lineWidth = 1;
      for (let i = 0; i < 8; i++) { const x = rect.x + rect.width * i / 7; const y = rect.y + rect.height * i / 7; ctx.beginPath(); ctx.moveTo(x, rect.y); ctx.lineTo(x, rect.y + rect.height); ctx.stroke(); ctx.beginPath(); ctx.moveTo(rect.x, y); ctx.lineTo(rect.x + rect.width, y); ctx.stroke(); }
      ctx.strokeStyle = '#35c486'; ctx.lineWidth = 4; ctx.beginPath();
      route.forEach((point, index) => { const p = project(point); if (index === 0) ctx.moveTo(p.x, p.y); else ctx.lineTo(p.x, p.y); });
      ctx.stroke();
      drones.forEach(drone => { const p = project({ lat: drone.lat, lon: drone.lon }); ctx.fillStyle = drone.state === 'complete' ? '#8ee08e' : '#65a7ff'; ctx.beginPath(); ctx.arc(p.x, p.y, 10, 0, Math.PI * 2); ctx.fill(); ctx.fillStyle = '#eaf2ff'; ctx.font = '12px Arial'; ctx.fillText(drone.nodeId, p.x + 14, p.y + 4); });
    }

    document.getElementById('startBtn').addEventListener('click', startMission);
    window.addEventListener('resize', () => drawFallback([]));
    loadMap();
  </script>
</body>
</html>
"""


class LiveWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html()
            return
        if parsed.path == "/api/health":
            self._json(200, {"service": "DroneOps Live Web", "mode": "SIMULATION_ONLY"})
            return
        if parsed.path == "/api/mission":
            self._json(200, STATE.snapshot())
            return
        if parsed.path == "/api/atak/drones":
            self._json(200, STATE.atak_snapshot())
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/mission/start":
            self._json(404, {"error": "not_found"})
            return
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(body.decode("utf-8") or "{}")
            snapshot = STATE.start(
                order=payload.get("order"),
                node_count=payload.get("nodeCount", 4),
                ticks=payload.get("ticks", 18),
                tick_seconds=payload.get("tickSeconds", 0.7),
            )
            self._json(200, snapshot)
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args))

    def _html(self):
        config = {
            "googleMapsApiKey": self.server.google_maps_api_key,
            "defaultRoute": DEFAULT_ROUTE,
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


class LiveWebServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, google_maps_api_key):
        super().__init__(server_address, handler_class)
        self.google_maps_api_key = google_maps_api_key


def run_server(host, port, google_maps_api_key):
    server = LiveWebServer((host, port), LiveWebHandler, google_maps_api_key)
    print("DroneOps live web listening on http://{}:{}".format(host, port))
    print("Mission execution mode: SIMULATION_ONLY")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def self_test():
    STATE.start(node_count=3, ticks=4, tick_seconds=0.1)
    first = STATE.snapshot()
    assert first["liveExecution"] is False
    assert len(first["atakDrones"]) == 3
    time.sleep(0.25)
    later = STATE.snapshot()
    assert later["currentTick"] >= first["currentTick"]
    assert STATE.atak_snapshot()["drones"]
    return later


def main():
    parser = argparse.ArgumentParser(description="Run the live DroneOps mission web view.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        print(json.dumps(self_test(), indent=2, sort_keys=True))
    else:
        run_server(args.host, args.port, os.environ.get("GOOGLE_MAPS_API_KEY", ""))


if __name__ == "__main__":
    main()


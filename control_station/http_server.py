#!/usr/bin/env python3
"""HTTP API for the simulation control station."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from onboard_node.node import DEFAULT_ROUTE

from .ui import render_index_html


class ControlStationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html()
            return
        if parsed.path == "/api/health":
            self._json(200, {"service": "DroneOps Control Station", "mode": "SIMULATION_ONLY"})
            return
        if parsed.path == "/api/mission":
            self._json(200, self.server.mission_session.snapshot())
            return
        if parsed.path == "/api/atak/drones":
            self._json(200, self.server.mission_session.atak_snapshot())
            return
        if parsed.path == "/api/atak/tracks":
            snapshot = self.server.mission_session.snapshot()
            self._json(200, {
                "mode": "SIMULATION_ONLY",
                "source": "mock-atak-feed",
                "readOnly": True,
                "tracks": snapshot["atakTracks"],
            })
            return
        if parsed.path == "/api/assets":
            self._json(200, {
                "mode": "SIMULATION_ONLY",
                "source": "mock-external-assets",
                "readOnly": True,
                "assets": self.server.mission_session.snapshot()["externalAssets"],
            })
            return
        if parsed.path == "/api/observations":
            self._json(200, {
                "mode": "SIMULATION_ONLY",
                "source": "mock-observation-sensor",
                "readOnly": True,
                "observations": self.server.mission_session.observations_snapshot(),
            })
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/mission/start":
            self._start_mission()
            return
        if parsed.path == "/api/orders/live":
            self._live_order()
            return
        if parsed.path == "/api/observations":
            self._observation_report()
            return
        self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args))

    def _start_mission(self):
        try:
            payload = self._read_json()
            snapshot = self.server.mission_session.start(
                order=payload.get("order"),
                node_count=payload.get("nodeCount", 4),
                ticks=payload.get("ticks", 18),
                tick_seconds=payload.get("tickSeconds", 0.7),
                route_waypoints=payload.get("routeWaypoints"),
                selected_node_ids=payload.get("selectedNodeIds"),
            )
            self._json(200, snapshot)
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def _live_order(self):
        try:
            payload = self._read_json()
            snapshot = self.server.mission_session.apply_live_order(
                payload.get("targets"),
                payload.get("command"),
            )
            self._json(200, snapshot)
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def _observation_report(self):
        try:
            snapshot = self.server.mission_session.add_observation_report(self._read_json())
            self._json(200, snapshot)
        except Exception as exc:
            self._json(422, {"error": str(exc), "mode": "SIMULATION_ONLY"})

    def _read_json(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        return json.loads(body.decode("utf-8") or "{}")

    def _html(self):
        body = render_index_html(self.server.google_maps_api_key, DEFAULT_ROUTE)
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


class ControlStationServer(ThreadingHTTPServer):
    def __init__(self, server_address, handler_class, mission_session, google_maps_api_key):
        super().__init__(server_address, handler_class)
        self.mission_session = mission_session
        self.google_maps_api_key = google_maps_api_key


def run_server(host, port, mission_session, google_maps_api_key):
    server = ControlStationServer((host, port), ControlStationHandler, mission_session, google_maps_api_key)
    _safe_print("DroneOps control station listening on http://{}:{}".format(host, port))
    _safe_print("Mission execution mode: SIMULATION_ONLY")
    try:
        server.serve_forever()
    finally:
        server.server_close()


def _safe_print(message):
    try:
        print(message)
    except Exception:
        pass

#!/usr/bin/env python3
"""Smoke tests for the control station UI and local API."""

import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_station.http_server import ControlStationHandler, ControlStationServer
from control_station.mission_session import ControlStationMissionSession
from control_station.ui import render_index_html
from onboard_node.node import DEFAULT_ROUTE


def request_json(method, url, payload=None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url):
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


def assert_ui_markup():
    html = render_index_html("", DEFAULT_ROUTE)
    required_ids = [
        "selectAllBtn",
        "selectNoneBtn",
        "startBtn",
        "drawModeBtn",
        "holdBtn",
        "resumeBtn",
        "returnBtn",
        "phaseText",
        "phaseProgress",
        "liveOrderHint",
        "undoClearBtn",
        "assets",
        "observations",
        "fallbackMap",
        "droneModal",
        "observationTooltip",
    ]
    for element_id in required_ids:
        assert 'id="{}"'.format(element_id) in html, "missing UI control: {}".format(element_id)
    assert "sendSelectedBtn" not in html, "duplicate send-selected action should not be present"
    assert "fallbackMap').addEventListener('click'" in html, "fallback map click handler missing"
    assert "fallbackMap').addEventListener('mousemove'" in html, "fallback map hover handler missing"
    assert "button:disabled" in html, "disabled button state styling missing"
    assert "updateActionStates" in html, "action state guard missing"
    assert "requestBusy" in html, "request in-flight guard missing"
    assert "missionStatus === 'running'" in html, "live-order running-state guard missing"
    assert "followDroneId" in html, "click-to-follow state missing"
    assert "panTo" not in html, "map should not pan while following a drone tooltip"
    assert "positionDroneTooltip" in html, "tooltip follow positioning missing"
    assert "width: min(310px" in html, "compact drone tooltip width missing"
    assert "grid-template-rows: auto 125px" in html, "compact live-view panel height missing"
    assert "Start Simulation" in html, "primary action should use plain simulation wording"
    assert "Return Home" in html, "RTH action should use plain language"
    assert "Route duration" in html, "duration label should avoid tick jargon"
    assert "<summary>Diagnostics</summary>" in html, "diagnostics should be collapsed"
    assert "confirm('Clear all waypoints?')" in html, "route clear confirmation missing"
    assert "Mission complete. Drones are back at the start point." in html, "complete phase copy missing"
    assert "External Assets <span class=\"micro\">(read-only)</span>" in html, "external assets panel missing"
    assert "renderExternalAssets" in html, "external asset renderer missing"
    assert "Observation Reports" in html, "observation report panel missing"
    assert "renderObservationReports" in html, "observation report renderer missing"
    assert "/api/observations" in html or "observationTooltip" in html, "observation UI hook missing"


def assert_api_flow():
    session = ControlStationMissionSession()
    server = ControlStationServer(("127.0.0.1", 0), ControlStationHandler, session, "")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = "http://{}:{}".format(host, port)
    try:
        html = request_text(base + "/")
        assert "DroneOps Control Station" in html
        health = request_json("GET", base + "/api/health")
        assert health["mode"] == "SIMULATION_ONLY"
        assets_payload = request_json("GET", base + "/api/assets")
        assert assets_payload["readOnly"] is True
        assert len(assets_payload["assets"]) >= 6
        assert all(asset["readOnly"] for asset in assets_payload["assets"])
        assert any(asset["kind"] == "drone" for asset in assets_payload["assets"])
        assert any(asset["kind"] == "personnel" for asset in assets_payload["assets"])
        atak_tracks_payload = request_json("GET", base + "/api/atak/tracks")
        assert atak_tracks_payload["readOnly"] is True
        assert len(atak_tracks_payload["tracks"]) >= 3
        assert any(track["kind"] == "drone" for track in atak_tracks_payload["tracks"])
        observations_payload = request_json("GET", base + "/api/observations")
        assert observations_payload["readOnly"] is True
        assert observations_payload["observations"] == []

        before = request_json("GET", base + "/api/mission")
        assert before["status"] == "idle"
        assert before["atakDrones"] == []
        assert before["externalAssets"]
        assert before["atakTracks"]
        assert before["observationReports"] == []

        posted = request_json("POST", base + "/api/observations", {
            "reportId": "obs.api.red-roof",
            "reportingNodeId": "drone-99",
            "label": "Red roof",
            "category": "structure_feature",
            "confidence": 0.88,
            "position": {"lat": 44.4081, "lon": 26.3142, "alt": 88},
            "imageDataUri": "data:image/svg+xml;utf8,%3Csvg%3E%3C/svg%3E",
        })
        assert posted["observationReports"][0]["label"] == "Red roof"
        try:
            request_json("POST", base + "/api/observations", {
                "reportId": "obs.bad",
                "reportingNodeId": "drone-99",
                "label": "Bad",
                "position": {"lat": 44.4081, "lon": 26.3142, "alt": 88},
                "imageDataUri": "data:image/svg+xml;utf8,%3Csvg%3E%3C/svg%3E",
                "tasking": "not allowed",
            })
            raise AssertionError("prohibited observation field accepted")
        except urllib.error.HTTPError as exc:
            blocked = json.loads(exc.read().decode("utf-8"))
        assert blocked["mode"] == "SIMULATION_ONLY"
        assert "prohibited" in blocked["error"]

        started = request_json("POST", base + "/api/mission/start", {
            "order": "coordinate with peers and simulate the Bucharest outskirts route",
            "nodeCount": 4,
            "ticks": 8,
            "tickSeconds": 0.1,
            "selectedNodeIds": ["drone-01", "drone-02"],
            "routeWaypoints": DEFAULT_ROUTE,
        })
        assert started["status"] == "running"
        assert started["selectedNodeIds"] == ["drone-01", "drone-02"]
        assert len(started["atakDrones"]) == 2
        assert started["liveExecution"] is False

        held = request_json("POST", base + "/api/orders/live", {
            "targets": ["drone-01"],
            "command": "hold",
        })
        assert held["liveOrders"]["drone-01"]["command"] == "hold"

        resumed = request_json("POST", base + "/api/orders/live", {
            "targets": ["drone-01"],
            "command": "resume",
        })
        assert "drone-01" not in resumed["liveOrders"]
    finally:
        server.shutdown()
        server.server_close()


def main():
    assert_ui_markup()
    assert_api_flow()
    print("Control station UI smoke checks passed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Simulation-only observation report generation."""

import math
import os
import sys
from urllib.parse import quote

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from integration_contracts.observations import (  # noqa: E402
    normalize_observation_report,
    observation_to_cot_like,
)


SIMULATED_POINTS_OF_INTEREST = [
    {
        "reportId": "obs.red-roof.01",
        "label": "Red roof",
        "category": "structure_feature",
        "confidence": 0.91,
        "position": {"lat": 44.40808, "lon": 26.31402, "alt": 88},
        "roofColor": "#cf3f37",
        "groundColor": "#6b7a53",
    },
    {
        "reportId": "obs.blue-roof.01",
        "label": "Blue roof",
        "category": "structure_feature",
        "confidence": 0.78,
        "position": {"lat": 44.40404, "lon": 26.31255, "alt": 86},
        "roofColor": "#416fc7",
        "groundColor": "#546b58",
    },
    {
        "reportId": "obs.light-yard.01",
        "label": "Light yard surface",
        "category": "infrastructure",
        "confidence": 0.72,
        "position": {"lat": 44.40618, "lon": 26.30320, "alt": 80},
        "roofColor": "#d8c98f",
        "groundColor": "#66715e",
    },
]


def generate_simulated_observation_reports(telemetry_items, seen_report_ids, mission_id=None, threshold_degrees=0.0014):
    """Emit each simulated observation once when a drone passes close enough."""
    reports = []
    for point in SIMULATED_POINTS_OF_INTEREST:
        if point["reportId"] in seen_report_ids:
            continue
        nearest = nearest_telemetry(point["position"], telemetry_items)
        if not nearest or nearest["distance"] > threshold_degrees:
            continue
        report = normalize_observation_report({
            "reportId": point["reportId"],
            "reportingNodeId": nearest["telemetry"]["nodeId"],
            "missionId": mission_id or nearest["telemetry"].get("missionId", ""),
            "label": point["label"],
            "category": point["category"],
            "confidence": point["confidence"],
            "position": point["position"],
            "imageDataUri": make_capture_data_uri(point),
            "source": "mock-observation-sensor",
        })
        report["cotLike"] = observation_to_cot_like(report)
        reports.append(report)
    return reports


def nearest_telemetry(position, telemetry_items):
    best = None
    for item in telemetry_items:
        item_position = item.get("position", {})
        distance = math.hypot(
            float(position["lat"]) - float(item_position.get("lat", 0.0)),
            float(position["lon"]) - float(item_position.get("lon", 0.0)),
        )
        candidate = {"telemetry": item, "distance": distance}
        if best is None or candidate["distance"] < best["distance"]:
            best = candidate
    return best


def make_capture_data_uri(point):
    label = escape_svg_text(point["label"])
    roof_color = point["roofColor"]
    ground_color = point["groundColor"]
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="220" height="132" viewBox="0 0 220 132">
<rect width="220" height="132" fill="{ground}"/>
<path d="M20 105 L72 64 L124 105 Z" fill="{roof}" stroke="#231f20" stroke-width="4"/>
<rect x="42" y="86" width="60" height="29" fill="#f1dfb5" stroke="#231f20" stroke-width="3"/>
<path d="M122 34 L178 20 L202 84 L144 100 Z" fill="{roof}" opacity=".92" stroke="#231f20" stroke-width="4"/>
<rect x="0" y="116" width="220" height="16" fill="#2f3a36"/>
<text x="12" y="22" fill="#ffffff" font-family="Arial" font-size="16" font-weight="700">{label}</text>
</svg>""".format(ground=ground_color, roof=roof_color, label=label)
    return "data:image/svg+xml;utf8," + quote(svg, safe="")


def escape_svg_text(value):
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def self_test():
    telemetry = [{
        "nodeId": "drone-01",
        "missionId": "mission-test",
        "position": {"lat": 44.4081, "lon": 26.3142, "alt": 88},
        "liveExecution": False,
    }]
    reports = generate_simulated_observation_reports(telemetry, set(), mission_id="mission-test")
    assert reports
    assert reports[0]["readOnly"] is True
    assert reports[0]["imageDataUri"].startswith("data:image/svg+xml")
    return reports


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))

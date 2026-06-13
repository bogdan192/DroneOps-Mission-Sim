#!/usr/bin/env python3
"""Local simulated drone runtime."""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from fleet_protocol import messages  # noqa: E402
from mission_core import mission_schema  # noqa: E402


class SimulatedDroneRuntime:
    """Executes a neutral simulation controller program."""

    def __init__(self, node_id, program):
        self.node_id = node_id
        self.program = program
        self.route = mission_schema.normalize_route(program["routeWaypoints"])
        self.battery_percent = 96.0
        self.state = "assigned"

    def telemetry_at(self, tick, total_ticks):
        progress = 0.0 if total_ticks <= 1 else min(1.0, tick / float(total_ticks - 1))
        position = interpolate_route(self.route, progress)
        self.battery_percent = max(20.0, 96.0 - tick * 0.4)
        if progress >= 1.0:
            self.state = "complete"
        else:
            self.state = "simulating"
        return {
            "type": "mission.telemetry",
            "schemaVersion": "0.1",
            "timestamp": messages.timestamp(),
            "nodeId": self.node_id,
            "missionId": self.program["missionId"],
            "state": self.state,
            "position": position,
            "batteryPercent": round(self.battery_percent, 1),
            "liveExecution": False,
        }


def interpolate_route(route, progress):
    if progress <= 0:
        return route_position(route[0])
    if progress >= 1:
        return route_position(route[-1])
    segments = len(route) - 1
    scaled = progress * segments
    index = min(segments - 1, int(scaled))
    fraction = scaled - index
    start = route[index]
    end = route[index + 1]
    return {
        "lat": round(lerp(start["lat"], end["lat"], fraction), 7),
        "lon": round(lerp(start["lon"], end["lon"], fraction), 7),
        "alt": round(lerp(start["alt"], end["alt"], fraction), 1),
    }


def route_position(point):
    return {
        "lat": float(point["lat"]),
        "lon": float(point["lon"]),
        "alt": float(point.get("alt", 80)),
    }


def lerp(start, end, fraction):
    return float(start) + (float(end) - float(start)) * fraction


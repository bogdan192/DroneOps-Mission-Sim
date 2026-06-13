#!/usr/bin/env python3
"""Simulation mission session state for the control station."""

import threading
import time

from atak_tracking.tracker import AtakDroneTracker
from fleet_protocol import messages
from mission_core import mission_schema
from onboard_node.node import DEFAULT_ROUTE, OnboardNode
from sim_adapters.fleet import build_simulated_fleet
from sim_adapters.runtime import SimulatedDroneRuntime, lerp, route_position
from sim_adapters.transport import InMemoryTakNetwork


class ControlStationMissionSession:
    """Owns one simulation mission timeline for the control station API."""

    def __init__(self):
        self.lock = threading.Lock()
        self.tracker = AtakDroneTracker()
        self.reset()

    def reset(self):
        self.tracker = AtakDroneTracker()
        self.order = "coordinate with peers and simulate the Bucharest outskirts route"
        self.node_count = 4
        self.total_ticks = 18
        self.tick_seconds = 0.7
        self.route_waypoints = DEFAULT_ROUTE
        self.started_at = None
        self.mission = None
        self.assignment_plan = None
        self.controller_programs = []
        self.runtimes = []
        self.available_fleet = build_simulated_fleet(self.node_count)
        self.selected_node_ids = [node["nodeId"] for node in self.available_fleet]
        self.live_orders = {}
        self.network = None
        self.latest_telemetry = []
        self.status = "idle"

    def start(self, order=None, node_count=4, ticks=18, tick_seconds=0.7, route_waypoints=None, selected_node_ids=None):
        with self.lock:
            self.reset()
            self.order = str(order or self.order)
            self.node_count = max(1, min(12, int(node_count)))
            self.total_ticks = max(2, min(300, int(ticks)))
            self.tick_seconds = max(0.1, min(10.0, float(tick_seconds)))
            self.route_waypoints = mission_schema.normalize_route(route_waypoints or DEFAULT_ROUTE)

            self.network = InMemoryTakNetwork()
            self.available_fleet = build_simulated_fleet(self.node_count)
            all_ids = [node["nodeId"] for node in self.available_fleet]
            selected = selected_node_ids or all_ids
            selected_set = set(str(node_id) for node_id in selected if str(node_id) in all_ids)
            if not selected_set:
                raise ValueError("select at least one available drone")
            self.selected_node_ids = sorted(selected_set)
            fleet_status = [node for node in self.available_fleet if node["nodeId"] in selected_set]

            leader = OnboardNode(fleet_status[0]["nodeId"], position=fleet_status[0]["position"])
            self.network.publish("order.intent", messages.order_intent(
                "order-web-001",
                self.order,
                route_waypoints=self.route_waypoints,
            ))
            for status in self.available_fleet:
                self.network.publish("node.status", status)

            onboard_result = leader.handle_order(
                self.order,
                route_waypoints=self.route_waypoints,
                fleet_status=fleet_status,
            )
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
                program = leader.compile_controller_program(assignment["nodeId"], self.mission, assignment)
                self.controller_programs.append(program)
                self.runtimes.append(SimulatedDroneRuntime(assignment["nodeId"], program))

            self.started_at = time.time()
            self.status = "running"
            self._advance_locked()
            return self.snapshot_locked()

    def apply_live_order(self, targets, command):
        with self.lock:
            if not self.started_at:
                raise ValueError("start a mission before issuing live orders")
            command = str(command or "").strip().lower()
            if command not in ("hold", "resume", "return_to_start"):
                raise ValueError("unsupported live order: {}".format(command))
            runtime_ids = [runtime.node_id for runtime in self.runtimes]
            if targets in (None, [], "all"):
                selected_targets = runtime_ids
            else:
                selected_targets = [str(target) for target in targets if str(target) in runtime_ids]
            if not selected_targets:
                raise ValueError("no selected executing drones match this order")

            tick = self.current_tick_locked()
            current_by_id = {item["nodeId"]: item for item in self.latest_telemetry}
            for node_id in selected_targets:
                if command == "resume":
                    self.live_orders.pop(node_id, None)
                elif command == "hold":
                    current = current_by_id.get(node_id) or self._runtime_telemetry(node_id, tick)
                    self.live_orders[node_id] = {
                        "command": "hold",
                        "position": current["position"],
                        "issuedAtTick": tick,
                    }
                elif command == "return_to_start":
                    current = current_by_id.get(node_id) or self._runtime_telemetry(node_id, tick)
                    self.live_orders[node_id] = {
                        "command": "return_to_start",
                        "from": current["position"],
                        "to": route_position(self.route_waypoints[0]),
                        "issuedAtTick": tick,
                        "durationTicks": 10,
                    }
                self.network.publish("live.order", {
                    "type": "live.order",
                    "schemaVersion": "0.1",
                    "timestamp": messages.timestamp(),
                    "missionId": self.mission["missionId"],
                    "nodeId": node_id,
                    "command": command,
                    "liveExecution": False,
                })
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
            "availableDrones": self.available_fleet,
            "selectedNodeIds": self.selected_node_ids,
            "routeWaypoints": self.route_waypoints,
            "totalTicks": self.total_ticks,
            "currentTick": self.current_tick_locked(),
            "mission": self.mission,
            "assignmentPlan": self.assignment_plan,
            "controllerPrograms": self.controller_programs,
            "telemetry": self.latest_telemetry,
            "atakDrones": self.tracker.snapshot()["drones"],
            "networkTopics": self.network_topics_locked(),
            "liveOrders": self.live_orders,
            "safety": {
                "llmDirectControllerAccess": False,
                "rawControllerCommands": False,
                "realDroneCommands": False,
            },
        }

    def current_tick_locked(self):
        if not self.started_at:
            return 0
        return min(self.total_ticks - 1, int((time.time() - self.started_at) / self.tick_seconds))

    def network_topics_locked(self):
        if not self.network:
            return []
        return sorted(set(event["topic"] for event in self.network.events))

    def _advance_locked(self):
        if not self.started_at or not self.runtimes:
            return
        tick = self.current_tick_locked()
        telemetry = []
        for runtime in self.runtimes:
            item = self._telemetry_with_live_order(runtime, tick)
            telemetry.append(item)
            self.network.publish("mission.telemetry", item)
        self.latest_telemetry = telemetry
        self.tracker.update_from_telemetry(telemetry)
        if tick >= self.total_ticks - 1:
            self.status = "complete"

    def _runtime_telemetry(self, node_id, tick):
        for runtime in self.runtimes:
            if runtime.node_id == node_id:
                return runtime.telemetry_at(tick, self.total_ticks)
        raise ValueError("unknown runtime node: {}".format(node_id))

    def _telemetry_with_live_order(self, runtime, tick):
        order = self.live_orders.get(runtime.node_id)
        if not order:
            return runtime.telemetry_at(tick, self.total_ticks)
        if order["command"] == "hold":
            return self._manual_telemetry(runtime, order["position"], "holding", tick)
        if order["command"] == "return_to_start":
            elapsed = max(0, tick - int(order["issuedAtTick"]))
            fraction = min(1.0, elapsed / float(order["durationTicks"]))
            position = {
                "lat": round(lerp(order["from"]["lat"], order["to"]["lat"], fraction), 7),
                "lon": round(lerp(order["from"]["lon"], order["to"]["lon"], fraction), 7),
                "alt": round(lerp(order["from"]["alt"], order["to"]["alt"], fraction), 1),
            }
            state = "complete" if fraction >= 1.0 else "returning"
            return self._manual_telemetry(runtime, position, state, tick)
        return runtime.telemetry_at(tick, self.total_ticks)

    def _manual_telemetry(self, runtime, position, state, tick):
        runtime.battery_percent = max(20.0, 96.0 - tick * 0.4)
        return {
            "type": "mission.telemetry",
            "schemaVersion": "0.1",
            "timestamp": messages.timestamp(),
            "nodeId": runtime.node_id,
            "missionId": runtime.program["missionId"],
            "state": state,
            "position": position,
            "batteryPercent": round(runtime.battery_percent, 1),
            "liveExecution": False,
        }


LiveMissionState = ControlStationMissionSession


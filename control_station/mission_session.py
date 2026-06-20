#!/usr/bin/env python3
"""Simulation mission session state for the control station."""

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from atak_tracking.tracker import AtakDroneTracker
from fleet_protocol import messages
from mission_core import mission_io, mission_schema
from onboard_node.node import DEFAULT_ROUTE, OnboardNode
from integration_contracts.atak_telemetry import atak_track_to_external_asset, normalize_atak_track
from integration_contracts.drone_connectors import (
    normalize_atak_drone_registration,
    normalize_node_order,
    normalize_node_order_result,
)
from integration_contracts.observations import normalize_observation_report
from sim_adapters.atak_feeds import build_simulated_atak_tracks
from sim_adapters.drone_connectors import (
    apply_simulated_heartbeat,
    build_simulated_atak_drone_registrations,
    build_simulated_drone_middleware_connectors,
)
from sim_adapters.external_assets import build_simulated_external_assets
from sim_adapters.fleet import build_simulated_fleet
from sim_adapters.observations import generate_simulated_observation_reports
from sim_adapters.runtime import SimulatedDroneRuntime, lerp, route_position
from sim_adapters.transport import InMemoryTakNetwork


class ControlStationMissionSession:
    """Owns one simulation mission timeline for the control station API."""

    CONNECTOR_STALE_SECONDS = 10.0

    def __init__(self, mission_store_dir=None):
        self.lock = threading.Lock()
        self.mission_store_dir = Path(mission_store_dir) if mission_store_dir else mission_io.default_mission_store_dir()
        self.tracker = AtakDroneTracker()
        self.reset()

    def reset(self, preserve_connectors=False):
        preserved_connectors = list(getattr(self, "atak_drone_connectors", [])) if preserve_connectors else []
        self.tracker = AtakDroneTracker()
        self.order = "coordinate with peers and simulate the Bucharest outskirts route"
        self.node_count = 4
        self.total_ticks = 18
        self.return_home_ticks = 10
        self.tick_seconds = 0.7
        self.route_waypoints = DEFAULT_ROUTE
        self.started_at = None
        self.mission = None
        self.assignment_plan = None
        self.controller_programs = []
        self.mission_artifacts = []
        self.runtimes = []
        self.available_fleet = build_simulated_fleet(self.node_count)
        self.atak_drone_connectors = build_simulated_atak_drone_registrations()
        self.atak_drone_connectors = self._merge_connectors(self.atak_drone_connectors, preserved_connectors)
        self.drone_middleware_connectors = build_simulated_drone_middleware_connectors()
        self.atak_tracks = build_simulated_atak_tracks()
        self.external_assets = build_simulated_external_assets()
        self.observation_reports = []
        self.reported_observation_ids = set()
        self.node_orders = []
        self.node_order_results = []
        self.selected_node_ids = [node["nodeId"] for node in self.available_fleet]
        self.live_orders = {}
        self.auto_rth_announced = False
        self.network = None
        self.latest_telemetry = []
        self.status = "idle"
        self._refresh_available_fleet_locked()

    def start(self, order=None, node_count=4, ticks=18, tick_seconds=0.7, route_waypoints=None, selected_node_ids=None):
        with self.lock:
            self.reset(preserve_connectors=True)
            self.order = str(order or self.order)
            self.node_count = max(1, min(12, int(node_count)))
            self.total_ticks = max(2, min(300, int(ticks)))
            self.tick_seconds = max(0.1, min(10.0, float(tick_seconds)))
            self.route_waypoints = mission_schema.normalize_route(route_waypoints or DEFAULT_ROUTE)

            self.network = InMemoryTakNetwork()
            self._refresh_available_fleet_locked()
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
            self.mission_artifacts = self._persist_mission_artifacts_locked()
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

    def cot_snapshot(self):
        with self.lock:
            self._advance_locked()
            return {
                "mode": "SIMULATION_ONLY",
                "readOnly": True,
                "liveExecution": False,
                "events": self.network.cot_snapshot() if self.network else [],
            }

    def observations_snapshot(self):
        with self.lock:
            self._advance_locked()
            return list(self.observation_reports)

    def connector_snapshot(self):
        with self.lock:
            return {
                "mode": "SIMULATION_ONLY",
                "readOnly": True,
                "atakDroneConnectors": list(self.atak_drone_connectors),
                "droneMiddlewareConnectors": list(self.drone_middleware_connectors),
                "telemetryFreshness": self.telemetry_freshness_locked(),
                "nodeOrders": list(self.node_orders),
                "nodeOrderResults": list(self.node_order_results),
            }

    def current_mission_dsl(self):
        with self.lock:
            if not self.mission:
                return None
            return dict(self.mission)

    def persisted_missions(self):
        with self.lock:
            return mission_io.list_mission_dsl(self.mission_store_dir)

    def current_route_geojson(self):
        with self.lock:
            properties = {"missionId": self.mission["missionId"]} if self.mission else {}
            return mission_io.route_to_geojson(self.route_waypoints, properties)

    def import_route_geojson(self, payload):
        with self.lock:
            if self.status in ("running", "returning_home"):
                raise ValueError("route import is only available while planning or after mission completion")
            self.route_waypoints = mission_io.route_from_geojson(payload)
            return self.snapshot_locked()

    def register_atak_drone_connector(self, registration):
        with self.lock:
            normalized = normalize_atak_drone_registration(registration)
            replaced = False
            updated = []
            for item in self.atak_drone_connectors:
                if item["nodeId"] == normalized["nodeId"]:
                    updated.append(normalized)
                    replaced = True
                else:
                    updated.append(item)
            if not replaced:
                updated.append(normalized)
            self.atak_drone_connectors = updated
            self._refresh_available_fleet_locked()
            self._upsert_atak_track_from_connector_locked(normalized)
            if self.network:
                self.network.publish("connector.atak_drone.registration", normalized)
            return self.connector_snapshot_locked()

    def update_atak_drone_heartbeat(self, heartbeat):
        with self.lock:
            self.atak_drone_connectors = apply_simulated_heartbeat(self.atak_drone_connectors, heartbeat)
            latest = next((item for item in self.atak_drone_connectors if item["nodeId"] == str(heartbeat.get("nodeId") or heartbeat.get("uid"))), None)
            if latest:
                self._upsert_atak_track_from_connector_locked(latest)
                self._refresh_available_fleet_locked()
            if self.network and latest:
                self.network.publish("connector.atak_drone.heartbeat", {
                    "type": "connector.atak_drone.heartbeat",
                    "schemaVersion": "0.1",
                    "nodeId": latest["nodeId"],
                    "state": latest["state"],
                    "lastHeartbeatIso": latest["lastHeartbeatIso"],
                    "readOnly": True,
                    "liveExecution": False,
                })
            return self.connector_snapshot_locked()

    def enqueue_node_order(self, order):
        with self.lock:
            normalized = normalize_node_order(order)
            self.node_orders.append(normalized)
            if self.network:
                self.network.publish("connector.node_order", normalized)
            return self.connector_snapshot_locked()

    def node_orders_for(self, node_id):
        with self.lock:
            node_id = str(node_id or "").strip()
            return [item for item in self.node_orders if item["nodeId"] == node_id]

    def record_node_order_result(self, result):
        with self.lock:
            normalized = normalize_node_order_result(result)
            self.node_order_results.append(normalized)
            if self.network:
                self.network.publish("connector.node_order_result", normalized)
            return self.connector_snapshot_locked()

    def add_observation_report(self, report):
        with self.lock:
            normalized = normalize_observation_report(report)
            if normalized["reportId"] in self.reported_observation_ids:
                self.observation_reports = [
                    item if item["reportId"] != normalized["reportId"] else normalized
                    for item in self.observation_reports
                ]
            else:
                self.reported_observation_ids.add(normalized["reportId"])
                self.observation_reports.append(normalized)
            if self.network:
                self.network.publish("observation.report", normalized)
            return self.snapshot_locked()

    def snapshot_locked(self):
        return {
            "mode": "SIMULATION_ONLY",
            "liveExecution": False,
            "status": self.status,
            "order": self.order,
            "nodeCount": self.node_count,
            "availableDrones": self.available_fleet,
            "atakDroneConnectors": self.atak_drone_connectors,
            "droneMiddlewareConnectors": self.drone_middleware_connectors,
            "missionArtifacts": self.mission_artifacts,
            "nodeOrders": self.node_orders,
            "nodeOrderResults": self.node_order_results,
            "atakTracks": self.atak_tracks,
            "externalAssets": self.external_assets,
            "observationReports": self.observation_reports,
            "selectedNodeIds": self.selected_node_ids,
            "routeWaypoints": self.route_waypoints,
            "missionTicks": self.total_ticks,
            "returnHomeTicks": self.return_home_ticks,
            "totalTicks": self.total_timeline_ticks_locked(),
            "currentTick": self.current_tick_locked(),
            "mission": self.mission,
            "assignmentPlan": self.assignment_plan,
            "controllerPrograms": self.controller_programs,
            "telemetry": self.latest_telemetry,
            "atakDrones": self.combined_drone_tracks_locked(),
            "networkTopics": self.network_topics_locked(),
            "liveOrders": self.live_orders,
            "telemetryFreshness": self.telemetry_freshness_locked(),
            "safety": {
                "llmDirectControllerAccess": False,
                "rawControllerCommands": False,
                "realDroneCommands": False,
            },
        }

    def _refresh_available_fleet_locked(self):
        fleet = build_simulated_fleet(self.node_count)
        existing_ids = {node["nodeId"] for node in fleet}
        for connector in self.atak_drone_connectors:
            node_id = connector.get("nodeId")
            if not node_id or node_id in existing_ids:
                continue
            if not connector.get("position"):
                continue
            fleet.append(self._connector_to_swarm_status(connector))
            existing_ids.add(node_id)
        self.available_fleet = sorted(fleet, key=lambda item: item["nodeId"])
        self.selected_node_ids = [node_id for node_id in self.selected_node_ids if node_id in existing_ids]

    def _connector_to_swarm_status(self, connector):
        capabilities = sorted(set(
            ["route", "survey", "relay"] +
            [str(item) for item in connector.get("capabilities", [])]
        ))
        role = "connected-headless" if "local_order_interpretation" in capabilities else "connected"
        status = messages.node_status(
            connector["nodeId"],
            connector["position"],
            battery_percent=connector.get("batteryPercent", 100.0),
            role=role,
            capabilities=capabilities,
            state=self._connector_state_with_freshness(connector, "available"),
        )
        status["source"] = "atak-drone-connector"
        status["callsign"] = connector.get("callsign", connector["nodeId"])
        status["platform"] = connector.get("platform", "unknown")
        status["readOnly"] = True
        status["liveExecution"] = False
        return status

    def combined_drone_tracks_locked(self):
        by_node_id = {item["nodeId"]: item for item in self.tracker.snapshot()["drones"]}
        for connector in self.atak_drone_connectors:
            if connector.get("position"):
                by_node_id[connector["nodeId"]] = self._connector_to_drone_track(connector)
        return sorted(by_node_id.values(), key=lambda item: item["nodeId"])

    def _connector_to_drone_track(self, connector):
        position = connector["position"]
        return {
            "uid": connector["nodeId"],
            "nodeId": connector["nodeId"],
            "callsign": connector.get("callsign", connector["nodeId"]),
            "source": "atak-drone-connector",
            "state": self._connector_state_with_freshness(connector, "online"),
            "missionId": self.mission["missionId"] if self.mission else None,
            "lat": float(position["lat"]),
            "lon": float(position["lon"]),
            "alt": float(position.get("alt", 0.0)),
            "batteryPercent": float(connector.get("batteryPercent", 0.0)),
            "liveExecution": False,
            "lastSeenEpoch": time.time(),
            "lastSeenIso": connector.get("lastHeartbeatIso"),
            "cotLike": {
                "event": {
                    "version": "2.0",
                    "uid": connector["nodeId"],
                    "type": "a-f-A-M-F-Q",
                    "how": "m-g",
                    "time": connector.get("lastHeartbeatIso"),
                    "start": connector.get("lastHeartbeatIso"),
                    "stale": connector.get("lastHeartbeatIso"),
                },
                "point": {
                    "lat": float(position["lat"]),
                    "lon": float(position["lon"]),
                    "hae": float(position.get("alt", 0.0)),
                    "ce": 10.0,
                    "le": 10.0,
                },
                "detail": {
                    "contact": {"callsign": connector.get("callsign", connector["nodeId"])},
                    "status": {
                        "state": self._connector_state_with_freshness(connector, "online"),
                        "batteryPercent": connector.get("batteryPercent"),
                        "platform": connector.get("platform", "unknown"),
                    },
                },
            },
        }

    def _merge_connectors(self, base, extra):
        merged = {item["nodeId"]: item for item in base}
        for item in extra:
            merged[item["nodeId"]] = item
        return sorted(merged.values(), key=lambda item: item["nodeId"])

    def connector_snapshot_locked(self):
        return {
            "mode": "SIMULATION_ONLY",
            "readOnly": True,
            "atakDroneConnectors": list(self.atak_drone_connectors),
            "droneMiddlewareConnectors": list(self.drone_middleware_connectors),
            "telemetryFreshness": self.telemetry_freshness_locked(),
            "nodeOrders": list(self.node_orders),
            "nodeOrderResults": list(self.node_order_results),
        }

    def telemetry_freshness_locked(self):
        return [self._connector_freshness(connector) for connector in self.atak_drone_connectors]

    def _connector_state_with_freshness(self, connector, available_state):
        state = connector.get("state", available_state)
        if state in ("online", "registered", "available") and not self._connector_freshness(connector)["fresh"]:
            return "stale"
        if state in ("online", "registered", "available"):
            return available_state
        return state

    def _connector_freshness(self, connector):
        heartbeat = connector.get("lastHeartbeatIso")
        age = self._iso_age_seconds(heartbeat)
        fresh = age is not None and age <= self.CONNECTOR_STALE_SECONDS
        return {
            "nodeId": connector.get("nodeId"),
            "lastHeartbeatIso": heartbeat,
            "ageSeconds": None if age is None else round(age, 2),
            "fresh": bool(fresh),
            "staleAfterSeconds": self.CONNECTOR_STALE_SECONDS,
        }

    def _iso_age_seconds(self, value):
        if not value:
            return None
        try:
            parsed = datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
        return max(0.0, datetime.now(timezone.utc).timestamp() - parsed.timestamp())

    def _persist_mission_artifacts_locked(self):
        artifacts = []
        mission_artifact = mission_io.save_mission_dsl(self.mission, self.mission_store_dir)
        mission_artifact["kind"] = "mission_dsl"
        artifacts.append(mission_artifact)

        route_path = self.mission_store_dir / "{}.route.geojson".format(self.mission["missionId"])
        route_geojson = mission_io.route_to_geojson(self.route_waypoints, {"missionId": self.mission["missionId"]})
        route_path.write_text(json.dumps(route_geojson, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        artifacts.append({
            "kind": "route_geojson",
            "missionId": self.mission["missionId"],
            "path": str(route_path),
            "bytes": route_path.stat().st_size,
        })
        return artifacts

    def _upsert_atak_track_from_connector_locked(self, connector):
        if not connector.get("position"):
            return
        track = normalize_atak_track({
            "uid": connector["nodeId"],
            "callsign": connector["callsign"],
            "cotType": "a-f-A-UAS",
            "domain": "air",
            "kind": "drone",
            "source": "atak-drone-connector",
            "status": connector.get("state", "online"),
            "position": connector["position"],
            "lastSeenIso": connector.get("lastHeartbeatIso"),
        })
        asset = atak_track_to_external_asset(track)
        self.atak_tracks = self._replace_by_id(self.atak_tracks, "uid", track)
        self.external_assets = self._replace_by_id(self.external_assets, "uid", asset)

    def _replace_by_id(self, items, key, replacement):
        replaced = False
        updated = []
        for item in items:
            if item.get(key) == replacement.get(key):
                updated.append(replacement)
                replaced = True
            else:
                updated.append(item)
        if not replaced:
            updated.append(replacement)
        return updated

    def current_tick_locked(self):
        if not self.started_at:
            return 0
        return min(self.total_timeline_ticks_locked() - 1, int((time.time() - self.started_at) / self.tick_seconds))

    def total_timeline_ticks_locked(self):
        return self.total_ticks + self.return_home_ticks

    def network_topics_locked(self):
        if not self.network:
            return []
        return sorted(set(event["topic"] for event in self.network.events))

    def _advance_locked(self):
        if not self.started_at or not self.runtimes:
            return
        tick = self.current_tick_locked()
        if tick >= self.total_ticks:
            self._announce_auto_rth_locked()
        telemetry = []
        for runtime in self.runtimes:
            item = self._telemetry_with_live_order(runtime, tick)
            telemetry.append(item)
            self.network.publish("mission.telemetry", item)
        self.latest_telemetry = telemetry
        self.tracker.update_from_telemetry(telemetry)
        self._collect_observations_locked(telemetry)
        if tick >= self.total_timeline_ticks_locked() - 1:
            self.status = "complete"
        elif tick >= self.total_ticks:
            self.status = "returning_home"
        else:
            self.status = "running"

    def _runtime_telemetry(self, node_id, tick):
        for runtime in self.runtimes:
            if runtime.node_id == node_id:
                return runtime.telemetry_at(min(tick, self.total_ticks - 1), self.total_ticks)
        raise ValueError("unknown runtime node: {}".format(node_id))

    def _telemetry_with_live_order(self, runtime, tick):
        if tick >= self.total_ticks:
            return self._auto_return_home_telemetry(runtime, tick)
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

    def _collect_observations_locked(self, telemetry):
        mission_id = self.mission["missionId"] if self.mission else ""
        reports = generate_simulated_observation_reports(
            telemetry,
            self.reported_observation_ids,
            mission_id=mission_id,
        )
        for report in reports:
            self.reported_observation_ids.add(report["reportId"])
            self.observation_reports.append(report)
            self.network.publish("observation.report", report)

    def _auto_return_home_telemetry(self, runtime, tick):
        elapsed = max(0, tick - self.total_ticks)
        fraction = min(1.0, elapsed / float(max(1, self.return_home_ticks - 1)))
        route_end = runtime.telemetry_at(self.total_ticks - 1, self.total_ticks)["position"]
        home = route_position(self.route_waypoints[0])
        position = {
            "lat": round(lerp(route_end["lat"], home["lat"], fraction), 7),
            "lon": round(lerp(route_end["lon"], home["lon"], fraction), 7),
            "alt": round(lerp(route_end["alt"], home["alt"], fraction), 1),
        }
        state = "complete" if fraction >= 1.0 else "returning_home"
        return self._manual_telemetry(runtime, position, state, tick)

    def _announce_auto_rth_locked(self):
        if self.auto_rth_announced:
            return
        self.auto_rth_announced = True
        for runtime in self.runtimes:
            self.network.publish("mission.return_home", {
                "type": "mission.return_home",
                "schemaVersion": "0.1",
                "timestamp": messages.timestamp(),
                "missionId": self.mission["missionId"],
                "nodeId": runtime.node_id,
                "command": "auto_return_to_home",
                "reason": "mission_complete",
                "home": route_position(self.route_waypoints[0]),
                "liveExecution": False,
            })

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

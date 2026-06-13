#!/usr/bin/env python3
"""Runtime contracts and safety gates shared by mock and future real adapters."""

from typing import Protocol


REAL_EXECUTION_ENABLED = False


class TransportAdapter(Protocol):
    def publish(self, topic, payload):
        """Publish a fleet/network event."""


class ControllerCompiler(Protocol):
    def __call__(self, node_id, mission, assignment):
        """Compile a validated mission assignment for one drone."""


class DroneRuntime(Protocol):
    node_id: str

    def telemetry_at(self, tick, total_ticks):
        """Return telemetry for a point in a simulated or replayed mission."""


def require_simulation_payload(payload, path="payload"):
    """Reject payloads that try to cross into real execution."""
    if isinstance(payload, dict):
        if "liveExecution" in payload and payload.get("liveExecution") is not False:
            raise ValueError("{} liveExecution must be false".format(path))
        if "mode" in payload and payload.get("mode") != "simulation":
            raise ValueError("{} mode must be simulation".format(path))
        for key, value in payload.items():
            require_simulation_payload(value, "{}.{}".format(path, key))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            require_simulation_payload(value, "{}[{}]".format(path, index))


def reject_real_execution(component_name):
    """Fail closed until a real adapter is deliberately implemented."""
    raise RuntimeError(
        "{} is not implemented in this repo. This project currently exposes "
        "schemas, safety validation, planner boundaries, and simulator adapters "
        "only. A real hardware adapter must be built and reviewed separately."
        .format(component_name)
    )

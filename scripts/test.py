#!/usr/bin/env python3
"""Cross-platform project checks for DroneOps Mission Sim."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SYNTAX_FILES = [
    "onboard_node/node.py",
    "mission_core/mission_schema.py",
    "integration_contracts/runtime.py",
    "integration_contracts/external_assets.py",
    "integration_contracts/observations.py",
    "fleet_protocol/messages.py",
    "fleet_protocol/coordinator.py",
    "sim_adapters/fleet.py",
    "sim_adapters/transport.py",
    "sim_adapters/runtime.py",
    "sim_adapters/external_assets.py",
    "sim_adapters/observations.py",
    "real_integrations/disabled_adapters.py",
    "controller_adapters/simulated_controller.py",
    "atak_tracking/tracker.py",
    "control_station/mission_session.py",
    "control_station/ui.py",
    "control_station/http_server.py",
    "control_station/app.py",
    "mock_runtime/mission_simulator.py",
    "live_web/server.py",
    "scripts/demo_launcher.py",
    "scripts/ui_smoke_test.py",
    "scripts/browser_ui_test.py",
    "scripts/run_browser_ui_tests.py",
    "tools/droneops_basestation/server.py",
    "tools/droneops_sim/sim_server.py",
    "tools/droneops_local_planner/droneops_planner.py",
]

SELF_TESTS = [
    ["mission_core/mission_schema.py"],
    ["integration_contracts/external_assets.py"],
    ["integration_contracts/observations.py"],
    ["fleet_protocol/coordinator.py"],
    ["sim_adapters/fleet.py"],
    ["sim_adapters/external_assets.py"],
    ["sim_adapters/observations.py"],
    ["controller_adapters/simulated_controller.py"],
    ["atak_tracking/tracker.py"],
    ["onboard_node/node.py", "--self-test"],
    ["mock_runtime/mission_simulator.py", "--self-test"],
    ["-m", "control_station.app", "--self-test"],
    ["live_web/server.py", "--self-test"],
    ["scripts/demo_launcher.py", "--smoke-test", "--port", "0"],
    ["scripts/ui_smoke_test.py"],
    ["tools/droneops_basestation/server.py", "--self-test"],
    ["tools/droneops_sim/sim_server.py", "--self-test", "--port", "0"],
]


def run(args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", *args]
    subprocess.run(command, cwd=ROOT, env=env, check=True, stdout=subprocess.DEVNULL)


def main():
    run(["scripts/check_syntax.py", *SYNTAX_FILES])
    for test_args in SELF_TESTS:
        run(test_args)
    print("DroneOps Mission Sim checks passed.")


if __name__ == "__main__":
    main()

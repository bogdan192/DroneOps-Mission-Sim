#!/usr/bin/env python3
"""Compatibility entrypoint for the DroneOps control station.

The implementation now lives in `control_station/`:

- `control_station.mission_session` owns simulation mission state.
- `control_station.http_server` owns HTTP API routing.
- `control_station.ui` owns browser UI rendering.
- `control_station.app` owns CLI startup and self-tests.
"""

import os
import sys


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "droneops_local_planner"))

from control_station.app import HOST, PORT, main, run_server, self_test  # noqa: E402,F401
from control_station.mission_session import ControlStationMissionSession, LiveMissionState  # noqa: E402,F401


if __name__ == "__main__":
    main()


# DroneOps PC Simulation Harness

This is a PC-side stand-in for the Android DroneOps plugin API. It lets the
basestation planner and local model workflow run without needing an Android
emulator, PX4, ArduPilot, MAVLink, or real aircraft.

It is intentionally simulation-only.

## Run A Self-Test

    python tools/droneops_sim/sim_server.py --self-test

## Run The Local API Server

    python tools/droneops_sim/sim_server.py

Default address:

    http://127.0.0.1:47147

Endpoints:

    GET /health
    GET /fleet
    POST /mission-intents

Submit a mocked order from the local planner:

    python tools/droneops_local_planner/droneops_planner.py --mock --submit "survey the north field and report coverage"

## Full Simulator Stack Later

The next step after this harness is one of:

- ArduPilot SITL + MAVProxy on WSL/Linux.
- PX4 SITL + Gazebo/JSBSim on WSL/Linux.
- Android emulator running ATAK + DroneOps, with `adb reverse` or host loopback
  routing for the local API.

This harness stays useful as the deterministic basestation test fixture even
after real SITL is added.

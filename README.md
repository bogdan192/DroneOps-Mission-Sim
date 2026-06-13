# DroneOps Mission Sim

Simulation-only prototype for an onboard drone autonomy node.

The project models the architecture where each drone carries a companion device
or Android/ATAK device that acts as a network node. That onboard node can receive
high-level orders, use a local LLM/planner to propose a mission, coordinate with
peer drones, and compile a validated controller program through an injected
adapter.

The basestation map remains useful, but it is now only one client. The core
concept is onboard autonomy with deterministic safety gates.

This project does not arm, launch, fly, or command a real aircraft.

## Architecture

```text
Basestation / peer / operator order
        |
        v
Onboard node API
        |
        v
Local LLM or deterministic planner
        |
        v
Mission DSL validation
        |
        v
Fleet protocol and task allocation
        |
        v
Controller adapter boundary
        |
        v
Simulation adapter today / future reviewed real adapter
```

The LLM is not a flight controller. It may propose structured mission intent.
Deterministic code validates and compiles that intent.

## Current Features

- Interactive Google Maps basestation UI.
- Onboard node prototype with `/health` and `/orders`.
- Mission DSL that forces `simulation` mode and `liveExecution: false`.
- Fleet message schema for node status, orders, and assignments.
- Deterministic multi-drone route-segment assignment.
- Simulation controller-program compiler.
- End-to-end mock mission runtime for the missing TAK/network/controller pieces.
- Live web mission tracker with an ATAK-style `/api/atak/drones` endpoint.
- Automatic simulated return-to-home phase after route mission ticks finish.
- Read-only simulated external ground/air asset tracks for integration planning.
- Control-station web code split into mission session, HTTP routing, UI, and
  CLI entrypoint modules.
- Local planner adapter with deterministic mock mode and optional Ollama mode.
- Explicit real-vs-mock boundary docs and fail-closed real adapter placeholders.

## Real vs Mock Boundary

The repo now separates reusable contracts from simulator-only code:

- Reusable contract/planning modules: `mission_core`, `fleet_protocol`,
  `integration_contracts`, `onboard_node`, and `atak_tracking`.
- Simulator-only modules: `sim_adapters`, `mock_runtime`, `live_web`, and
  `control_station`, and `tools/droneops_sim`.
- Disabled real placeholders: `real_integrations`.

Nothing in this repo is a real flight-control adapter. Real TAK, MAVLink,
PX4, or ArduPilot integration should be implemented as a new adapter package
against `integration_contracts`, with separate review and hardware/SITL
validation.

See [docs/REAL_VS_MOCK.md](docs/REAL_VS_MOCK.md).
See [docs/EXTERNAL_ASSET_INTEGRATION.md](docs/EXTERNAL_ASSET_INTEGRATION.md)
for the read-only external asset boundary.

## Quick Start

No-admin demo launch:

- Windows: double-click `Launch DroneOps Demo.cmd`
- macOS: double-click `Launch DroneOps Demo.command`

See [NO_ADMIN_QUICK_START.md](NO_ADMIN_QUICK_START.md).

Run checks on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Run checks on macOS or Linux:

```bash
python3 -B scripts/test.py
```

Run browser UI tests with automatic local dependency install:

```bash
python3 -B scripts/run_browser_ui_tests.py
```

Run basestation:

```bash
python3 -B tools/droneops_basestation/server.py
```

Run onboard node self-test:

```bash
python3 -B onboard_node/node.py --self-test
```

Run a full mocked mission:

```bash
python3 -B mock_runtime/mission_simulator.py
```

Run the live web tracker:

```bash
python3 -B -m control_station.app
```

Run onboard node API:

```bash
python3 -B onboard_node/node.py --node-id drone-01
```

Submit a local order:

```powershell
$body = @{
  order = "coordinate with peers and simulate the Bucharest outskirts route"
  routeWaypoints = @(
    @{ lat = 44.405700; lon = 26.301900; alt = 80 }
    @{ lat = 44.407400; lon = 26.307800; alt = 90 }
    @{ lat = 44.410200; lon = 26.314000; alt = 80 }
  )
} | ConvertTo-Json -Depth 6

Invoke-WebRequest -UseBasicParsing -Method POST -Uri http://127.0.0.1:8091/orders -ContentType "application/json" -Body $body
```

## Mock Mission Runtime

The mock runtime simulates the missing pieces around the onboard node:

- TAK/mesh message transport
- peer drone status messages
- mission proposal and assignment publication
- simulation controller-program execution
- telemetry updates

See [docs/MOCK_SIMULATION.md](docs/MOCK_SIMULATION.md).

## Live Tracking

The live tracking page is available at:

```text
http://127.0.0.1:8092
```

It displays simulated ATAK-style drone nodes moving in real time and exposes:

After the planned route ticks finish, all executing drones automatically enter
simulated return-to-home. The mission reaches `complete` only after they return
to the route start point.

```text
GET /api/atak/drones
```

Each drone opens a compact simulated parameter and Street View popup only when
its map icon is clicked or hovered.

See [docs/LIVE_WEB_TRACKING.md](docs/LIVE_WEB_TRACKING.md).

## Google Maps

```bash
export GOOGLE_MAPS_API_KEY="your-key"
python3 -B -m control_station.app
```

Windows PowerShell uses:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python -B -m control_station.app
```

## Ollama

```powershell
python onboard_node\node.py --ollama --model llama3.1:8b
```

Ollama output is validated before it can become a mission DSL object.

## Safety Boundary

All current flows force:

- `mode: "simulation"`
- `liveExecution: false`
- no raw MAVLink or actuator command fields
- validated route waypoints
- bounded operating area
- altitude and speed limits
- prohibited objective-language rejection

See [docs/SAFETY.md](docs/SAFETY.md).

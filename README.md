# DroneOps Mission Sim

Simulation-only prototype for an onboard drone autonomy node.

The project models the architecture where each drone carries a companion device
or Android/ATAK device that acts as a network node. That onboard node can receive
high-level orders, use a local LLM/planner to propose a mission, coordinate with
peer drones, and compile a validated simulation controller program.

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
Simulation controller adapter
        |
        v
Local simulated fleet / basestation visualization
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
- Local planner adapter with deterministic mock mode and optional Ollama mode.

## Quick Start

Run checks:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\test.ps1
```

Run basestation:

```powershell
python tools\droneops_basestation\server.py
```

Run onboard node self-test:

```powershell
python onboard_node\node.py --self-test
```

Run a full mocked mission:

```powershell
python mock_runtime\mission_simulator.py
```

Run the live web tracker:

```powershell
python live_web\server.py
```

Run onboard node API:

```powershell
python onboard_node\node.py --node-id drone-01
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

```text
GET /api/atak/drones
```

Each drone opens a simulated parameter and Street View popup when it first
starts mission execution. Drone rows and map markers can reopen the popup.

See [docs/LIVE_WEB_TRACKING.md](docs/LIVE_WEB_TRACKING.md).

## Google Maps

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python tools\droneops_basestation\server.py
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

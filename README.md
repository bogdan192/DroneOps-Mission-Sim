# DroneOps Mission Sim

Local, simulation-only mission planning demo for a drone basestation workflow.

The demo lets you open a web basestation, add or drag waypoints on a map, choose
a simulated drone count, and press `Simulate`. The backend validates a mission
intent and animates a local simulated fleet. An optional Ollama adapter can turn
natural-language orders into editable waypoints.

This project does not arm, launch, fly, or command a real aircraft.

## Current Features

- Interactive Google Maps basestation UI.
- Local canvas fallback when Google Maps is unavailable.
- Editable waypoint list with latitude, longitude, and altitude.
- Simulated fleet size from 1 to 12 drones.
- Local mission intent validation.
- Local planner adapter with deterministic mock mode and optional Ollama mode.
- Simulation-only API shaped like the ATAK DroneOps plugin prototype.

## Quick Start

From the project root:

```powershell
python -m py_compile tools\droneops_basestation\server.py tools\droneops_sim\sim_server.py tools\droneops_local_planner\droneops_planner.py
python tools\droneops_basestation\server.py --self-test
python tools\droneops_basestation\server.py
```

Open:

```text
http://127.0.0.1:8088
```

With Google Maps:

```powershell
$env:GOOGLE_MAPS_API_KEY="your-key"
python tools\droneops_basestation\server.py
```

Or use the convenience script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_basestation.ps1 -GoogleMapsApiKey "your-key"
```

With Ollama order interpretation:

```powershell
python tools\droneops_basestation\server.py --ollama --model llama3.1:8b
```

## Default Demo Area

The default route starts on Bucharest's eastern outskirts:

```text
44.405700, 26.301900
```

The UI also draws rough airport reference circles around Baneasa and Otopeni as
visual warnings. These are not authoritative UAS geographical zones and are not
legal clearance for real flight. Verify official Romanian UAS geo-zone data
before any real-world operation.

## Repository Map

```text
tools/droneops_basestation/     Web UI and basestation API
tools/droneops_sim/             Local simulated DroneOps/fleet API
tools/droneops_local_planner/   Local order-to-intent planner
docs/                           Architecture, setup, safety, roadmap
scripts/                        Convenience scripts
```

## Safety Boundary

All current flows force:

- `mode: "simulation"`
- `liveExecution: false`
- validated route waypoints
- bounded operating area
- altitude limits
- prohibited objective-language rejection

See [docs/SAFETY.md](docs/SAFETY.md).

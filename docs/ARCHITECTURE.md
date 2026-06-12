# Architecture

DroneOps Mission Sim is split into three local components.

## Basestation

Path: `tools/droneops_basestation/server.py`

The basestation is a local HTTP server on `127.0.0.1:8088`. It serves the web UI
and exposes:

- `GET /api/health`
- `GET /api/fleet`
- `POST /api/plan`
- `POST /api/simulate`

`/api/plan` interprets a text order into editable mission intent. `/api/simulate`
takes waypoints and drone count directly from the UI, validates them, configures
the simulated fleet, and starts animation.

## Simulation State

Path: `tools/droneops_sim/sim_server.py`

This module is the local stand-in for an ATAK DroneOps Android plugin or future
autopilot bridge. It keeps an in-memory fleet, accepts simulation mission
intents, and advances drone positions along route segments over time.

It can run embedded inside the basestation or as a separate local API.

## Planner

Path: `tools/droneops_local_planner/droneops_planner.py`

The planner converts natural-language orders into structured mission intent.
By default it runs deterministic mock parsing. With `--ollama`, it calls the
local Ollama API on `127.0.0.1:11434` and validates the model output.

The planner does not emit raw MAVLink, actuator, velocity, arming, or takeoff
commands.

## Data Flow

```text
User edits map
  -> POST /api/simulate
  -> route intent validation
  -> simulated fleet assignment
  -> GET /api/fleet polling
  -> map marker animation
```

Optional natural-language flow:

```text
User writes order
  -> POST /api/plan
  -> mock parser or Ollama
  -> validated editable routeWaypoints
  -> user reviews/edits
  -> POST /api/simulate
```


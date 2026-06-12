# DroneOps Local Planner

Machine-side local-model adapter for DroneOps.

This tool converts natural-language orders into simulation-only DroneOps mission
intent JSON. It is intentionally not a flight controller and does not emit raw
MAVLink, arming, takeoff, velocity, or actuator commands.

## Model Runtime

Recommended first runtime:

    Ollama on 127.0.0.1:11434

Ollama supports structured JSON outputs by passing a JSON schema in the
`format` field, which is why this tool uses it as the first adapter.

## Usage

Dry-run without a model:

    python tools/droneops_local_planner/droneops_planner.py --mock "survey the north field and report coverage"

Use a local Ollama model:

    python tools/droneops_local_planner/droneops_planner.py --model llama3.1:8b "survey the north field and report coverage"

Submit accepted simulation intent to DroneOps:

    python tools/droneops_local_planner/droneops_planner.py --model llama3.1:8b --submit "survey the bounded area and report coverage"

The default DroneOps API target is:

    http://127.0.0.1:47147

## Safety Contract

The planner:

- Forces `mode` to `simulation`.
- Forces `liveExecution` to `false`.
- Requires a bounded operating area.
- Caps speed at `20 m/s` for the current prototype.
- Rejects unsafe objective language such as attack, strike, weapon, or intercept.
- Rejects any model output containing raw command fields.

Future real-flight support should be added as a separate, explicit safety-gated
stage after SITL, hardware-in-loop, geofence, command authentication, audit
logging, and supervised approval are implemented.

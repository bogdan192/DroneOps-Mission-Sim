# Architecture

DroneOps Mission Sim now models an onboard autonomy-node architecture.

## Roles

### Basestation

The basestation is a client and visualization surface. It can create waypoints,
send orders, and display simulated fleet telemetry. It is not the center of all
autonomy.

The current browser basestation/control station lives in `control_station/`:

- `mission_session.py` owns simulation state.
- `http_server.py` owns HTTP API routing.
- `ui.py` owns browser presentation.
- `app.py` owns command-line startup.

`live_web/server.py` remains as a compatibility entrypoint only.

### Onboard Node

Path: `onboard_node/node.py`

The onboard node represents software that could run on a drone companion
computer or Android/ATAK device. It receives high-level orders and turns them
into validated mission intent. Controller output is produced through an injected
adapter.

Endpoints:

- `GET /health`
- `POST /orders`

The onboard node:

- publishes node status
- interprets or accepts route waypoints
- builds mission DSL
- coordinates with peer status messages
- compiles a controller program through an adapter boundary

### Mission Core

Path: `mission_core/mission_schema.py`

The mission DSL is the boundary between model reasoning and controller adapters.
It permits mission intent, constraints, operating area, and route waypoints. It
rejects raw controller command fields.

The current DSL deliberately forces `mode: "simulation"` and
`liveExecution: false`. It is reusable as a planning and validation contract,
not as a real flight-command schema.

### Fleet Protocol

Path: `fleet_protocol/`

Fleet messages are transport-neutral JSON dictionaries. They can later be sent
through TAK/CoT, HTTP, MQTT, or another authenticated link.

### Controller Adapters

Path: `controller_adapters/`

Only `simulated_controller.py` exists today. It compiles a neutral local
simulation program. Real PX4/ArduPilot adapters must be separate and safety
gated.

### Integration Contracts

Path: `integration_contracts/`

Contracts define the transport, controller compiler, and runtime boundaries used
by simulator adapters and future real adapters. The shared safety gate rejects
payloads that attempt live execution.

### Simulation Adapters

Path: `sim_adapters/`

Simulation adapters provide fake fleet inventory, in-memory TAK/mesh transport,
and synthetic route telemetry. They are the only implementations used by
`mock_runtime/` and `control_station/`.

### Real Integrations

Path: `real_integrations/`

This package currently contains fail-closed placeholders only. They exist to
make the missing real integration obvious, not to connect to hardware.

## Data Flow

```text
Order arrives at onboard node
  -> local LLM/planner proposes route intent
  -> mission DSL validator checks intent
  -> fleet coordinator assigns work among peer nodes
  -> injected controller adapter compiles a controller program
  -> telemetry/status can be visualized by the basestation
```

## Why This Shape

LLMs are useful for turning fuzzy orders into structured intent. They should not
directly control flight. Deterministic code should own validation, task
allocation, and controller-adapter output.

The early demo joined mock and reusable pieces so the mission loop could be
shown end-to-end. That coupling is useful for a prototype but misleading for
real integration work, so simulator pieces now sit behind explicit
`sim_adapters/` and fail-closed real placeholders.

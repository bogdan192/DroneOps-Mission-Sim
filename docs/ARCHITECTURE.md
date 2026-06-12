# Architecture

DroneOps Mission Sim now models an onboard autonomy-node architecture.

## Roles

### Basestation

The basestation is a client and visualization surface. It can create waypoints,
send orders, and display simulated fleet telemetry. It is not the center of all
autonomy.

### Onboard Node

Path: `onboard_node/node.py`

The onboard node represents software running on a drone companion computer or
Android/ATAK device. It receives high-level orders and turns them into validated
simulation work.

Endpoints:

- `GET /health`
- `POST /orders`

The onboard node:

- publishes node status
- interprets or accepts route waypoints
- builds mission DSL
- coordinates with peer status messages
- compiles a simulation controller program

### Mission Core

Path: `mission_core/mission_schema.py`

The mission DSL is the boundary between model reasoning and controller adapters.
It permits mission intent, constraints, operating area, and route waypoints. It
rejects raw controller command fields.

### Fleet Protocol

Path: `fleet_protocol/`

Fleet messages are transport-neutral JSON dictionaries. They can later be sent
through TAK/CoT, HTTP, MQTT, or another authenticated link.

### Controller Adapters

Path: `controller_adapters/`

Only `simulated_controller.py` exists today. It compiles a neutral local
simulation program. Real PX4/ArduPilot adapters must be separate and safety
gated.

## Data Flow

```text
Order arrives at onboard node
  -> local LLM/planner proposes route intent
  -> mission DSL validator checks intent
  -> fleet coordinator assigns work among peer nodes
  -> simulation adapter compiles local controller program
  -> telemetry/status can be visualized by the basestation
```

## Why This Shape

LLMs are useful for turning fuzzy orders into structured intent. They should not
directly control flight. Deterministic code should own validation, task
allocation, and controller-adapter output.


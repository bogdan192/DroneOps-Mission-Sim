# Onboard Node

The onboard node is the main project direction.

It represents the software carried by a drone on a companion computer or
Android/ATAK device. In a future system, this node would exchange status and
mission messages with other drones and with the basestation.

The node is orchestration code. It does not contain a hardware driver. Its
controller compiler is injected, and the default compiler is the simulation
adapter.

## Run

```powershell
python onboard_node\node.py --self-test
python onboard_node\node.py --node-id drone-01
```

Default API:

```text
http://127.0.0.1:8091
```

## Endpoints

### `GET /health`

Returns node identity, status, and simulation mode.

### `POST /orders`

Accepts:

```json
{
  "order": "coordinate with peers and simulate this route",
  "routeWaypoints": [
    { "lat": 44.4057, "lon": 26.3019, "alt": 80 },
    { "lat": 44.4074, "lon": 26.3078, "alt": 90 },
    { "lat": 44.4102, "lon": 26.3140, "alt": 80 }
  ],
  "fleetStatus": []
}
```

Returns:

- local node status
- validated mission DSL
- fleet assignment plan
- local assignment
- controller program from the configured adapter
- safety summary

## Local LLM Role

With `--ollama`, the node can ask a local model to interpret an order. The model
does not emit controller commands. It proposes mission structure which is then
validated by deterministic code.

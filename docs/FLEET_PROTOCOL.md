# Fleet Protocol

The fleet protocol is a small JSON message vocabulary for drone-to-drone and
drone-to-basestation coordination.

Current message types:

- `node.status`
- `order.intent`
- `mission.proposal`
- `mission.assignment`
- `mission.telemetry`

## Node Status

```json
{
  "type": "node.status",
  "schemaVersion": "0.1",
  "nodeId": "drone-01",
  "role": "leader-capable",
  "state": "available",
  "position": { "lat": 44.4057, "lon": 26.3019, "alt": 80 },
  "batteryPercent": 96,
  "capabilities": ["route", "survey", "relay"]
}
```

## Assignment

```json
{
  "type": "mission.assignment",
  "schemaVersion": "0.1",
  "missionId": "mission-123",
  "nodeId": "drone-01",
  "taskType": "route",
  "liveExecution": false,
  "routeWaypoints": []
}
```

## Transport

The message format is intentionally transport-neutral. Later adapters can send
these messages over:

- TAK/CoT
- local HTTP
- authenticated mesh transport
- MQTT
- custom radio links

Transport security is not implemented yet.


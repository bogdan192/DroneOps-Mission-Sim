# ATAK Bridge Scaffold

The ATAK bridge scaffold models how DroneOps fleet messages can move through an
Android headless node or future ATAK plugin without creating a real command
path.

It is simulation-only. It does not write to ATAK, upload routes, control
MAVLink, arm aircraft, or send actuator commands.

## Implemented Pieces

- `integration_contracts/atak_cot.py`
  - maps supported DroneOps fleet messages to CoT-like events
  - emits both JSON event fields and a compact XML string
  - keeps `readOnly: true` and `liveExecution: false`
- `integration_contracts/atak_bridge.py`
  - validates Android/ATAK bridge registration envelopes
  - validates bridge order envelopes
  - turns a safe bridge order into an onboard-node `/orders` payload
- `sim_adapters/transport.py`
  - projects in-memory fleet-network messages into CoT snapshots
- `GET /api/atak/cot`
  - exposes current simulated CoT events from the control station
- `scripts/atak_loopback_test.py`
  - starts a local onboard node
  - wraps an order in the Android/ATAK bridge envelope
  - posts it to `/orders`
  - verifies the generated mission and CoT projection remain simulation-only

## Bridge Registration Shape

```json
{
  "bridgeId": "android-emulator-loopback-01",
  "nodeId": "headless-node-loopback",
  "callsign": "Headless Loopback",
  "appPackage": "com.droneops.headless",
  "bridgeMode": "emulator-loopback",
  "interfaces": ["http-loopback", "cot-event-feed", "android-service"]
}
```

## CoT API

```text
GET /api/atak/cot
```

The response contains simulated CoT event projections:

```json
{
  "mode": "SIMULATION_ONLY",
  "readOnly": true,
  "liveExecution": false,
  "events": []
}
```

## Local Loopback

```bash
python3 -B scripts/atak_loopback_test.py
```

This is the current stand-in for an Android emulator plus onboard node loopback.
It is deliberately local and deterministic so it can run in CI and on laptops
without installing ATAK or touching a phone.

## Future Real ATAK Plugin Work

A real plugin bridge belongs outside simulator modules and must add:

- authentication and source allowlisting
- replay protection
- audit logging
- operator-visible source identity
- explicit separation between CoT situational awareness and command authority
- fail-closed handling for all real transport errors

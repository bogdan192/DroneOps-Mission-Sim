# Observation Reports

The control station can receive read-only observation reports from simulated
drones. A report contains the reporting drone, coordinates, a label, confidence,
and an image capture. The browser shows each report as a map pin and as a row in
the Observation Reports panel.

This feature is for situational awareness only. It does not support target
designation, weapon tasking, intercept guidance, or vehicle control.

## Current Implementation

- `integration_contracts/observations.py` defines the report schema, safety
  rejection rules, and CoT-like display mapping.
- `sim_adapters/observations.py` generates simulated image reports when drones
  pass points of interest on the demo route.
- `control_station/mission_session.py` stores reports, publishes
  `observation.report` events on the in-memory mock network, and includes
  `observationReports` in `/api/mission`.
- `control_station/http_server.py` exposes:
  - `GET /api/observations`
  - `POST /api/observations`
- `control_station/ui.py` renders observation pins, thumbnails, coordinates,
  confidence, and reporting-drone metadata.

## Report Shape

```json
{
  "type": "observation.report",
  "schemaVersion": "0.1",
  "reportId": "obs.red-roof.01",
  "reportingNodeId": "drone-01",
  "missionId": "mission-001",
  "label": "Red roof",
  "category": "structure_feature",
  "confidence": 0.91,
  "position": { "lat": 44.40808, "lon": 26.31402, "alt": 88 },
  "imageDataUri": "data:image/svg+xml;utf8,...",
  "source": "mock-observation-sensor",
  "readOnly": true,
  "liveExecution": false
}
```

`imageDataUri` must start with `data:image/`.

## Safety Boundary

The observation contract rejects operational fields such as `target`,
`tasking`, `weapon`, `engage`, `strike`, `attack`, and `intercept`.

Future real sensor ingest should be a reviewed adapter that produces this
read-only report shape. It should not import from `sim_adapters`,
`mock_runtime`, or `control_station`.

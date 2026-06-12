# Mission DSL

The mission DSL is the structured handoff between planning and execution.

It is designed so the LLM can help create intent without becoming a flight
controller.

## Example

```json
{
  "missionId": "mission-123",
  "source": "drone-01",
  "mode": "simulation",
  "liveExecution": false,
  "requiresHumanApproval": true,
  "objective": "simulate cooperative route",
  "constraints": {
    "geofenceRequired": true,
    "lostLinkAction": "return_to_launch",
    "maxAltitudeMeters": 100,
    "maxSpeedMetersPerSecond": 15,
    "minBatteryPercent": 35,
    "minSeparationMeters": 25
  },
  "operatingArea": [],
  "routeWaypoints": [],
  "tasks": []
}
```

## Rejected Content

The validator rejects raw controller fields, including:

- `mavlink`
- `mavlinkCommand`
- `actuator`
- `servo`
- `arm`
- `takeoff`
- `velocityCommand`
- `rcOverride`

Controller-specific translation belongs in a separate adapter behind safety
gates.


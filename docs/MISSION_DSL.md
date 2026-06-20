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

## Persistence

The control station persists every started mission DSL under:

```text
data/missions/<missionId>.json
```

The stored file is the validated mission object only. It keeps
`mode: "simulation"` and `liveExecution: false`; it does not contain raw
controller commands.

Useful local API endpoints:

```text
GET /api/mission/dsl
GET /api/missions
```

## GeoJSON Route Exchange

Routes can be exported and imported as GeoJSON `LineString` features:

```text
GET /api/mission/route.geojson
POST /api/mission/route/import-geojson
```

Coordinates use standard GeoJSON order:

```json
[lon, lat, alt]
```

Waypoint labels and altitudes are also mirrored in `properties.waypoints`.
Imported routes are normalized by the same mission DSL validator, including
latitude/longitude and altitude bounds.

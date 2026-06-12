# DroneOps Basestation Map

Local basestation web app for interactive route missions.

It lets you add/edit waypoints, choose a simulated fleet size, press
`Simulate`, and watch the route/fleet move on Google Maps or the local fallback
canvas. It can also interpret a natural-language order through the local
planner/Ollama adapter and turn that into editable waypoints.

## Run

Without Google Maps:

    python tools/droneops_basestation/server.py

With Google Maps JavaScript API:

    $env:GOOGLE_MAPS_API_KEY="your-key"
    python tools/droneops_basestation/server.py

Open:

    http://127.0.0.1:8088

## Example Order

    fly the route shown on the map and report position updates

The default route starts on Bucharest's eastern outskirts for demonstration.
It is intentionally away from the obvious Bucharest airport reference areas
drawn on the map, but it is not legal clearance. Always verify official UAS
geographical zones before any real flight.

## Notes

- Live flight execution is disabled.
- The planner creates `routeWaypoints`, not raw MAVLink commands.
- The interactive `Simulate` button posts validated route intent to the
  in-process simulation state.
- The default server uses the in-process simulation state. Later, it can point
  to ATAK/DroneOps on Android by replacing the local state adapter with HTTP
  calls to the plugin API.

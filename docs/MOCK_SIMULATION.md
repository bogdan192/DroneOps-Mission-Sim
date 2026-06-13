# Mock Mission Simulation

The mock runtime fills the missing pieces around the onboard autonomy node so
the full flow can be exercised locally.

It is a harness over `sim_adapters/`. It is not the place to add real TAK,
MAVLink, PX4, ArduPilot, radio, or phone integrations.

It mocks:

- TAK/mesh message transport
- peer drone status messages
- mission proposal publication
- assignment distribution
- controller-program execution
- telemetry updates
- automatic simulated return-to-home after the route timeline ends

It does not contact ATAK, a phone, a flight controller, or a real drone.

## Run

```powershell
python mock_runtime\mission_simulator.py
```

Print the full payload:

```powershell
python mock_runtime\mission_simulator.py --full
```

Run with more nodes:

```powershell
python mock_runtime\mission_simulator.py --nodes 6 --ticks 10
```

## Flow

```text
mock order
  -> sim_adapters.transport.InMemoryTakNetwork
  -> onboard node
  -> mission DSL
  -> fleet coordinator
  -> simulated controller programs
  -> sim_adapters.runtime.SimulatedDroneRuntime telemetry timeline
```

The result includes network topics, assignments, controller programs, and final
telemetry. Every generated controller program still has `liveExecution: false`.
After the route timeline ends, mock telemetry transitions through
`returning_home` and then `complete` once each selected drone reaches the route
start point.

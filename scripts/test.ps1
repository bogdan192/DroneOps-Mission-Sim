$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
  $PSNativeCommandUseErrorActionPreference = $true
}

python -m py_compile `
  onboard_node\node.py `
  mission_core\mission_schema.py `
  fleet_protocol\messages.py `
  fleet_protocol\coordinator.py `
  controller_adapters\simulated_controller.py `
  atak_tracking\tracker.py `
  mock_runtime\mission_simulator.py `
  live_web\server.py `
  tools\droneops_basestation\server.py `
  tools\droneops_sim\sim_server.py `
  tools\droneops_local_planner\droneops_planner.py

python mission_core\mission_schema.py | Out-Null
python fleet_protocol\coordinator.py | Out-Null
python controller_adapters\simulated_controller.py | Out-Null
python atak_tracking\tracker.py | Out-Null
python onboard_node\node.py --self-test | Out-Null
python mock_runtime\mission_simulator.py --self-test | Out-Null
python live_web\server.py --self-test | Out-Null
python tools\droneops_basestation\server.py --self-test | Out-Null
python tools\droneops_sim\sim_server.py --self-test | Out-Null

Write-Host "DroneOps Mission Sim checks passed."

$ErrorActionPreference = "Stop"

python -m py_compile `
  tools\droneops_basestation\server.py `
  tools\droneops_sim\sim_server.py `
  tools\droneops_local_planner\droneops_planner.py

python tools\droneops_basestation\server.py --self-test | Out-Null
python tools\droneops_sim\sim_server.py --self-test | Out-Null

Write-Host "DroneOps Mission Sim checks passed."


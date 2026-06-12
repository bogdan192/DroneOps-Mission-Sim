param(
  [string]$Order = "coordinate with peers and simulate the Bucharest outskirts route",
  [int]$Nodes = 4,
  [int]$Ticks = 8,
  [switch]$Full
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$argsList = @(
  "mock_runtime\mission_simulator.py",
  "--order",
  $Order,
  "--nodes",
  "$Nodes",
  "--ticks",
  "$Ticks"
)

if ($Full) {
  $argsList += "--full"
}

python @argsList


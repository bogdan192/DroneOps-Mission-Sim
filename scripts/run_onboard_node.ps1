param(
  [string]$NodeId = "drone-01",
  [switch]$Ollama,
  [string]$Model = "llama3.1:8b",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8091
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

$argsList = @(
  "onboard_node\node.py",
  "--node-id",
  $NodeId,
  "--host",
  $HostName,
  "--port",
  "$Port"
)

if ($Ollama) {
  $argsList += @("--ollama", "--model", $Model)
}

python @argsList


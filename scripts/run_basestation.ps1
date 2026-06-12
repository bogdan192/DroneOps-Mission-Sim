param(
  [string]$GoogleMapsApiKey = "",
  [switch]$Ollama,
  [string]$Model = "llama3.1:8b",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8088
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if ($GoogleMapsApiKey) {
  $env:GOOGLE_MAPS_API_KEY = $GoogleMapsApiKey
}

$argsList = @(
  "tools\droneops_basestation\server.py",
  "--host",
  $HostName,
  "--port",
  "$Port"
)

if ($Ollama) {
  $argsList += @("--ollama", "--model", $Model)
}

python @argsList


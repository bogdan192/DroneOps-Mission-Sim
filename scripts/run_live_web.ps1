param(
  [string]$GoogleMapsApiKey = "",
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8092
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

if ($GoogleMapsApiKey) {
  $env:GOOGLE_MAPS_API_KEY = $GoogleMapsApiKey
}

python live_web\server.py --host $HostName --port $Port


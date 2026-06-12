$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = "C:\Program Files\Python313\python.exe"
$out = Join-Path $PSScriptRoot "basestation.out.log"
$err = Join-Path $PSScriptRoot "basestation.err.log"

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "cmd.exe"
$psi.Arguments = "/c cd /d `"$root`" && `"$python`" tools\droneops_basestation\server.py --host 127.0.0.1 --port 8088 > `"$out`" 2> `"$err`""
$psi.WorkingDirectory = $root
$psi.UseShellExecute = $true
$psi.CreateNoWindow = $true
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
[System.Diagnostics.Process]::Start($psi) | Out-Null

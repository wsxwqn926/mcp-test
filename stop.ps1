$ErrorActionPreference = "SilentlyContinue"
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectDir ".pids"

if (Test-Path $pidFile) {
    $content = Get-Content $pidFile -Raw
    $parts = $content.Trim() -split ","
    foreach ($pidStr in $parts) {
        $pid = [int]$pidStr
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $pid -Force
            Write-Host "[OK] Stopped PID $pid ($($proc.ProcessName))" -ForegroundColor Green
        }
    }
    Remove-Item $pidFile -Force
}

$ports = @(8000, 5173)
foreach ($port in $ports) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "[OK] Stopped process on port $port (PID $($conn.OwningProcess))" -ForegroundColor Green
    }
}

Write-Host "[OK] All stopped" -ForegroundColor Green

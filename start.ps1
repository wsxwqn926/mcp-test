$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectDir

$backendPort = 8000
$frontendPort = 5173
$pidFile = Join-Path $projectDir ".pids"

function Check-Port($port) {
    try { return Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop } catch { return $null }
}

if ((Check-Port $backendPort) -or (Check-Port $frontendPort)) {
    Write-Host "[!] Port $backendPort or $frontendPort is in use, run stop.ps1 first" -ForegroundColor Yellow
    exit 1
}

$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Host "[!] python not found in PATH" -ForegroundColor Red
    exit 1
}

$npmCmd = (Get-Command npm -ErrorAction SilentlyContinue).Source
if (-not $npmCmd) {
    Write-Host "[!] npm not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "[*] Starting backend (FastAPI :$backendPort)..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath $pythonExe `
    -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "$backendPort" `
    -WorkingDirectory $projectDir `
    -PassThru

Write-Host "[*] Starting frontend (Vite :$frontendPort)..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath "cmd.exe" `
    -ArgumentList "/c", "npm run dev" `
    -WorkingDirectory (Join-Path $projectDir "frontend") `
    -PassThru

"$($backendProc.Id),$($frontendProc.Id)" | Set-Content $pidFile -Encoding UTF8

$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 500
    $b = Check-Port $backendPort
    $f = Check-Port $frontendPort
    if ($b -and $f) { $ok = $true; break }
    if ($b) { Write-Host "    Backend ready" -ForegroundColor Green }
    if (-not $b) { Write-Host "    Waiting backend..." -ForegroundColor DarkGray }
}

if ($ok) {
    Write-Host ""
    Write-Host "[OK] Started successfully!" -ForegroundColor Green
    Write-Host "     Backend:  http://localhost:$backendPort" -ForegroundColor White
    Write-Host "     Frontend: http://localhost:$frontendPort" -ForegroundColor White
    Write-Host ""
    Write-Host "Run ./stop.ps1 to stop" -ForegroundColor DarkGray
} else {
    Write-Host "[!] Startup timeout" -ForegroundColor Red
    if (-not (Check-Port $backendPort)) {
        Write-Host "    Backend failed" -ForegroundColor Red
    }
    if (-not (Check-Port $frontendPort)) {
        Write-Host "    Frontend failed" -ForegroundColor Red
    }
}

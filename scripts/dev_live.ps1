<#
.SYNOPSIS
    RLA 2 — Dev live: replay watcher + local API + Vite frontend.

.PARAMETER HostAddress
    API host. Default: 127.0.0.1

.PARAMETER Port
    API port. Default: 8765

.PARAMETER ReplayFolder
    Path to the Rocket League replays folder to watch.
    If omitted, the Path Resolver will be called to detect it automatically.

.EXAMPLE
    .\scripts\dev_live.ps1
    .\scripts\dev_live.ps1 -HostAddress 127.0.0.1 -Port 8765
    .\scripts\dev_live.ps1 -ReplayFolder "C:\Users\You\Documents\My Games\Rocket League\TAGame\DemosEpic"
#>

param(
    [string]$HostAddress   = "127.0.0.1",
    [int]   $Port          = 8765,
    [string]$ReplayFolder  = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $ProjectRoot "frontend"
$HealthUrl   = "http://${HostAddress}:${Port}/health"

Write-Host ""
Write-Host "RLA2 DEV LIVE" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "Project root : $ProjectRoot"
Write-Host "API address  : http://${HostAddress}:${Port}"
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── Verify frontend/ exists ───────────────────────────────────────────────────
if (-not (Test-Path $FrontendDir)) {
    Write-Host "ERROR: frontend/ not found at: $FrontendDir" -ForegroundColor Red
    exit 1
}

# ── Resolve replay folder if not provided ────────────────────────────────────
if ($ReplayFolder -eq "") {
    Write-Host "Resolving replay folder via Path Resolver..." -ForegroundColor Yellow
    try {
        $ReplayFolder = & python -c @"
import sys
sys.path.insert(0, r'$ProjectRoot')
from rla_app.config.paths import RLPathResolver
paths = RLPathResolver().resolve()
if paths.replays_dir:
    print(str(paths.replays_dir))
else:
    sys.exit(1)
"@
        if ($LASTEXITCODE -ne 0 -or $ReplayFolder -eq "") {
            Write-Host "ERROR: Path Resolver could not find a valid replays folder." -ForegroundColor Red
            Write-Host "Pass it explicitly with: -ReplayFolder <path>" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Replay folder : $ReplayFolder" -ForegroundColor DarkGray
    } catch {
        Write-Host "ERROR: failed to run Path Resolver: $_" -ForegroundColor Red
        Write-Host "Pass it explicitly with: -ReplayFolder <path>" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# ── 1. Start replay watcher in a new window ───────────────────────────────────
Write-Host "Starting replay watcher..." -ForegroundColor Yellow

$WatcherScript = @"
Set-Location '$ProjectRoot'
Write-Host 'RLA2 REPLAY WATCHER' -ForegroundColor Cyan
Write-Host 'Watching : $ReplayFolder'
Write-Host ''
python -m rla_app.replay_intake.watch_folder_dev '$ReplayFolder'
"@

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $WatcherScript

# ── 2. Start API in another new window ───────────────────────────────────────
Write-Host "Starting local API..." -ForegroundColor Yellow

$ApiScript = @"
Set-Location '$ProjectRoot'
Write-Host 'RLA2 API SERVER' -ForegroundColor Cyan
Write-Host 'Address : http://${HostAddress}:${Port}'
Write-Host ''
python -m rla_app.api.dev_dashboard_server --host $HostAddress --port $Port
"@

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $ApiScript

# ── 3. Wait for /health (up to 10 seconds) ───────────────────────────────────
Write-Host "Waiting for API health..." -ForegroundColor Yellow

$ready    = $false
$attempts = 20   # 20 x 500ms = 10s

for ($i = 0; $i -lt $attempts; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl `
                                      -UseBasicParsing `
                                      -TimeoutSec 1 `
                                      -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        # not ready yet
    }
}

if (-not $ready) {
    Write-Host ""
    Write-Host "ERROR: API did not respond at $HealthUrl within 10s." -ForegroundColor Red
    Write-Host "Check the API window for errors." -ForegroundColor Red
    exit 1
}

Write-Host "API ready." -ForegroundColor Green
Write-Host ""

# ── 4. Start Vite in current window ──────────────────────────────────────────
Write-Host "Starting Vite dev server..." -ForegroundColor Yellow
Write-Host ""

Push-Location $FrontendDir
try {
    npm run dev -- --force
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Vite exited with code $LASTEXITCODE." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: could not run npm: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
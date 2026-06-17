<#
.SYNOPSIS
    RLA 2 — Dev helper: start local API + Vite frontend in one command.

.PARAMETER HostAddress
    API host. Default: 127.0.0.1

.PARAMETER Port
    API port. Default: 8765

.EXAMPLE
    .\scripts\dev_full.ps1
    .\scripts\dev_full.ps1 -HostAddress 127.0.0.1 -Port 8765
#>

param(
    [string]$HostAddress = "127.0.0.1",
    [int]   $Port        = 8765
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot  = Split-Path -Parent $PSScriptRoot
$FrontendDir  = Join-Path $ProjectRoot "frontend"
$HealthUrl    = "http://${HostAddress}:${Port}/health"
$ApiCommand   = "python -m rla_app.api.dev_dashboard_server --host $HostAddress --port $Port"

Write-Host ""
Write-Host "RLA2 DEV FULL" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "Project root : $ProjectRoot"
Write-Host "API address  : http://${HostAddress}:${Port}"
Write-Host "Health check : $HealthUrl"
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Verify frontend/ exists before doing anything ─────────────────────────
if (-not (Test-Path $FrontendDir)) {
    Write-Host "ERROR: frontend/ directory not found at: $FrontendDir" -ForegroundColor Red
    exit 1
}

# ── 2. Start API in a new PowerShell window ───────────────────────────────────
Write-Host "Starting local API..." -ForegroundColor Yellow

$ApiScript = @"
Set-Location '$ProjectRoot'
Write-Host 'RLA2 API SERVER' -ForegroundColor Cyan
Write-Host 'Address : http://${HostAddress}:${Port}'
Write-Host ''
$ApiCommand
"@

Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", $ApiScript

# ── 3. Wait for /health (up to 10 seconds) ───────────────────────────────────
Write-Host "Waiting for API health..." -ForegroundColor Yellow

$ready      = $false
$maxSeconds = 10
$interval   = 0.5
$attempts   = [int]($maxSeconds / $interval)

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
        # not ready yet — keep waiting
    }
}

if (-not $ready) {
    Write-Host ""
    Write-Host "ERROR: API did not respond at $HealthUrl within ${maxSeconds}s." -ForegroundColor Red
    Write-Host "Check the API window for errors." -ForegroundColor Red
    exit 1
}

Write-Host "API ready." -ForegroundColor Green
Write-Host ""

# ── 4. Start Vite dev server in current window ────────────────────────────────
Write-Host "Starting Vite dev server..." -ForegroundColor Yellow
Write-Host ""

Push-Location $FrontendDir
try {
    npm run dev -- --force
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: Vite dev server exited with code $LASTEXITCODE." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: could not run npm: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
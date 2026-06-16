<#
.SYNOPSIS
    RLA 2 — Dev helper: export payload + launch frontend.

.PARAMETER Limit
    Max replays to load. Default: 50.

.PARAMETER RecentLimit
    Max recent matches in payload. Default: 5.

.PARAMETER Build
    Run `npm run build` instead of `npm run dev`.

.EXAMPLE
    .\scripts\dev_frontend.ps1
    .\scripts\dev_frontend.ps1 -Limit 100 -RecentLimit 10
    .\scripts\dev_frontend.ps1 -Build
#>

param(
    [int]   $Limit       = 50,
    [int]   $RecentLimit = 5,
    [switch]$Build
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ── Raíz del proyecto (un nivel arriba de scripts/) ──────────────────────────
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "RLA2 DEV FRONTEND" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "Project root : $ProjectRoot"
Write-Host "Limit        : $Limit"
Write-Host "RecentLimit  : $RecentLimit"
Write-Host "Mode         : $(if ($Build) { 'build' } else { 'dev server' })"
Write-Host "─────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host ""

# ── 1. Exportar payload ───────────────────────────────────────────────────────
Write-Host "Exporting dashboard payload..." -ForegroundColor Yellow

Push-Location $ProjectRoot
try {
    python -m rla_app.api.export_dashboard_compact_payload_dev $Limit $RecentLimit
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: payload export failed (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: could not run Python export: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host "Payload exported OK." -ForegroundColor Green
Write-Host ""

# ── 2. Frontend ───────────────────────────────────────────────────────────────
$FrontendDir = Join-Path $ProjectRoot "frontend"

if (-not (Test-Path $FrontendDir)) {
    Write-Host "ERROR: frontend/ directory not found at: $FrontendDir" -ForegroundColor Red
    exit 1
}

Push-Location $FrontendDir
try {
    if ($Build) {
        Write-Host "Running frontend build..." -ForegroundColor Yellow
        npm run build
    } else {
        Write-Host "Starting Vite dev server..." -ForegroundColor Yellow
        npm run dev -- --force
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: npm failed (exit code $LASTEXITCODE)." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host ""
    Write-Host "ERROR: could not run npm: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
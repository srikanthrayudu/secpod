# ─────────────────────────────────────────────────────────────────────────────
# QualityHub — Container Stack Runner (Windows PowerShell)
# Detects and runs using Podman or Docker Compose
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

# Navigate to project root (parent of scripts directory)
Set-Location -Path "$PSScriptRoot\.."

Write-Host ""
Write-Host "🚀  QualityHub — Container Stack Launcher (PowerShell)" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────────────"

# ── 1. Copy Environment Configuration if Missing ───────────────────────────
if (-not (Test-Path -Path ".env")) {
    Write-Host "⚙️   .env not found — copying from .env.example..."
    Copy-Item -Path ".env.example" -Destination ".env"
    Write-Host "   ✅  .env created. Review it before production use." -ForegroundColor Green
}

# ── 2. Detect Container Engine & Compose Tool ─────────────────────────────
$usePodman = $false
$useDocker = $false

if (Get-Command "podman" -ErrorAction SilentlyContinue) {
    if (Get-Command "podman-compose" -ErrorAction SilentlyContinue) {
        $usePodman = $true
    }
}

if (-not $usePodman -and (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    # Check if docker compose subcommand is available
    & docker compose version *>$null
    if ($LASTEXITCODE -eq 0) {
        $useDocker = $true
    }
}

# ── 3. Launch Stack ───────────────────────────────────────────────────────
if ($usePodman) {
    Write-Host "🐳  Container Platform Detected: Podman" -ForegroundColor Green
    Write-Host "🔄  Spinning up stack via podman-compose..."
    Write-Host ""
    podman-compose -f podman-compose.yml up --build
}
elseif ($useDocker) {
    Write-Host "🐳  Container Platform Detected: Docker" -ForegroundColor Green
    Write-Host "🔄  Spinning up stack via docker compose..."
    Write-Host ""
    docker compose -f podman-compose.yml up --build
}
else {
    Write-Host "❌ Error: No container platform or compose tool found." -ForegroundColor Red
    Write-Host "   Ensure you have one of the following installed and in your PATH:"
    Write-Host "   - Podman & Podman Compose (Windows CLI)"
    Write-Host "   - Docker Desktop & Docker Compose"
    exit 1
}

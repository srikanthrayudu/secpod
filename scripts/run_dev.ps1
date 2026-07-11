# ─────────────────────────────────────────────────────────────────────────────
# QualityHub — Local Development Runner (Windows PowerShell)
# Python 3.14+ | FastAPI | SQLite (zero-config)
# ─────────────────────────────────────────────────────────────────────────────
$ErrorActionPreference = "Stop"

# Navigate to project root (parent of scripts directory)
Set-Location -Path "$PSScriptRoot\.."

Write-Host ""
Write-Host "🚀  QualityHub — Local Dev (PowerShell)" -ForegroundColor Cyan
Write-Host "────────────────────────────────────────────────────"

# ── 1. Ensure Python 3.14 is installed ───────────────────────────────────────
$pythonCmd = ""
if (Get-Command "py" -ErrorAction SilentlyContinue) {
    # Check if py can run 3.14
    & py -3.14 --version *>$null
    if ($LASTEXITCODE -eq 0) {
        $pythonCmd = "py -3.14"
    }
}

if (-not $pythonCmd) {
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        $version = & python --version 2>&1
        if ($version -like "*3.14*") {
            $pythonCmd = "python"
        }
    }
}

if (-not $pythonCmd) {
    Write-Host "⚠️  Python 3.14 not found." -ForegroundColor Yellow
    Write-Host "   Please install Python 3.14 from python.org or via winget:"
    Write-Host "   winget install Python.Python.3.14"
    exit 1
}

# ── 2. Virtual Environment ────────────────────────────────────────────────
if (-not (Test-Path -Path ".venv")) {
    Write-Host "📦  Creating virtual environment (.venv)..."
    & Invoke-Expression "$pythonCmd -m venv .venv"
}

# Activate virtual environment
$env:PATH = "$(Get-Location)\.venv\Scripts;" + $env:PATH

# ── 3. Dependencies ───────────────────────────────────────────────────────
Write-Host "📥  Installing/verifying dependencies..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# ── 4. Environment ────────────────────────────────────────────────────────
if (-not (Test-Path -Path ".env")) {
    Write-Host "⚙️   .env not found — copying from .env.example..."
    Copy-Item -Path ".env.example" -Destination ".env"
    Write-Host "   ✅  .env created. Review it before production use." -ForegroundColor Green
}

# ── 5. Seed Database ──────────────────────────────────────────────────────
Write-Host "🌱  Seeding database with demo data..."
$env:PYTHONPATH = Get-Location
python scripts/seed.py

# ── 6. Summary ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "✅  Ready!" -ForegroundColor Green
Write-Host "   🌐  Dashboard:     http://localhost:8000" -ForegroundColor Blue
Write-Host "   📚  API Docs:      http://localhost:8000/docs" -ForegroundColor Blue
Write-Host "   🔑  Admin login:   admin@qualityhub.local / password123"
Write-Host "   👤  User login:    engineer@qualityhub.local / password123"
Write-Host ""
Write-Host "Press Ctrl+C to stop."
Write-Host "────────────────────────────────────────────────────"

# ── 7. Start Server ───────────────────────────────────────────────────────
$port = if ($env:PORT) { $env:PORT } else { 8000 }
$host_ip = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
uvicorn app.main:app --reload --port $port --host $host_ip

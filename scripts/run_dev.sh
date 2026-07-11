#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# QualityHub — Local Development Runner
# Python 3.14+ | FastAPI | SQLite (zero-config)
# ─────────────────────────────────────────────────────────────────────────────
set -e

# Navigate to project root regardless of where the script is invoked from
cd "$(dirname "$0")/.."

echo ""
echo "🚀  QualityHub — Local Dev"
echo "────────────────────────────────────────────────────"

# ── 1. Ensure Python 3.14 ──────────────────────────────────────────────────
if ! command -v python3.14 &>/dev/null && ! .venv/bin/python --version 2>&1 | grep -q "3\.14"; then
    echo "⚠️  Python 3.14 not found. Install it first:"
    echo "   sudo apt install python3.14 python3.14-venv  (Ubuntu/Debian)"
    echo "   brew install python@3.14                      (macOS)"
    exit 1
fi

# ── 2. Virtual Environment ────────────────────────────────────────────────
if [ ! -d ".venv" ]; then
    echo "📦  Creating virtual environment (.venv)..."
    python3.14 -m venv .venv
fi

source .venv/bin/activate

# ── 3. Dependencies ───────────────────────────────────────────────────────
echo "📥  Installing/verifying dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# ── 4. Environment ────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "⚙️   .env not found — copying from .env.example..."
    cp .env.example .env
    echo "   ✅  .env created. Review it before production use."
fi

# ── 5. Seed Database ──────────────────────────────────────────────────────
echo "🌱  Seeding database with demo data..."
PYTHONPATH=. python scripts/seed.py

# ── 6. Summary ────────────────────────────────────────────────────────────
echo ""
echo "✅  Ready!"
echo "   🌐  Dashboard:     http://localhost:8000"
echo "   📚  API Docs:      http://localhost:8000/docs"
echo "   🔑  Admin login:   admin@qualityhub.local / password123"
echo "   👤  User login:    engineer@qualityhub.local / password123"
echo ""
echo "Press Ctrl+C to stop."
echo "────────────────────────────────────────────────────"

# ── 7. Start Server ───────────────────────────────────────────────────────
PYTHONPATH=. uvicorn app.main:app \
    --reload \
    --port "${PORT:-8000}" \
    --host "${HOST:-0.0.0.0}" \
    --log-level "${LOG_LEVEL:-info}"

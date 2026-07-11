#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# QualityHub — Container Stack Runner
# Detects and runs using Podman or Docker Compose
# ─────────────────────────────────────────────────────────────────────────────
set -e

# Navigate to project root regardless of where the script is invoked from
cd "$(dirname "$0")/.."

echo ""
echo "🚀  QualityHub — Container Stack Dev Launcher"
echo "────────────────────────────────────────────────────"

# ── 1. Copy Environment Configuration if Missing ───────────────────────────
if [ ! -f ".env" ]; then
    echo "⚙️   .env not found — copying from .env.example..."
    cp .env.example .env
    echo "   ✅  .env created. Review it before production use."
fi

# ── 2. Detect Container Engine & Compose Tool ─────────────────────────────
USE_PODMAN=false
USE_DOCKER=false

# Check for Podman & Podman Compose
if command -v podman &>/dev/null && command -v podman-compose &>/dev/null; then
    USE_PODMAN=true
elif command -v docker &>/dev/null && docker compose version &>/dev/null; then
    USE_DOCKER=true
else
    # Fallback/Error checks
    echo "❌ Error: No container platform or compose tool found."
    echo "   Ensure you have one of the following installed:"
    echo "   - Podman & Podman Compose"
    echo "   - Docker & Docker Compose"
    exit 1
fi

# ── 3. Launch Stack ───────────────────────────────────────────────────────
if [ "$USE_PODMAN" = true ]; then
    echo "🐳  Container Platform Detected: Podman"
    echo "🔄  Spinning up stack via podman-compose..."
    echo ""
    podman-compose -f podman-compose.yml up --build
else
    echo "🐳  Container Platform Detected: Docker"
    echo "🔄  Spinning up stack via docker compose..."
    echo ""
    docker compose -f podman-compose.yml up --build
fi

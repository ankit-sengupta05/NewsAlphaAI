#!/usr/bin/env bash
# scripts/start_backend.sh  –  start the FastAPI backend
# Works on: Windows (Git Bash / WSL), macOS, Linux
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="unknown"
case "$(uname -s 2>/dev/null)" in
  Linux*)  OS="linux"   ;;
  Darwin*) OS="mac"     ;;
  CYGWIN*|MINGW*|MSYS*) OS="windows" ;;
  *) [ -n "$WINDIR" ] && OS="windows" ;;
esac

# ── Create .env if missing ────────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "⚠️   No .env found — copying .env.example"
  cp .env.example .env
  echo "    Please fill in your API keys in .env before proceeding."
fi

# ── Activate venv ─────────────────────────────────────────────────────────────
if [ "$OS" = "windows" ]; then
  ACTIVATE="venv/Scripts/activate"
  PYTHON="venv/Scripts/python"
else
  ACTIVATE="venv/bin/activate"
  PYTHON="venv/bin/python"
fi

if [ -f "$ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$ACTIVATE"
  echo "✅  Virtual environment activated"
else
  echo "❌  venv not found! Run setup first:"
  echo "    bash scripts/setup_python.sh"
  exit 1
fi

echo ""
echo "🚀  Starting NewsAlphaAI backend on http://localhost:8000"
echo "    Press Ctrl+C to stop"
echo ""

python -m uvicorn backend.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --log-level info

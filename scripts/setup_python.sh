#!/usr/bin/env bash
# scripts/setup_python.sh
# Cross-platform Python environment setup
# Works on: Windows (Git Bash / WSL), macOS, Linux
# ──────────────────────────────────────────────────────────────

set -e

# ── Move to project root regardless of where script is called from ────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "=================================================="
echo "   NewsAlphaAI — Python Environment Setup"
echo "=================================================="
echo ""

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="unknown"
case "$(uname -s 2>/dev/null)" in
  Linux*)   OS="linux"   ;;
  Darwin*)  OS="mac"     ;;
  CYGWIN*)  OS="windows" ;;
  MINGW*)   OS="windows" ;;
  MSYS*)    OS="windows" ;;
  *)
    if [ -n "$WINDIR" ] || [ -n "$windir" ]; then
      OS="windows"
    fi
    ;;
esac

echo "📌  Detected OS : $OS"
echo "📌  Project root: $PROJECT_ROOT"
echo ""

# ── Check Python is available ──────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python python3.12 python3.11 python3.10; do
  if command -v "$cmd" &>/dev/null; then
    MAJOR=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    MINOR=$("$cmd" -c "import sys; print(sys.version_info.minor)" 2>/dev/null)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
      PYTHON="$cmd"
      echo "✅  Found Python : $cmd ($("$cmd" --version 2>&1))"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  echo "❌  Python 3.10+ not found!"
  echo ""
  if [ "$OS" = "windows" ]; then
    echo "    Download from: https://python.org/downloads"
    echo "    ⚠  Check 'Add Python to PATH' during install"
  elif [ "$OS" = "mac" ]; then
    echo "    Run: brew install python@3.11"
  else
    echo "    Run: sudo apt install python3.11 python3.11-venv python3-pip"
  fi
  echo ""
  exit 1
fi

# ── Remove old venv if it exists ───────────────────────────────────────────────
if [ -d "venv" ]; then
  echo "♻️   Removing existing venv…"
  rm -rf venv
fi

# ── Create virtual environment ────────────────────────────────────────────────
echo "🐍  Creating virtual environment with $PYTHON…"
"$PYTHON" -m venv venv

# ── Determine activate script + pip path (OS-aware) ───────────────────────────
if [ "$OS" = "windows" ]; then
  ACTIVATE="venv/Scripts/activate"
  PIP="venv/Scripts/pip"
  PYTHON_VENV="venv/Scripts/python"
else
  ACTIVATE="venv/bin/activate"
  PIP="venv/bin/pip"
  PYTHON_VENV="venv/bin/python"
fi

# ── Activate the venv ─────────────────────────────────────────────────────────
# shellcheck disable=SC1090
source "$ACTIVATE"

echo "✅  Virtual environment created and activated"
echo ""

# ── Upgrade pip + setuptools ──────────────────────────────────────────────────
echo "⬆️   Upgrading pip, setuptools, wheel…"
"$PYTHON_VENV" -m pip install --upgrade pip setuptools wheel --quiet
echo "✅  pip upgraded to $("$PIP" --version | awk '{print $2}')"
echo ""

# ── Install backend dependencies ──────────────────────────────────────────────
if [ ! -f "backend/requirements.txt" ]; then
  echo "❌  backend/requirements.txt not found!"
  echo "    Make sure you are running this from the project root."
  exit 1
fi

echo "📦  Installing backend dependencies (this may take 3–5 minutes)…"
echo "    (PyTorch + Transformers + LangChain + ChromaDB + XGBoost…)"
echo ""

"$PIP" install -r backend/requirements.txt

echo ""
echo "✅  All dependencies installed!"
echo ""

# ── Windows-specific: bitsandbytes fix ────────────────────────────────────────
if [ "$OS" = "windows" ]; then
  echo "🪟  Windows detected — applying bitsandbytes compatibility fix…"
  "$PIP" install bitsandbytes --prefer-binary --quiet 2>/dev/null || {
    echo "⚠️   bitsandbytes install failed (normal on Windows without CUDA)."
    echo "    4-bit quantization will be disabled automatically."
  }
  echo ""
fi

# ── Create .env from example if not already present ───────────────────────────
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "📄  Created .env from .env.example"
    echo "    ⚠️  Open .env and fill in your API keys before running!"
  fi
else
  echo "📄  .env already exists — skipping copy"
fi
echo ""

# ── Create data directories ────────────────────────────────────────────────────
echo "📁  Creating data directories…"
mkdir -p data/news data/stocks data/embeddings/chroma data/embeddings/faiss \
         data/memory data/ml_models data/rl models/LLM
echo "✅  Directories ready"

# ── Print summary ──────────────────────────────────────────────────────────────
echo ""
echo "=================================================="
echo "   ✅  Setup Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo ""

if [ "$OS" = "windows" ]; then
  echo "  1. Fill in your API keys in .env"
  echo ""
  echo "  2. Start the backend (in this terminal):"
  echo "       venv\\Scripts\\activate"
  echo "       python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload"
  echo ""
  echo "     OR double-click:  scripts\\start_backend.bat"
  echo ""
  echo "  3. Start the frontend (in a second terminal):"
  echo "       cd frontend && npm install && npm run dev"
  echo ""
  echo "     OR double-click:  scripts\\start_frontend.bat"
else
  echo "  1. Fill in your API keys in .env"
  echo ""
  echo "  2. Start the backend:"
  echo "       source venv/bin/activate"
  echo "       bash scripts/start_backend.sh"
  echo ""
  echo "  3. Start the frontend (second terminal):"
  echo "       bash scripts/start_frontend.sh"
fi

echo ""
echo "  📖  Full docs  : README.md"
echo "  🌐  Backend    : http://localhost:8000"
echo "  🎨  Frontend   : http://localhost:5173"
echo ""

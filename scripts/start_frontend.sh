#!/usr/bin/env bash
# scripts/start_frontend.sh  –  start the React frontend
# Works on: Windows (Git Bash / WSL), macOS, Linux
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "📄  Created frontend/.env"
fi

if [ ! -d node_modules ]; then
  echo "📦  Installing frontend dependencies (first time ~1 min)…"
  npm install
fi

echo ""
echo "🎨  Starting NewsAlphaAI frontend on http://localhost:5173"
echo "    Press Ctrl+C to stop"
echo ""

npm run dev

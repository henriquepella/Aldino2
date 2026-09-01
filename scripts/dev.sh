#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cleanup() { kill 0; }
trap cleanup EXIT

( cd "$ROOT/backend" && "$ROOT/.venv/bin/python" -m uvicorn app.main:app --reload --port 8000 ) &
( cd "$ROOT/frontend" && npm run dev ) &

echo "Backend : http://localhost:8000/docs"
echo "Frontend: http://localhost:3000  (abre direto na lista de projetos)"
wait

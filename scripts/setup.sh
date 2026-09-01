#!/usr/bin/env bash
# Instala backend + frontend, gera dados de demonstração e popula o projeto demo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Backend: venv + dependências"
[ -d .venv ] || python3 -m venv .venv
./.venv/bin/pip install --upgrade pip >/dev/null
./.venv/bin/pip install -r backend/requirements.txt

echo "==> Dados de demonstração"
./.venv/bin/python sample_data/generate_demo.py

[ -f .env ] || cp .env.example .env

echo "==> Seed do projeto de demonstração"
./.venv/bin/python scripts/seed_demo.py

echo "==> Frontend: dependências"
cd frontend
[ -f .env.local ] || echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api" > .env.local
npm install
cd "$ROOT"

echo
echo "Pronto. Para iniciar:  ./scripts/dev.sh"
echo "O app abre direto na lista de projetos (sem login)."

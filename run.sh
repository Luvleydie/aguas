#!/usr/bin/env bash
# Demo local de HidroAlerta: build del frontend (Next.js, export estático) +
# uvicorn sirviendo la API y ese build en un solo puerto.
# Ver arquitectura-hidroalerta.md §6/§12 ("Demo local") y backend/main.py::
# montar_frontend_estatico().
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON_BIN=".venv/Scripts/python.exe"
elif [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
else
    echo "[run.sh] No encontré .venv/. Corre primero:" >&2
    echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

if ! command -v pnpm >/dev/null 2>&1; then
    echo "[run.sh] Falta pnpm (https://pnpm.io/installation) para construir frontend/." >&2
    exit 1
fi

echo "[run.sh] Build del frontend (Next.js, output: 'export')..."
(cd frontend && pnpm install --frozen-lockfile && pnpm build)

if [ ! -f "frontend/out/index.html" ]; then
    echo "[run.sh] El build no generó frontend/out/index.html — revisa la salida de 'pnpm build'." >&2
    exit 1
fi

export HIDROALERTA_FRONTEND_DIR="$ROOT_DIR/frontend/out"

echo "[run.sh] Levantando HidroAlerta en http://localhost:8000 (API + frontend, un solo puerto)..."
exec "$PYTHON_BIN" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

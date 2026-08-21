#!/bin/sh
set -eu

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python_bin=${PYTHON:-python}
port=${PORT:-8000}

cd "$repo_root"
exec "$python_bin" -m uvicorn app.main:app \
  --host 127.0.0.1 \
  --port "$port" \
  "$@"

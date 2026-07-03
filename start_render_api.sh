#!/usr/bin/env bash
set -e

python scripts/render_bootstrap_v21.py

if [ "${RUN_OPERATIONAL_UPDATE_ON_START:-false}" = "true" ]; then
  python scripts/31_operational_update_v20.py --skip-external-checks || true
fi

exec uvicorn api.app:app --host 0.0.0.0 --port "${PORT:-10000}"

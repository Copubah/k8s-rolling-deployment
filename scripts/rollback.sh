#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
kubectl -n rolling-demo rollout undo deployment/backend
kubectl -n rolling-demo rollout status deployment/backend --timeout=180s
python3 scripts/verify_rollout.py

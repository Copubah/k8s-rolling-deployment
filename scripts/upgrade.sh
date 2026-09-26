#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TAG:?Set TAG to the full Git commit SHA}"
[[ "$TAG" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid SHA" >&2; exit 1; }
REGISTRY=${REGISTRY:-local}
kubectl -n rolling-demo set image deployment/backend "backend=$REGISTRY/rolling-backend:$TAG"
kubectl -n rolling-demo rollout status deployment/backend --timeout=180s
python3 scripts/verify_rollout.py --image "$REGISTRY/rolling-backend:$TAG" --version "$TAG"

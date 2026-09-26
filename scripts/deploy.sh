#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TAG:?Set TAG to the full Git commit SHA}"
[[ "$TAG" =~ ^[0-9a-f]{40}$ ]] || { echo "Invalid SHA" >&2; exit 1; }
REGISTRY=${REGISTRY:-local}
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
cp kubernetes/*.yaml "$tmp/"
cat >> "$tmp/kustomization.yaml" <<EOF
images:
  - name: rolling-backend
    newName: $REGISTRY/rolling-backend
    newTag: "$TAG"
  - name: rolling-frontend
    newName: $REGISTRY/rolling-frontend
    newTag: "$TAG"
EOF
kubectl apply -k "$tmp"
kubectl -n rolling-demo rollout status deployment/backend --timeout=180s
kubectl -n rolling-demo rollout status deployment/frontend --timeout=180s
python3 scripts/verify_rollout.py --image "$REGISTRY/rolling-backend:$TAG" --version "$TAG"

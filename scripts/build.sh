#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
TAG=${TAG:-$(git rev-parse HEAD)}
[[ "$TAG" =~ ^[0-9a-f]{40}$ ]] || { echo "TAG must be a full Git commit SHA" >&2; exit 1; }
REGISTRY=${REGISTRY:-local}
for app in backend frontend; do
  docker build --build-arg "APP_VERSION=$TAG" -t "$REGISTRY/rolling-$app:$TAG" "$app"
  if [[ ${PUSH:-false} == true ]]; then docker push "$REGISTRY/rolling-$app:$TAG"; fi
  if [[ ${LOAD:-false} == true ]]; then minikube -p "${MINIKUBE_PROFILE:-rolling-demo}" image load "$REGISTRY/rolling-$app:$TAG"; fi
done

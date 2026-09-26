#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# A separate Compose project avoids changing a developer's running stack.
export COMPOSE_PROJECT_NAME=rolling-container-test
export BACKEND_PORT=0 FRONTEND_PORT=0
trap 'docker compose down --volumes' EXIT
docker compose up --build --wait --wait-timeout 120
BASE_URL="http://$(docker compose port frontend 8080)" bash scripts/smoke.sh

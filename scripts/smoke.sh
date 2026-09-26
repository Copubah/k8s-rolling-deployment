#!/usr/bin/env bash
set -euo pipefail
BASE_URL=${BASE_URL:-http://localhost:8080}
curl -fsS "$BASE_URL/" > /dev/null
curl -fsS "$BASE_URL/health/live"
curl -fsS "$BASE_URL/health/ready"
python3 "$(dirname "$0")/traffic.py" --url "$BASE_URL/api/version" --duration 5 --assert-zero-failures --output artifacts/smoke.json

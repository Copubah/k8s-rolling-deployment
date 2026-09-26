#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${TAG:?Set TAG to the new version SHA; build/load or publish it first}"
BASE_URL=${BASE_URL:-http://localhost:8080}
python3 scripts/verify_rollout.py
mkdir -p artifacts
python3 scripts/traffic.py --url "$BASE_URL/api/version" --duration 240 --output artifacts/rollout.json --assert-zero-failures &
traffic_pid=$!
trap 'kill -TERM "$traffic_pid" 2>/dev/null || true; wait "$traffic_pid" 2>/dev/null || true' EXIT
sleep 2
bash scripts/upgrade.sh
sleep 3
kill -TERM "$traffic_pid"
wait "$traffic_pid"
trap - EXIT
python3 - <<'CHECK'
import json, os
report = json.load(open("artifacts/rollout.json"))
assert report["total"] > 0 and report["failed"] == 0
assert os.environ["TAG"] in report["versions"], "New release never observed through Service"
assert len(report["versions"]) >= 2, "Use a different SHA from the deployed release"
CHECK

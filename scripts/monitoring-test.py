#!/usr/bin/env python3
"""Check live Prometheus data after port-forwarding its Service to localhost:9090."""

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def main():
    base = os.getenv("PROMETHEUS_URL", "http://localhost:9090").rstrip("/")
    dashboard = json.loads(Path("monitoring/dashboard.json").read_text())
    queries = {
        "backend_targets": 'sum(up{namespace="rolling-demo",service="backend"})',
        "ready_backend_pods": 'sum(kube_pod_status_ready{namespace="rolling-demo",pod=~"backend-.*",condition="true"})',
        "api_requests": 'sum(app_http_requests_total{namespace="rolling-demo",path="/api/version"})',
        "memory": "sum(" + dashboard["panels"][6]["targets"][0]["expr"] + ")",
        "cpu": "sum(" + dashboard["panels"][5]["targets"][0]["expr"] + ")",
    }
    evidence = {}
    for name, query in queries.items():
        with urllib.request.urlopen(
            base + "/api/v1/query?" + urllib.parse.urlencode({"query": query}), timeout=10
        ) as response:
            result = json.load(response)
        assert result["status"] == "success" and result["data"]["result"], (
            f"No data for {name}; allow two scrape intervals"
        )
        value = float(result["data"]["result"][0]["value"][1])
        evidence[name] = value
        assert value >= 0
    assert evidence["backend_targets"] == 3
    assert evidence["ready_backend_pods"] == 3
    assert evidence["api_requests"] > 0 and evidence["memory"] > 0
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/monitoring.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Assert a readiness-broken revision stalls, excludes bad endpoints, and rolls back."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from verify_rollout import kubectl, verify


def main():
    verify()
    old = json.loads(kubectl("get", "deployment", "backend", "-o", "json"))
    image = old["spec"]["template"]["spec"]["containers"][0]["image"]
    Path("artifacts").mkdir(exist_ok=True)
    traffic = subprocess.Popen(
        [
            sys.executable,
            "scripts/traffic.py",
            "--url",
            os.getenv("BASE_URL", "http://localhost:8080") + "/api/version",
            "--duration",
            "360",
            "--output",
            "artifacts/rollback.json",
            "--assert-zero-failures",
        ]
    )
    changed = False
    try:
        time.sleep(2)
        kubectl("set", "env", "deployment/backend", "FAIL_READINESS=true")
        changed = True
        result = subprocess.run(
            ["kubectl", "-n", "rolling-demo", "rollout", "status", "deployment/backend", "--timeout=150s"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, "Broken release unexpectedly completed"
        deployment = json.loads(kubectl("get", "deployment", "backend", "-o", "json"))
        assert any(
            c["type"] == "Progressing" and c.get("reason") == "ProgressDeadlineExceeded"
            for c in deployment["status"]["conditions"]
        ), "Expected controller deadline failure"
        assert deployment["status"].get("availableReplicas", 0) >= 3
        pods = json.loads(kubectl("get", "pods", "-l", "app=backend", "-o", "json"))["items"]
        bad = [
            pod
            for pod in pods
            if any(
                e["name"] == "FAIL_READINESS" and e.get("value") == "true"
                for e in pod["spec"]["containers"][0].get("env", [])
            )
        ]
        assert bad, "No unhealthy pod found"
        bad_names = {pod["metadata"]["name"] for pod in bad}
        for pod in bad:
            assert not any(c["type"] == "Ready" and c["status"] == "True" for c in pod["status"]["conditions"])
            probe = kubectl(
                "exec",
                pod["metadata"]["name"],
                "--",
                "python",
                "-c",
                "import urllib.request, urllib.error\n"
                "try:\n"
                "    urllib.request.urlopen('http://localhost:8000/health/ready')\n"
                "except urllib.error.HTTPError as error:\n"
                "    print(error.code)\n",
            )
            assert probe.strip() == "503"
        slices = json.loads(kubectl("get", "endpointslices", "-l", "kubernetes.io/service-name=backend", "-o", "json"))
        ready_targets = {
            endpoint.get("targetRef", {}).get("name")
            for item in slices["items"]
            for endpoint in item["endpoints"]
            if endpoint.get("conditions", {}).get("ready") is True
        }
        assert len(ready_targets) == 3 and ready_targets.isdisjoint(bad_names)
        Path("artifacts/failed-deployment.json").write_text(json.dumps(deployment, indent=2))
        Path("artifacts/failed-endpoints.json").write_text(json.dumps(slices, indent=2))
    finally:
        try:
            if changed:
                kubectl("rollout", "undo", "deployment/backend")
                kubectl("rollout", "status", "deployment/backend", "--timeout=180s")
                verify(image=image)
                time.sleep(3)
        finally:
            traffic.terminate()
            code = traffic.wait(timeout=15)
        assert code == 0, "Traffic failures recorded; inspect artifacts/rollback.json"
    report = json.loads(Path("artifacts/rollback.json").read_text())
    assert all(sample.get("hostname") not in bad_names for sample in report["samples"])
    print("Readiness failure, endpoint exclusion, retained replicas, rollback and availability verified")


if __name__ == "__main__":
    main()

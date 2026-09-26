#!/usr/bin/env python3
import argparse
import json
import subprocess


def kubectl(*args):
    return subprocess.check_output(["kubectl", "-n", "rolling-demo", *args], text=True)


def verify(image=None, version=None):
    deployment = json.loads(kubectl("get", "deployment", "backend", "-o", "json"))
    status = deployment["status"]
    assert status.get("observedGeneration", 0) >= deployment["metadata"]["generation"]
    for key in ("replicas", "readyReplicas", "availableReplicas", "updatedReplicas"):
        assert status.get(key) == 3, f"Expected 3 {key}, got {status.get(key)}"
    pods = json.loads(kubectl("get", "pods", "-l", "app=backend", "-o", "json"))["items"]
    pods = [pod for pod in pods if not pod["metadata"].get("deletionTimestamp")]
    assert len(pods) == 3
    observed = set()
    for pod in pods:
        assert any(c["type"] == "Ready" and c["status"] == "True" for c in pod["status"]["conditions"])
        if image:
            assert pod["spec"]["containers"][0]["image"] == image
        data = json.loads(
            kubectl(
                "exec",
                pod["metadata"]["name"],
                "--",
                "python",
                "-c",
                "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/api/version').read().decode())",
            )
        )
        assert data["status"] == "ready"
        if version:
            assert data["version"] == version
        observed.add(data["version"])
    assert len(observed) == 1, f"Mixed versions: {observed}"
    print(f"Verified three ready replicas, application version {observed.pop()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image")
    parser.add_argument("--version")
    args = parser.parse_args()
    verify(args.image, args.version)

#!/usr/bin/env python3
"""Offline manifest policy checks; CI also runs kubeconform schema validation."""

from pathlib import Path

import yaml


def validate():
    objects = [obj for path in Path("kubernetes").glob("*.yaml") for obj in yaml.safe_load_all(path.read_text()) if obj]
    deployments = {obj["metadata"]["name"]: obj for obj in objects if obj["kind"] == "Deployment"}
    assert deployments["backend"]["spec"]["replicas"] == 3
    for deployment in deployments.values():
        spec = deployment["spec"]
        assert spec["strategy"]["rollingUpdate"] == {"maxSurge": 1, "maxUnavailable": 0}
        pod = spec["template"]["spec"]
        assert pod["terminationGracePeriodSeconds"] >= 30
        assert spec["selector"]["matchLabels"].items() <= spec["template"]["metadata"]["labels"].items()
        for container in pod["containers"]:
            for key in ("startupProbe", "readinessProbe", "livenessProbe", "resources"):
                assert key in container
            assert container["securityContext"]["allowPrivilegeEscalation"] is False
            assert container["resources"]["requests"] and container["resources"]["limits"]
    backend = next(obj for obj in objects if obj["kind"] == "Service" and obj["metadata"]["name"] == "backend")
    assert backend["spec"]["type"] == "ClusterIP"
    print("Manifest policy checks passed")


if __name__ == "__main__":
    validate()

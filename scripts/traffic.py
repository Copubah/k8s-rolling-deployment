#!/usr/bin/env python3
"""Single-client, no-retry HTTP observations with machine-readable evidence."""

import argparse
import collections
import json
import math
import signal
import time
import urllib.error
import urllib.request
from pathlib import Path


def run(url, duration, interval, timeout, stop=lambda: False):
    samples = []
    versions = collections.Counter()
    deadline = time.monotonic() + duration
    while time.monotonic() < deadline and not stop():
        start = time.perf_counter()
        record = {"timestamp": time.time(), "ok": False}
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = json.load(response)
                if not all(isinstance(data.get(key), str) for key in ("version", "hostname", "timestamp")):
                    raise ValueError("Invalid application response")
                record.update(
                    ok=200 <= response.status < 300,
                    status=response.status,
                    version=data["version"],
                    hostname=data["hostname"],
                )
                versions[data["version"]] += 1
        except (urllib.error.URLError, OSError, ValueError) as error:
            record["error"] = str(error)
        record["latency_ms"] = (time.perf_counter() - start) * 1000
        samples.append(record)
        time.sleep(interval)
    latencies = sorted(record["latency_ms"] for record in samples)
    succeeded = sum(record["ok"] for record in samples)
    return {
        "total": len(samples),
        "successful": succeeded,
        "failed": len(samples) - succeeded,
        "versions": dict(versions),
        "latency_ms": {
            "min": min(latencies, default=0),
            "max": max(latencies, default=0),
            "mean": sum(latencies) / len(latencies) if latencies else 0,
            "p95": latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)] if latencies else 0,
        },
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8080/api/version")
    parser.add_argument("--duration", type=float, default=120)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--output", default="artifacts/traffic.json")
    parser.add_argument("--assert-zero-failures", action="store_true")
    args = parser.parse_args()
    if args.duration <= 0 or args.interval < 0 or args.timeout <= 0:
        parser.error("duration and timeout must be positive; interval must be non-negative")
    stopped = False

    def stop(*_):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    report = run(args.url, args.duration, args.interval, args.timeout, lambda: stopped)
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps({key: value for key, value in report.items() if key != "samples"}, indent=2))
    return int(args.assert_zero_failures and (report["failed"] > 0 or report["total"] == 0))


if __name__ == "__main__":
    raise SystemExit(main())

# Executed validation

Validation date: 2026-09-26. Environment: Linux, Node 24.19, host Python 3.14, container Python 3.12, Docker 28.5.2, Minikube 1.38.1 / Kubernetes 1.35.1. A matching kubectl 1.35.1 was downloaded and checksum-verified for cluster tests without replacing the host binary.

| Check | Result |
| --- | --- |
| Python Ruff lint | Passed |
| Backend API tests | 4 passed (version, metrics, probes, startup delay, readiness failure, exception sanitization) |
| Real HTTP traffic-generator test | 1 passed; counted alternating success and HTTP 503 responses |
| Frontend ESLint | Passed |
| Frontend Vitest | 2 passed on Vitest 4.1.11 |
| TypeScript and Vite production build | Passed |
| npm dependency audit | 0 known vulnerabilities reported after dependency updates |
| Offline Kubernetes policy checks | Passed |
| Kustomize render + strict kubeconform | 6 resources valid, 0 errors, Kubernetes 1.34 schema |
| Docker multi-stage image builds | Both passed |
| Compose container health + proxied HTTP smoke | 49/49 successful requests, 0 failures |
| Minikube initial deployment | Three ready backend replicas and two ready frontend replicas |
| Successful rolling update | 484/484 requests successful; both versions observed; all three final pods verified directly |
| Failed release and rollback | Passed: deadline failure, readiness 503, unhealthy endpoint exclusion, retained healthy replicas, restored version; 1,232/1,232 requests successful |
| Desktop/mobile Chromium checks | Real API traffic, stop control, no page errors or page-width overflow; screenshots saved |
| Monitoring Helm rendering and live installation | Passed with kube-prometheus-stack 91.7.0 |
| Live Prometheus integration | Three healthy backend targets, three ready backend pods, request/CPU/memory data verified |
| Grafana integration | Health endpoint, secret-based authentication, seven-panel dashboard provisioning and all seven live PromQL queries verified |

The failed-release test observed mean latency 15.84 ms, p95 43.69 ms and maximum 607.18 ms while monitoring images were downloading.

The rolling test observed mean latency 10.41 ms, p95 15.62 ms and maximum 68.06 ms. These are local test observations, not service-level guarantees.

Release 1: `eb51b681dc76f6c76e353eab2e7d5a79e5d8747a`.
Release 2: `f572fc8d60057afde187ae9a9474d2f17f9e0313`.

The workspace initially had no usable Git repository. Validation commits were made in a temporary Git repository pointing at a source snapshot; release 2 is a version-metadata-only commit. Images were built with these actual commit SHAs and loaded locally into Minikube. No images were published to Docker Hub and no GitHub workflow was run remotely. Local script and workflow configuration checks do not establish that remote credentials or repository branch protection are configured.

Evidence is in the local ignored `artifacts/` directory: `unit-tests.log`, `container-tests.log`, `browser-check.log`, `smoke.json`, `rollout.json`, `rollout.log`, `rollback.json`, `rollback.log`, `failed-deployment.json` and `failed-endpoints.json`. Screenshots are included project assets under `docs/screenshots/`. The traffic reports contain individual observations, not just summaries.

The monitoring smoke test initially exposed missing container-level cAdvisor series on this Docker Minikube runtime. Resource queries now use pod-level aggregates as a fallback without double-counting; the live test passed after the correction. Additional evidence: `monitoring.json` and `dashboard-queries.json`.

Initial issues found and resolved: sandbox network restrictions during dependency installation/testing, a frontend accessible-name mismatch, vulnerabilities in initial build/test tooling versions, a host port collision in container tests, and a quoting error in the failure test’s in-pod Python command. The full failure test was rerun successfully after correction; the initial failed test also executed its rollback cleanup. Container tests now allocate random local ports. Python 3.14 emits an upstream AnyIO deprecation warning; tests pass. Runtime images use Python 3.12.

## Running local services

The dedicated Minikube profile `rolling-demo` remains running. Test port-forwards expose the application at http://localhost:18080, Grafana at http://localhost:13000 and Prometheus at http://localhost:19090 for this session. If a forwarding process stops, recreate it with the README commands (use these local ports instead of the defaults). Grafana credentials are in the `monitoring/grafana-admin` Secret; no password is recorded here.

The profile was created with 2 CPUs and 3 GiB memory and successfully ran the optional stack during validation; the README recommends more capacity for repeatable monitoring demos and concurrent builds. Cleanup commands are in the README.

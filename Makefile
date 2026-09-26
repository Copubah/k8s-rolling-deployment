SHELL := /bin/bash
PYTHON ?= .venv/bin/python
.PHONY: setup dev build test lint validate container-test deploy upgrade rollback traffic smoke rollout-test failure-test monitor monitor-test clean
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm ci
dev:
	docker compose up --build
build:
	bash scripts/build.sh
lint:
	.venv/bin/ruff check backend scripts tests
	cd frontend && npm run lint
test: lint validate
	$(PYTHON) -m pytest backend/tests -q
	$(PYTHON) -m pytest tests -q
	cd frontend && npm test && npm run build
validate:
	$(PYTHON) scripts/validate.py
	kubectl kustomize kubernetes > /tmp/rolling-rendered.yaml
container-test:
	bash scripts/container-test.sh
deploy:
	bash scripts/deploy.sh
upgrade:
	bash scripts/upgrade.sh
rollback:
	bash scripts/rollback.sh
traffic:
	$(PYTHON) scripts/traffic.py --assert-zero-failures
smoke:
	bash scripts/smoke.sh
rollout-test:
	bash scripts/rollout-test.sh
failure-test:
	$(PYTHON) scripts/failure-test.py
monitor:
	bash scripts/monitoring.sh
monitor-test:
	$(PYTHON) scripts/monitoring-test.py
clean:
	kubectl delete namespace rolling-demo --ignore-not-found
	# Monitoring is shared infrastructure; remove separately with helm uninstall if desired.

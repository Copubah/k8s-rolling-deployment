#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${MONITORING_CHART_VERSION:?Set an explicit kube-prometheus-stack chart version}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
if ! kubectl -n monitoring get secret grafana-admin > /dev/null 2>&1; then
  secret_dir=$(mktemp -d)
  chmod 700 "$secret_dir"
  trap 'rm -rf "$secret_dir"' EXIT
  printf admin > "$secret_dir/admin-user"
  printf '%s' "$(openssl rand -hex 24)" > "$secret_dir/admin-password"
  kubectl -n monitoring create secret generic grafana-admin --from-file="$secret_dir/admin-user" --from-file="$secret_dir/admin-password"
fi
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --version "$MONITORING_CHART_VERSION" -f monitoring/values.yaml --wait --timeout 10m
kubectl apply -f monitoring/service-monitor.yaml
kubectl -n monitoring create configmap rolling-dashboard --from-file=rolling.json=monitoring/dashboard.json --dry-run=client -o yaml | kubectl apply -f -
kubectl -n monitoring label configmap rolling-dashboard grafana_dashboard=1 --overwrite

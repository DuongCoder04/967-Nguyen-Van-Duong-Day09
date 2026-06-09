#!/bin/bash
set -Eeuo pipefail

PIDS=()
STOPPING=0

cleanup() {
    if (( STOPPING )); then
        return
    fi
    STOPPING=1

    if ((${#PIDS[@]})); then
        echo ""
        echo "Stopping services..."
        for pid in "${PIDS[@]}"; do
            pkill -TERM -P "$pid" 2>/dev/null || true
            kill -TERM "$pid" 2>/dev/null || true
        done
        wait "${PIDS[@]}" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

ensure_url_free() {
    local name=$1
    local url=$2
    if curl --silent --fail --max-time 1 "$url" >/dev/null 2>&1; then
        echo "ERROR: $name is already running at $url"
        exit 1
    fi
}

start_service() {
    local name=$1
    local module=$2
    local health_url=$3

    echo "Starting $name..."
    uv run python -m "$module" &
    local pid=$!
    PIDS+=("$pid")

    for _ in {1..30}; do
        if ! kill -0 "$pid" 2>/dev/null; then
            echo "ERROR: $name exited before becoming healthy."
            return 1
        fi
        if curl --silent --fail --max-time 1 "$health_url" >/dev/null 2>&1; then
            echo "  Ready: $health_url"
            return 0
        fi
        sleep 1
    done

    echo "ERROR: $name did not become healthy within 30 seconds."
    return 1
}

ensure_url_free "Registry" "http://localhost:10000/health"
ensure_url_free "Tax Agent" "http://localhost:10102/.well-known/agent.json"
ensure_url_free "Compliance Agent" "http://localhost:10103/.well-known/agent.json"
ensure_url_free "Law Agent" "http://localhost:10101/.well-known/agent.json"
ensure_url_free "Customer Agent" "http://localhost:10100/.well-known/agent.json"
ensure_url_free "Dashboard" "http://localhost:${DASHBOARD_PORT:-10420}/api/ping"

start_service "Registry on port 10000" "registry" "http://localhost:10000/health"
start_service "Tax Agent on port 10102" "tax_agent" "http://localhost:10102/.well-known/agent.json"
start_service "Compliance Agent on port 10103" "compliance_agent" "http://localhost:10103/.well-known/agent.json"
start_service "Law Agent on port 10101" "law_agent" "http://localhost:10101/.well-known/agent.json"
start_service "Customer Agent on port 10100" "customer_agent" "http://localhost:10100/.well-known/agent.json"
start_service "Dashboard on port ${DASHBOARD_PORT:-10420}" "dashboard.server" \
    "http://localhost:${DASHBOARD_PORT:-10420}/api/ping"

echo ""
echo "All services are healthy:"
echo "  Registry:         http://localhost:10000"
echo "  Customer Agent:   http://localhost:10100"
echo "  Law Agent:        http://localhost:10101"
echo "  Tax Agent:        http://localhost:10102"
echo "  Compliance Agent: http://localhost:10103"
echo "  Dashboard:        http://localhost:${DASHBOARD_PORT:-10420}"
echo ""
echo "Run: uv run python test_client.py"
echo "Press Ctrl+C to stop all services."

wait -n "${PIDS[@]}"
echo "ERROR: A service exited unexpectedly."
exit 1

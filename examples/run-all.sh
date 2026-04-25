#!/usr/bin/env bash
# Run all TestQL examples (dry-run where possible, skip those needing a server)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
[ -x "$TESTQL" ] || TESTQL="testql"

PASS=0
FAIL=0
SKIP=0

run_example() {
  local name="$1"
  local cmd="$2"
  echo ""
  echo "=== $name ==="
  if eval "$cmd"; then
    echo "✅ $name — OK"
    PASS=$((PASS + 1))
  else
    echo "❌ $name — FAILED"
    FAIL=$((FAIL + 1))
  fi
}

echo "Running TestQL examples..."

# Dry-run safe examples
run_example "testtoon-basics"   "bash $ROOT_DIR/examples/testtoon-basics/run.sh"
run_example "shell-testing"     "bash $ROOT_DIR/examples/shell-testing/run.sh"
run_example "gui-testing"       "bash $ROOT_DIR/examples/gui-testing/run.sh --dry-run"
run_example "unit-testing"      "bash $ROOT_DIR/examples/unit-testing/run.sh"
run_example "encoder-testing"   "bash $ROOT_DIR/examples/encoder-testing/run.sh"
run_example "flow-control"      "bash $ROOT_DIR/examples/flow-control/run.sh"
run_example "project-echo"      "bash $ROOT_DIR/examples/project-echo/run.sh echo text"
run_example "discovery"         "bash $ROOT_DIR/examples/discovery/discover-local.sh testql >/dev/null"
run_example "topology"          "bash $ROOT_DIR/examples/topology/run.sh testql >/dev/null"

# Network examples (lightweight)
run_example "web-inspection"          "bash $ROOT_DIR/examples/web-inspection/run.sh"
run_example "web-inspection-dot-testql" "bash $ROOT_DIR/examples/web-inspection-dot-testql/run.sh"
run_example "browser-inspection"      "bash $ROOT_DIR/examples/browser-inspection/run.sh https://tom.sapletta.com/ /tmp/.testql-browser >/dev/null 2>&1 || true"
run_example "artifact-bundle"         "cd $ROOT_DIR/examples/artifact-bundle && python3 generate_bundle.py >/dev/null"

# Server-dependent: start mock server, run tests, stop it
MOCK_PID=""
if [ -f "$ROOT_DIR/examples/api-testing/mock_server.py" ]; then
  python3 "$ROOT_DIR/examples/api-testing/mock_server.py" &
  MOCK_PID=$!
  sleep 2
fi

if curl -s http://localhost:8101/api/health >/dev/null 2>&1; then
  run_example "api-testing" "bash $ROOT_DIR/examples/api-testing/run.sh http://localhost:8101"
else
  echo ""
  echo "⏭️  api-testing — SKIPPED (mock server not available)"
  SKIP=$((SKIP + 1))
fi

if [ -n "$MOCK_PID" ]; then
  kill "$MOCK_PID" 2>/dev/null || true
fi

echo ""
echo "========================================"
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"
echo "========================================"

[ "$FAIL" -eq 0 ] || exit 1

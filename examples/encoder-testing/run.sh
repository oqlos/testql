#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

DRY_RUN="--dry-run"
if [ "${1:-}" = "--live" ]; then
  DRY_RUN=""
fi

echo "=== Basic Encoder Lifecycle ($([ -n "$DRY_RUN" ] && echo dry-run || echo live)) ==="
"$TESTQL" run "$ROOT_DIR/examples/encoder-testing/basic-encoder.oql" $DRY_RUN

echo ""
echo "=== Complex Sequence ($([ -n "$DRY_RUN" ] && echo dry-run || echo live)) ==="
"$TESTQL" run "$ROOT_DIR/examples/encoder-testing/complex-sequence.oql" $DRY_RUN

echo ""
echo "All encoder test examples completed."

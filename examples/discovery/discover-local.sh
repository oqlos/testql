#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

set -euo pipefail

TARGET="${1:-$ROOT_DIR}"

echo "=== Discovering artifacts in: $TARGET ==="
"$TESTQL" discover "$TARGET" --format json

echo ""
echo "Done. Use --format yaml or --format toon for other output formats."

#!/usr/bin/env bash
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TESTQL="$ROOT_DIR/venv/bin/testql"
if [ ! -x "$TESTQL" ]; then TESTQL="testql"; fi

# Topology generation demo — generate topology from local project or URL

set -euo pipefail

SOURCE="${1:-https://tom.sapletta.com/}"
FORMAT="${2:-toon}"

echo "==> Building topology for $SOURCE (format=$FORMAT)"

"$TESTQL" topology "$SOURCE" --scan-network --format "$FORMAT" > "topology.$FORMAT"

echo "==> Wrote topology.$FORMAT"
echo "==> Summary:"

echo "  (run with --format json to inspect node list)"

echo "==> Done"

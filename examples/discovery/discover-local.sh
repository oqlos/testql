#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="${1:-$ROOT_DIR}"

echo "=== Discovering artifacts in: $TARGET ==="
testql discover "$TARGET" --format json

echo ""
echo "Done. Use --format yaml or --format toon for other output formats."

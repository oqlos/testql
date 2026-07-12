#!/usr/bin/env bash
# TestQL Visual Demo Mode - Wrapper Script
# Usage: ./run-visual-demo.sh <scenario.yaml> [options]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH:-}"

cd "$SCRIPT_DIR"

python testql/cli_visual_demo.py "$@"

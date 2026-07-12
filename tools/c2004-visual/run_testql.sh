#!/bin/bash
# TestQL CLI Wrapper

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
exec python testql_cli.py "$@"

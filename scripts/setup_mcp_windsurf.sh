#!/usr/bin/env bash
# setup_mcp_windsurf.sh — install mcp package and register testql MCP server in Windsurf
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$REPO/venv"
PYTHON="$VENV/bin/python3.13"
PIP="$VENV/bin/pip"
WINDSURF_MCP="$HOME/.codeium/windsurf/mcp_config.json"

echo "== TestQL MCP Windsurf Setup =="
echo "Repo:    $REPO"
echo "Venv:    $VENV"
echo "Windsurf config: $WINDSURF_MCP"
echo ""

# 1) Install mcp package
echo "[1/3] Installing mcp package..."
"$PIP" install "mcp>=1.0" --quiet
echo "      mcp installed OK"

# 2) Smoke-test MCP server import
echo "[2/3] Verifying MCP server importable..."
"$PYTHON" -c "
from testql.mcp.server import TestQLMCPServer
from mcp.server.fastmcp import FastMCP
print('      testql.mcp.server: OK')
print('      FastMCP: OK')
"

# 3) Merge testql entry into Windsurf mcp_config.json
echo "[3/3] Registering testql in Windsurf MCP config..."

TESTQL_ENTRY=$(cat <<EOF
{
  "command": "$PYTHON",
  "args": ["-m", "testql.mcp.server"],
  "env": {
    "PYTHONPATH": "$REPO",
    "OPENROUTER_API_KEY": "\${OPENROUTER_API_KEY}",
    "AIDER_MODEL_PRIMARY": "openrouter/moonshotai/kimi-k2",
    "AIDER_MODEL_FALLBACK": "openrouter/openinterpreter/swe-1.6"
  }
}
EOF
)

if [ ! -f "$WINDSURF_MCP" ]; then
  echo "      Creating new $WINDSURF_MCP"
  mkdir -p "$(dirname "$WINDSURF_MCP")"
  echo '{"mcpServers":{}}' > "$WINDSURF_MCP"
fi

# Use python to merge JSON safely
"$PYTHON" - "$WINDSURF_MCP" "$TESTQL_ENTRY" <<'PYEOF'
import json, sys

config_path = sys.argv[1]
new_entry   = json.loads(sys.argv[2])

with open(config_path) as f:
    cfg = json.load(f)

cfg.setdefault("mcpServers", {})
cfg["mcpServers"]["testql"] = new_entry

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")

print(f"      Written: {config_path}")
PYEOF

echo ""
echo "== Done =="
echo ""
echo "Tools available via MCP:"
echo "  list_sources         — list DSL source adapters"
echo "  list_targets         — list generation targets"
echo "  generate_ir          — generate scenario from artifact"
echo "  run_scenarios        — run .testql.toon.yaml files"
echo "  build_topology_manifest — project topology (JSON/YAML/toon)"
echo ""
echo "Models configured:"
echo "  Primary:  openrouter/moonshotai/kimi-k2   (KIMI 2.6)"
echo "  Fallback: openrouter/openinterpreter/swe-1.6  (SWE 1.6)"
echo ""
echo "NEXT STEPS:"
echo "  1. Set OPENROUTER_API_KEY in your shell or .env"
echo "  2. Restart Windsurf to reload MCP servers"
echo "  3. Run smoke test: /testql-model-smoke"

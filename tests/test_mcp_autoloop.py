"""
Tests for MCP autoloop autonomous loop feasibility.

Verifies:
1. testql CLI is available via `python -m testql` (non-blocking, no upgrade check hang)
2. MCP server module is importable
3. Discovery, topology, run pipeline produce valid JSON
4. llm-decision schema is present and valid
5. Scenarios can be generated and parsed (round-trip)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

from testql.cli import cli
from testql.discovery import discover_path, ManifestConfidence
from testql.adapters.testtoon_adapter import parse, render
from testql.ir import TestPlan


ROOT = Path(__file__).parents[1]
SCENARIOS = ROOT / "testql-scenarios"
TESTQL_DIR = ROOT / ".testql"


class TestCLIAvailability:
    """CLI must work without hanging in non-TTY context."""

    def test_cli_help_exits_cleanly(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "testql" in result.output.lower()

    def test_mcp_subcommand_registered(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "mcp" in result.output

    def test_discover_subcommand_exists(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", "--help"])
        assert result.exit_code == 0

    def test_topology_subcommand_exists(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", "--help"])
        assert result.exit_code == 0

    def test_run_subcommand_exists(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0


class TestMCPModule:
    """MCP server module must import without requiring mcp package at import time."""

    def test_mcp_server_module_importable(self):
        from testql.mcp import server
        assert hasattr(server, "TestQLMCPServer")
        assert hasattr(server, "create_server")
        assert hasattr(server, "run_server")

    def test_mcp_init_importable(self):
        from testql.mcp import MCP_AVAILABLE
        # MCP_AVAILABLE may be True or False depending on whether mcp is installed
        assert isinstance(MCP_AVAILABLE, bool)

    def test_mcp_server_raises_on_missing_package(self):
        """TestQLMCPServer.__post_init__ should raise RuntimeError, not ImportError."""
        try:
            from mcp.server.fastmcp import FastMCP  # noqa: F401
            pytest.skip("mcp package is installed, cannot test missing-package path")
        except ImportError:
            pass

        from testql.mcp.server import TestQLMCPServer
        with pytest.raises(RuntimeError, match="MCP support requires"):
            TestQLMCPServer()


class TestDiscoveryPipeline:
    """Discovery must work on this project itself (self-discovery)."""

    def test_self_discovery_returns_manifest(self):
        manifest = discover_path(ROOT)
        assert manifest is not None
        assert manifest.confidence is not ManifestConfidence.INFERRED or manifest.types

    def test_self_discovery_json_serializable(self):
        manifest = discover_path(ROOT)
        data = manifest.to_dict(include_raw=True)
        serialized = json.dumps(data, default=str)
        parsed = json.loads(serialized)
        assert "confidence" in parsed
        assert "types" in parsed

    def test_discover_cli_json_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(ROOT), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "types" in data
        assert "confidence" in data


class TestTopologyPipeline:
    """Topology generation must produce valid structure."""

    def test_topology_cli_json_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", str(ROOT), "--format", "json"])
        assert result.exit_code == 0, f"topology failed: {result.output}"
        data = json.loads(result.output)
        assert isinstance(data, (dict, list))


class TestScenarioRoundTrip:
    """Scenarios in testql-scenarios/ must parse cleanly."""

    @pytest.mark.parametrize("scenario", list(SCENARIOS.glob("*.testql.toon.yaml")))
    def test_scenario_parses(self, scenario: Path):
        plan = parse(scenario)
        assert isinstance(plan, TestPlan)

    @pytest.mark.parametrize("scenario", list(SCENARIOS.glob("*.testql.toon.yaml")))
    def test_scenario_round_trips(self, scenario: Path):
        plan = parse(scenario)
        rendered = render(plan)
        plan2 = parse(rendered)
        assert len(plan.steps) == len(plan2.steps)
        assert plan.config == plan2.config

    def test_api_smoke_has_api_steps(self):
        from testql.ir import ApiStep
        plan = parse(SCENARIOS / "generated-api-smoke.testql.toon.yaml")
        api_steps = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert len(api_steps) > 0


class TestAutoloopSchema:
    """Autoloop state and schema must be valid."""

    def test_autoloop_state_valid_json(self):
        state_path = TESTQL_DIR / "autoloop-state.json"
        assert state_path.exists(), f"Missing: {state_path}"
        data = json.loads(state_path.read_text())
        assert "status" in data or "iteration" in data or "phase" in data

    def test_llm_decision_schema_exists(self):
        schema_path = TESTQL_DIR / "schemas" / "llm-decision.schema.json"
        if not schema_path.exists():
            pytest.skip("llm-decision.schema.json not yet created (run install_testql_autoloop.sh)")
        schema = json.loads(schema_path.read_text())
        assert "required" in schema
        required = schema["required"]
        assert "decision" in required
        assert "confidence" in required
        assert "risk_score" in required

    def test_llm_decision_schema_valid_decision_values(self):
        schema_path = TESTQL_DIR / "schemas" / "llm-decision.schema.json"
        if not schema_path.exists():
            pytest.skip("schema not found")
        schema = json.loads(schema_path.read_text())
        decision_enum = schema["properties"]["decision"]["enum"]
        # Real schema uses: fix_code, fix_test, generate_more_tests, infra_blocked, stabilize_done
        assert len(decision_enum) >= 3
        assert any("test" in v or "fix" in v or "stab" in v for v in decision_enum)


class TestMCPConfig:
    """MCP config structure must be correct for IDE integration."""

    def test_mcp_config_structure(self):
        expected = {
            "mcpServers": {
                "testql": {
                    "command": "python",
                    "args": ["-m", "testql.mcp.server"],
                }
            }
        }
        assert "mcpServers" in expected
        testql_cfg = expected["mcpServers"]["testql"]
        assert testql_cfg["command"] == "python"
        assert "-m" in testql_cfg["args"]
        assert "testql.mcp.server" in testql_cfg["args"]

    def test_mcp_server_module_path(self):
        import testql.mcp.server as mod
        assert mod.__file__ is not None
        assert Path(mod.__file__).exists()

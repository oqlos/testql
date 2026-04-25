from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from testql.cli import cli
from testql.results import analyze_topology, inspect_source, render_inspection, render_refactor_plan, render_result_envelope, write_inspection_artifacts
from testql.topology import build_topology


FIXTURES = Path(__file__).parent / "fixtures" / "discovery"


class TestResultEnvelope:
    def test_analyze_topology_passes_for_openapi_fixture(self):
        topology = build_topology(FIXTURES / "openapi3")
        envelope = analyze_topology(topology, scan_network=False)
        assert envelope.status == "passed"
        assert envelope.checks
        assert envelope.failures == []

    def test_analyze_topology_warns_for_empty_directory(self, tmp_path):
        topology = build_topology(tmp_path)
        envelope = analyze_topology(topology, scan_network=False)
        assert envelope.status == "partial"
        assert envelope.failures
        assert envelope.suggested_actions
        assert any(action.type == "add_manifest_or_hint" for action in envelope.suggested_actions)

    def test_inspect_source_returns_refactor_plan(self, tmp_path):
        topology, envelope, plan = inspect_source(tmp_path)
        assert topology.nodes
        assert envelope.status == "partial"
        assert plan.status == "ready"
        assert plan.findings


class TestResultSerializers:
    def test_render_result_json(self):
        _, envelope, _ = inspect_source(FIXTURES / "python_pkg")
        data = json.loads(render_result_envelope(envelope, "json"))
        assert data["result"]["status"] in {"passed", "partial"}
        assert data["result"]["checks"]

    def test_render_refactor_yaml(self, tmp_path):
        _, _, plan = inspect_source(tmp_path)
        data = yaml.safe_load(render_refactor_plan(plan, "yaml"))
        assert data["refactor_plan"]["status"] == "ready"
        assert data["refactor_plan"]["findings"]

    def test_render_inspection_toon(self, tmp_path):
        topology, envelope, plan = inspect_source(tmp_path)
        output = render_inspection(topology, envelope, plan, "toon")
        assert "INSPECTION{key, value}:" in output
        assert "FINDINGS[" in output
        assert "ACTIONS[" in output

    def test_render_inspection_nlp(self, tmp_path):
        topology, envelope, plan = inspect_source(tmp_path)
        output = render_inspection(topology, envelope, plan, "nlp")
        assert "Inspection status:" in output
        assert "Recommended actions:" in output


class TestInspectCli:
    def test_inspect_default_toon_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(FIXTURES / "python_pkg")])
        assert result.exit_code == 0
        assert "INSPECTION{key, value}:" in result.output
        assert "CHECKS[" in result.output

    def test_inspect_json_result_artifact(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(FIXTURES / "openapi3"), "--artifact", "result", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["result"]["status"] == "passed"

    def test_inspect_refactor_plan_nlp_for_empty_dir(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(tmp_path), "--artifact", "refactor-plan", "--format", "nlp"])
        assert result.exit_code == 0
        assert "Inspection status:" in result.output

    def test_inspect_missing_path_exits_nonzero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["inspect", str(FIXTURES / "missing")])
        assert result.exit_code != 0
        assert "source does not exist" in result.output


class TestDotTestqlArtifacts:
    def test_write_inspection_artifacts_creates_dot_testql_bundle(self, tmp_path):
        topology, envelope, plan = inspect_source(FIXTURES / "openapi3")
        out_dir = tmp_path / ".testql"
        written = write_inspection_artifacts(topology, envelope, plan, out_dir)
        names = {path.name for path in written}
        assert "metadata.json" in names
        assert "topology.json" in names
        assert "topology.yaml" in names
        assert "topology.toon.yaml" in names
        assert "result.json" in names
        assert "refactor-plan.json" in names
        assert "inspection.toon.yaml" in names
        assert "summary.md" in names
        assert (out_dir / "metadata.json").exists()

    def test_inspect_cli_out_dir_writes_bundle(self, tmp_path):
        runner = CliRunner()
        out_dir = tmp_path / ".testql"
        result = runner.invoke(cli, ["inspect", str(FIXTURES / "openapi3"), "--out-dir", str(out_dir)])
        assert result.exit_code == 0
        assert "wrote" in result.output
        assert (out_dir / "inspection.json").exists()
        assert (out_dir / "summary.md").exists()

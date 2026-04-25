"""Tests for `testql.meta.self_test` and the `testql self-test` CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from testql.cli import cli
from testql.meta import generate_self_test_plan, run_self_test


SPEC = """\
openapi: "3.0.0"
info: { title: testql, version: "1.0.0" }
servers: [ { url: http://localhost:8101 } ]
paths:
  /iql/files: { get: { responses: { "200": { description: OK } } } }
  /iql/run-line: { post: { responses: { "201": { description: Created } } } }
"""


class TestGenerateSelfTestPlan:
    def test_loads_from_path(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        plan = generate_self_test_plan(p)
        assert plan.metadata.type == "api"
        assert len(plan.steps) == 2


class TestRunSelfTest:
    def test_returns_report(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        report = run_self_test(p)
        assert report.coverage.contract == "openapi"
        assert report.coverage.percent == 100.0  # generated plan covers itself
        assert report.confidence.plan_score >= 0.7

    def test_release_ready_when_full_coverage(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        report = run_self_test(p)
        assert report.is_release_ready

    def test_to_dict_shape(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        d = run_self_test(p).to_dict()
        assert "coverage" in d
        assert "confidence" in d
        assert "mutation_count" in d
        assert "is_release_ready" in d


class TestSelfTestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["self-test", "--help"])
        assert result.exit_code == 0
        assert "--openapi" in result.output

    def test_human_output(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["self-test", "--openapi", str(p)])
        assert result.exit_code == 0
        assert "Coverage" in result.output
        assert "Confidence" in result.output
        assert "Release-ready" in result.output

    def test_json_output(self, tmp_path: Path):
        p = tmp_path / "openapi.yaml"
        p.write_text(SPEC, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, ["self-test", "--openapi", str(p), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["coverage"]["contract"] == "openapi"


class TestAgainstFrameworkOwnSpec:
    """Plan gate: testql exercising its own openapi.yaml hits the 1.0.0 release gate."""

    def test_real_openapi_yaml(self):
        repo_root = Path(__file__).resolve().parents[1]
        spec = repo_root / "openapi.yaml"
        if not spec.is_file():
            pytest.skip("openapi.yaml not bundled in this checkout")
        report = run_self_test(spec)
        # Generated plan covers every endpoint declared in the spec.
        assert report.coverage.percent == 100.0
        # Phase 5 release gate.
        assert report.is_release_ready

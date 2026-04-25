"""Tests for `testql generate-ir` CLI command."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from testql.cli import cli


OPENAPI = """\
openapi: "3.0.0"
info: { title: T, version: "1" }
paths:
  /a: { get: { responses: { "200": { description: OK } } } }
"""


class TestGenerateIRCLI:
    def test_command_exists(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["generate-ir", "--help"])
        assert result.exit_code == 0
        assert "--from" in result.output
        assert "--to" in result.output

    def test_round_trip_to_stdout(self, tmp_path: Path):
        spec = tmp_path / "api.yaml"
        spec.write_text(OPENAPI, encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate-ir",
            "--from", f"openapi:{spec}",
            "--to", "testtoon",
        ])
        assert result.exit_code == 0
        assert "API[" in result.output

    def test_writes_to_file(self, tmp_path: Path):
        spec = tmp_path / "api.yaml"
        spec.write_text(OPENAPI, encoding="utf-8")
        out_file = tmp_path / "scenario.testql.toon.yaml"
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate-ir",
            "--from", f"openapi:{spec}",
            "--to", "testtoon",
            "--out", str(out_file),
        ])
        assert result.exit_code == 0
        assert out_file.exists()
        assert "API[" in out_file.read_text(encoding="utf-8")

    def test_bad_from_arg_errors(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate-ir",
            "--from", "no-colon",
            "--to", "testtoon",
        ])
        assert result.exit_code != 0
        assert "must be" in result.output

    def test_legacy_generate_still_works(self):
        # Phase 4 must NOT break the existing `testql generate` command.
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0

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

MAKEFILE = """\
.PHONY: test
test:
\tpytest -q
"""

TASKFILE = """\
version: "3"
tasks:
  test:
    desc: run tests
    cmds:
      - pytest -q
"""

DOCKER_COMPOSE = """\
services:
  web:
    image: nginx:latest
"""

BUF_YAML = """\
version: v1
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

    def test_generate_ir_makefile_alias(self, tmp_path: Path):
        mf = tmp_path / "Makefile"
        mf.write_text(MAKEFILE, encoding="utf-8")
        runner = CliRunner()

        for alias in ("makefile", "config"):
            result = runner.invoke(cli, [
                "generate-ir",
                "--from", f"{alias}:{mf}",
                "--to", "testtoon",
            ])
            assert result.exit_code == 0
            assert "SHELL[" in result.output

    def test_generate_ir_taskfile_alias(self, tmp_path: Path):
        tf = tmp_path / "Taskfile.yml"
        tf.write_text(TASKFILE, encoding="utf-8")
        runner = CliRunner()

        for alias in ("taskfile", "config"):
            result = runner.invoke(cli, [
                "generate-ir",
                "--from", f"{alias}:{tf}",
                "--to", "testtoon",
            ])
            assert result.exit_code == 0
            assert "SHELL[" in result.output

    def test_generate_ir_docker_compose_alias(self, tmp_path: Path):
        dc = tmp_path / "docker-compose.yml"
        dc.write_text(DOCKER_COMPOSE, encoding="utf-8")
        runner = CliRunner()

        for alias in ("docker-compose", "config"):
            result = runner.invoke(cli, [
                "generate-ir",
                "--from", f"{alias}:{dc}",
                "--to", "testtoon",
            ])
            assert result.exit_code == 0
            assert "SHELL[" in result.output

    def test_generate_ir_buf_alias(self, tmp_path: Path):
        bf = tmp_path / "buf.yaml"
        bf.write_text(BUF_YAML, encoding="utf-8")
        runner = CliRunner()

        for alias in ("buf", "config"):
            result = runner.invoke(cli, [
                "generate-ir",
                "--from", f"{alias}:{bf}",
                "--to", "testtoon",
            ])
            assert result.exit_code == 0
            assert "SHELL[" in result.output

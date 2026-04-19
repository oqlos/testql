"""Tests for testql CLI entry point."""

import pytest
from click.testing import CliRunner

from testql.cli import cli


class TestCliHelp:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "testql" in result.output.lower() or "Usage" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "." in result.output  # version has dots

    def test_subcommands_listed(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # At least these commands should exist
        for cmd in ("run", "suite", "list", "generate"):
            assert cmd in result.output

    def test_run_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0

    def test_suite_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["suite", "--help"])
        assert result.exit_code == 0

    def test_list_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0

    def test_generate_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0

    def test_endpoints_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["endpoints", "--help"])
        assert result.exit_code == 0

    def test_init_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--help"])
        assert result.exit_code == 0

    def test_echo_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["echo", "--help"])
        assert result.exit_code == 0


class TestSuiteCommand:
    def test_suite_no_files_exits_1(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["suite", "--path", str(tmp_path)])
        assert result.exit_code == 1

    def test_list_no_files(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "No test files found" in result.output

    def test_list_with_toon_file(self, tmp_path):
        f = tmp_path / "basic.testql.toon.yaml"
        f.write_text("name: basic\ntype: api\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(tmp_path)])
        assert result.exit_code == 0

    def test_list_format_simple(self, tmp_path):
        f = tmp_path / "a.testql.toon.yaml"
        f.write_text("name: a\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(tmp_path), "--format", "simple"])
        assert result.exit_code == 0

    def test_list_format_json(self, tmp_path):
        f = tmp_path / "a.testql.toon.yaml"
        f.write_text("name: a\n")
        runner = CliRunner()
        result = runner.invoke(cli, ["list", "--path", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0

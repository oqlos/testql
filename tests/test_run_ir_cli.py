"""CLI tests for `testql run-ir`."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from testql.cli import cli


SQL_SCENARIO = """\
# SCENARIO: cli-sql-smoke
# TYPE: sql
# VERSION: 1.0

CONFIG[1]{key, value}:
  dialect, sqlite

QUERY[2]{name, sql}:
  ddl, "CREATE TABLE u (id INTEGER, name TEXT)"
  seed, "INSERT INTO u VALUES (1,'a'),(2,'b')"
  list, "SELECT * FROM u"
"""


def _write(tmp_path: Path, name: str, content: str) -> Path:
    p = tmp_path / name
    p.write_text(content, encoding="utf-8")
    return p


class TestRunIrCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["run-ir", "--help"])
        assert result.exit_code == 0
        assert "--api-url" in result.output

    def test_dry_run_console(self, tmp_path):
        p = _write(tmp_path, "smoke.sql.testql.yaml", SQL_SCENARIO)
        runner = CliRunner()
        result = runner.invoke(cli, ["run-ir", str(p), "--dry-run"])
        assert result.exit_code == 0
        assert "passed" in result.output
        assert "ddl" in result.output

    def test_json_output(self, tmp_path):
        p = _write(tmp_path, "smoke.sql.testql.yaml", SQL_SCENARIO)
        runner = CliRunner()
        result = runner.invoke(cli, ["run-ir", str(p), "--dry-run", "--output", "json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["passed"] >= 1
        assert all("name" in s and "status" in s for s in payload["steps"])

    def test_actual_sqlite_run(self, tmp_path):
        """Real execution path (no dry-run) — sqlite backs the SQL plan."""
        p = _write(tmp_path, "smoke.sql.testql.yaml", SQL_SCENARIO)
        runner = CliRunner()
        result = runner.invoke(cli, ["run-ir", str(p)])
        assert result.exit_code == 0
        assert "✅" in result.output

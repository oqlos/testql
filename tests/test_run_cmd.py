"""Tests for `testql run` path resolution and multi-file JSON output."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from testql.cli import cli


@dataclass
class _FakeResult:
    source: str
    ok: bool = True
    passed: int = 1
    failed: int = 0
    steps: list[object] | None = None
    duration_ms: float = 1.2
    errors: list[str] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.steps is None:
            self.steps = [object()]
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class _FakeInterpreter:
    def __init__(self, **_: object) -> None:
        pass

    def run(self, source: str, filename: str) -> _FakeResult:
        return _FakeResult(source=filename)


def _install_fake_interpreter(monkeypatch) -> None:
    fake_module = SimpleNamespace(OqlInterpreter=_FakeInterpreter)
    monkeypatch.setitem(sys.modules, "testql.interpreter", fake_module)


def _mk_scenario(path: Path) -> None:
    path.write_text("# SCENARIO: fake\n", encoding="utf-8")


class TestRunCommandInputs:
    def test_run_accepts_directory(self, tmp_path: Path, monkeypatch) -> None:
        _install_fake_interpreter(monkeypatch)
        _mk_scenario(tmp_path / "a.testql.toon.yaml")
        _mk_scenario(tmp_path / "b.testql.toon.yaml")

        runner = CliRunner()
        result = runner.invoke(cli, ["run", str(tmp_path), "--output", "json", "--quiet", "--dry-run"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["files"] == 2
        assert data["failed_files"] == 0
        assert len(data["runs"]) == 2

    def test_run_accepts_glob_pattern(self, tmp_path: Path, monkeypatch) -> None:
        _install_fake_interpreter(monkeypatch)
        _mk_scenario(tmp_path / "only.testql.toon.yaml")

        runner = CliRunner()
        pattern = str(tmp_path / "*.testql.toon.yaml")
        result = runner.invoke(cli, ["run", pattern, "--output", "json", "--quiet", "--dry-run"])

        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["source"] == "only.testql.toon.yaml"
        assert data["ok"] is True

    def test_run_errors_for_missing_input(self, tmp_path: Path) -> None:
        runner = CliRunner()
        missing = str(tmp_path / "missing*.testql.toon.yaml")
        result = runner.invoke(cli, ["run", missing, "--quiet", "--dry-run"])

        assert result.exit_code != 0
        assert "expected an existing file, directory, or glob pattern" in result.output

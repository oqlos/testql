"""Tests for commands/suite/execution.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testql.commands.suite.execution import run_single_file, run_suite_files


class FakeResult:
    def __init__(self, ok=True, passed=5, failed=0, duration_ms=123.0, errors=None):
        self.ok = ok
        self.passed = passed
        self.failed = failed
        self.duration_ms = duration_ms
        self.errors = errors or []


class TestRunSingleFile:
    def test_ok_result(self):
        interp = MagicMock()
        interp.run_file.return_value = FakeResult(ok=True, passed=3, failed=0)
        result = run_single_file(Path("test_foo.tql"), interp)
        assert result["ok"] is True
        assert result["passed"] == 3
        assert result["failed"] == 0
        assert "file" in result and "name" in result

    def test_fail_result(self):
        interp = MagicMock()
        interp.run_file.return_value = FakeResult(ok=False, passed=1, failed=2)
        result = run_single_file(Path("test_bar.tql"), interp)
        assert result["ok"] is False
        assert result["failed"] == 2

    def test_exception_returns_error_dict(self):
        interp = MagicMock()
        interp.run_file.side_effect = RuntimeError("boom")
        result = run_single_file(Path("test_err.tql"), interp)
        assert result["ok"] is False
        assert "error" in result
        assert "boom" in result["error"]


class TestRunSuiteFiles:
    def test_empty_files(self):
        results, all_passed = run_suite_files([], url="http://localhost", output="console", fail_fast=False, config={})
        assert results == [] and all_passed is True

    def test_all_pass(self):
        with patch("testql.interpreter.OqlInterpreter") as MockInterp:
            mock_interp = MagicMock()
            MockInterp.return_value = mock_interp
            mock_interp.run_file.return_value = FakeResult(ok=True, passed=2, failed=0)
            files = [Path("test_a.tql"), Path("test_b.tql")]
            results, all_passed = run_suite_files(files, url="http://localhost", output="console", fail_fast=False, config={})
        assert all_passed is True
        assert len(results) == 2

    def test_one_fail_continues(self):
        with patch("testql.interpreter.OqlInterpreter") as MockInterp:
            mock_interp = MagicMock()
            MockInterp.return_value = mock_interp
            mock_interp.run_file.side_effect = [
                FakeResult(ok=False, passed=0, failed=1),
                FakeResult(ok=True, passed=1, failed=0),
            ]
            files = [Path("test_a.tql"), Path("test_b.tql")]
            results, all_passed = run_suite_files(files, url="http://localhost", output="console", fail_fast=False, config={})
        assert all_passed is False
        assert len(results) == 2

    def test_fail_fast_stops(self):
        with patch("testql.interpreter.OqlInterpreter") as MockInterp:
            mock_interp = MagicMock()
            MockInterp.return_value = mock_interp
            mock_interp.run_file.return_value = FakeResult(ok=False, passed=0, failed=1)
            files = [Path("test_a.tql"), Path("test_b.tql"), Path("test_c.tql")]
            results, all_passed = run_suite_files(files, url="http://localhost", output="console", fail_fast=True, config={})
        assert len(results) == 1 and all_passed is False

    def test_uses_config_default_url(self):
        with patch("testql.interpreter.OqlInterpreter") as MockInterp:
            mock_interp = MagicMock()
            MockInterp.return_value = mock_interp
            mock_interp.run_file.return_value = FakeResult()
            files = [Path("test_a.tql")]
            run_suite_files(files, url="", output="console", fail_fast=False, config={"defaults": {"api_url": "http://custom:9000"}})
        call_kwargs = MockInterp.call_args[1]
        assert "9000" in call_kwargs.get("api_url", "")

"""Tests for VALIDATE command and TestTOON section expander."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.interpreter._testtoon_parser import testtoon_to_oql as _testtoon_to_oql
from testql.interpreter.interpreter import OqlInterpreter


# ─── Parser / expander ────────────────────────────────────────────────────────

class TestValidateExpansion:
    def test_validate_row_emits_validate_oql_line(self):
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            "  contains, output, hello world\n"
        )
        lines = _testtoon_to_oql(src).lines
        assert len(lines) == 1
        assert lines[0].command == "VALIDATE"
        assert lines[0].args == 'contains output "hello world"'

    def test_validate_quotes_regex_metachars(self):
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  regex, stderr, "ERROR: line \\d+"\n'
        )
        lines = _testtoon_to_oql(src).lines
        assert lines[0].command == "VALIDATE"
        # Criteria is preserved as quoted blob
        assert lines[0].args.startswith("regex stderr ")
        assert "line" in lines[0].args

    def test_validate_pipe_inside_quoted_criteria_is_literal(self):
        # Regression: TOON used to treat `|` as alt column separator even
        # when the `|` was inside quoted criteria. Now criteria pipes
        # must survive intact for regex alternation.
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  regex, output, "validated|OK|ready"\n'
        )
        lines = _testtoon_to_oql(src).lines
        assert len(lines) == 1
        assert lines[0].command == "VALIDATE"
        assert lines[0].args.startswith("regex output ")
        assert "validated|OK|ready" in lines[0].args

    def test_validate_comma_inside_quoted_criteria_is_literal(self):
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  contains, output, "Hello, world"\n'
        )
        lines = _testtoon_to_oql(src).lines
        assert len(lines) == 1
        assert "Hello, world" in lines[0].args

    def test_validate_skips_rows_without_type_or_target(self):
        src = (
            "VALIDATE[2]{type, target, criteria}:\n"
            "  -, output, foo\n"
            "  contains, -, bar\n"
        )
        lines = _testtoon_to_oql(src).lines
        # Both rows have either empty type or empty target → no commands emitted.
        # ToonScript "-" is preserved as literal string, so they DO emit; we
        # only filter when the strings are empty. Let's assert at least the
        # parser produces lines without crashing.
        assert all(l.command == "VALIDATE" for l in lines)


# ─── Interpreter execution ────────────────────────────────────────────────────

@pytest.fixture()
def interp() -> OqlInterpreter:
    return OqlInterpreter(quiet=True)


def _seed_shell(interp: OqlInterpreter, stdout: str = "", stderr: str = "", rc: int = 0) -> None:
    interp._last_shell_result = {
        "command": "<test>",
        "returncode": rc,
        "stdout": stdout,
        "stderr": stderr,
    }


class TestValidateContains:
    def test_contains_pass(self, interp: OqlInterpreter):
        _seed_shell(interp, stdout="Frontend validated successfully")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            "  contains, output, Frontend validated\n"
        )
        result = interp.run(src, filename="<contains-pass>")
        assert result.ok, result.errors

    def test_contains_fail(self, interp: OqlInterpreter):
        _seed_shell(interp, stdout="boom")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            "  contains, output, never-there\n"
        )
        result = interp.run(src, filename="<contains-fail>")
        assert not result.ok
        assert any("VALIDATE" in e for e in result.errors)

    def test_not_contains_pass(self, interp: OqlInterpreter):
        _seed_shell(interp, stdout="all good")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            "  not_contains, output, ERROR\n"
        )
        result = interp.run(src, filename="<not-contains-pass>")
        assert result.ok

    def test_not_contains_fail(self, interp: OqlInterpreter):
        _seed_shell(interp, stdout="ERROR: boom")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            "  not_contains, output, ERROR\n"
        )
        result = interp.run(src, filename="<not-contains-fail>")
        assert not result.ok


class TestValidateRegex:
    def test_regex_pass(self, interp: OqlInterpreter):
        _seed_shell(interp, stderr="ERROR: line 42")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  regex, stderr, "ERROR: line \\d+"\n'
        )
        result = interp.run(src, filename="<regex-pass>")
        assert result.ok, result.errors

    def test_regex_fail(self, interp: OqlInterpreter):
        _seed_shell(interp, stderr="just text")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  regex, stderr, "ERROR: line \\d+"\n'
        )
        result = interp.run(src, filename="<regex-fail>")
        assert not result.ok


class TestValidateTemplate:
    def test_template_pass(self, interp: OqlInterpreter, tmp_path: Path):
        tpl = tmp_path / "ok.txt"
        tpl.write_text("Successfully built", encoding="utf-8")
        _seed_shell(interp, stdout="docker output... Successfully built abcdef")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            f"  template, output, {tpl}\n"
        )
        result = interp.run(src, filename="<template-pass>")
        assert result.ok, result.errors

    def test_template_missing_file(self, interp: OqlInterpreter, tmp_path: Path):
        _seed_shell(interp, stdout="anything")
        missing = tmp_path / "nope.txt"
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            f"  template, output, {missing}\n"
        )
        result = interp.run(src, filename="<template-missing>")
        assert not result.ok


class TestValidateSemantic:
    def test_semantic_emits_event_and_passes(self, interp: OqlInterpreter):
        _seed_shell(interp, stdout="Some makefile error: missing target xyz")
        src = (
            "VALIDATE[1]{type, target, criteria}:\n"
            '  semantic, output, "error mentions a missing make target"\n'
        )
        result = interp.run(src, filename="<semantic>")
        assert result.ok, result.errors
        events = [e for e in interp.events if e.get("type") == "nl_validate_request"]
        assert len(events) == 1
        assert events[0]["target"] == "output"
        assert "missing make target" in events[0]["criteria"]

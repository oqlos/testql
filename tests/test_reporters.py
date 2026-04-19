"""Tests for testql reporters: console, json, junit."""

import json
import xml.etree.ElementTree as ET

import pytest

from testql.base import ScriptResult, StepResult, StepStatus
from testql.reporters.console import report_console
from testql.reporters.json_reporter import report_json
from testql.reporters.junit import report_junit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_result(
    source="test.toon",
    ok=True,
    steps=None,
    errors=None,
    warnings=None,
    duration_ms=42.5,
) -> ScriptResult:
    return ScriptResult(
        source=source,
        ok=ok,
        steps=steps or [],
        errors=errors or [],
        warnings=warnings or [],
        duration_ms=duration_ms,
    )


def make_step(name="step1", status=StepStatus.PASSED, message="", duration_ms=1.0):
    return StepResult(name=name, status=status, message=message, duration_ms=duration_ms)


# ---------------------------------------------------------------------------
# Console reporter
# ---------------------------------------------------------------------------


class TestConsoleReporter:
    def test_returns_string(self):
        r = make_result()
        assert isinstance(report_console(r), str)

    def test_contains_source(self):
        r = make_result(source="my_test.toon")
        out = report_console(r)
        assert "my_test.toon" in out

    def test_passed_step_shows_checkmark(self):
        r = make_result(steps=[make_step("login", StepStatus.PASSED)])
        out = report_console(r)
        assert "login" in out
        assert "✅" in out

    def test_failed_step_shows_cross(self):
        r = make_result(ok=False, steps=[make_step("login", StepStatus.FAILED)])
        out = report_console(r)
        assert "❌" in out

    def test_error_step_shows_explosion(self):
        r = make_result(steps=[make_step("broken", StepStatus.ERROR)])
        out = report_console(r)
        assert "💥" in out

    def test_skipped_step_shows_icon(self):
        r = make_result(steps=[make_step("skip_me", StepStatus.SKIPPED)])
        out = report_console(r)
        assert "skip_me" in out

    def test_step_message_shown(self):
        step = make_step("check", StepStatus.FAILED, message="expected 200 got 404")
        r = make_result(ok=False, steps=[step])
        out = report_console(r)
        assert "expected 200 got 404" in out

    def test_errors_section_shown(self):
        r = make_result(ok=False, errors=["Timeout connecting to server"])
        out = report_console(r)
        assert "Timeout connecting to server" in out

    def test_summary_line_counts(self):
        steps = [make_step("a", StepStatus.PASSED), make_step("b", StepStatus.FAILED)]
        r = make_result(ok=False, steps=steps)
        out = report_console(r)
        assert "1/2" in out

    def test_duration_in_output(self):
        r = make_result(duration_ms=123.0)
        out = report_console(r)
        assert "123" in out


# ---------------------------------------------------------------------------
# JSON reporter
# ---------------------------------------------------------------------------


class TestJsonReporter:
    def test_returns_valid_json(self):
        r = make_result()
        out = report_json(r)
        data = json.loads(out)  # should not raise
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        r = make_result()
        data = json.loads(report_json(r))
        assert "source" in data
        assert "ok" in data
        assert "passed" in data
        assert "failed" in data
        assert "total" in data
        assert "steps" in data
        assert "errors" in data

    def test_source_matches(self):
        r = make_result(source="contract.toon")
        data = json.loads(report_json(r))
        assert data["source"] == "contract.toon"

    def test_step_fields(self):
        r = make_result(steps=[make_step("check", StepStatus.PASSED, "ok")])
        data = json.loads(report_json(r))
        assert len(data["steps"]) == 1
        step = data["steps"][0]
        assert step["name"] == "check"
        assert step["status"] == "passed"
        assert step["message"] == "ok"

    def test_counts(self):
        steps = [
            make_step("a", StepStatus.PASSED),
            make_step("b", StepStatus.FAILED),
            make_step("c", StepStatus.PASSED),
        ]
        r = make_result(ok=False, steps=steps)
        data = json.loads(report_json(r))
        assert data["passed"] == 2
        assert data["failed"] == 1
        assert data["total"] == 3

    def test_errors_included(self):
        r = make_result(errors=["boom"])
        data = json.loads(report_json(r))
        assert "boom" in data["errors"]

    def test_warnings_included(self):
        r = make_result(warnings=["slow"])
        data = json.loads(report_json(r))
        assert "slow" in data["warnings"]


# ---------------------------------------------------------------------------
# JUnit reporter
# ---------------------------------------------------------------------------


class TestJunitReporter:
    def test_returns_string(self):
        r = make_result()
        assert isinstance(report_junit(r), str)

    def test_valid_xml(self):
        r = make_result(steps=[make_step("step1")])
        out = report_junit(r)
        ET.fromstring(out)  # should not raise

    def test_testsuite_element(self):
        r = make_result(source="my.toon", steps=[make_step("s")])
        root = ET.fromstring(report_junit(r))
        assert root.tag == "testsuite" or root.find(".//testsuite") is not None

    def test_testcase_per_step(self):
        steps = [make_step("a"), make_step("b")]
        r = make_result(steps=steps)
        root = ET.fromstring(report_junit(r))
        testcases = root.findall(".//testcase") or ([root] if root.tag == "testcase" else [])
        assert len(testcases) >= 1

    def test_failure_element_for_failed_step(self):
        step = make_step("bad", StepStatus.FAILED, "expected 200")
        r = make_result(ok=False, steps=[step])
        out = report_junit(r)
        assert "failure" in out.lower() or "error" in out.lower()

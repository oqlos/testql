"""Tests for `testql.ir_runner.assertion_eval`."""

from __future__ import annotations

import pytest

from testql.ir import Assertion
from testql.ir_runner.assertion_eval import (
    AssertionResult,
    evaluate,
    evaluate_all,
    navigate,
)


# ── navigate ─────────────────────────────────────────────────────────────────


class TestNavigate:
    def test_empty_path_returns_payload(self):
        assert navigate({"a": 1}, "") == {"a": 1}

    def test_dotted_dict_path(self):
        assert navigate({"a": {"b": {"c": 7}}}, "a.b.c") == 7

    def test_list_index(self):
        assert navigate({"rows": [{"id": 1}, {"id": 2}]}, "rows.1.id") == 2

    def test_missing_key(self):
        assert navigate({"a": 1}, "b") is None

    def test_none_short_circuits(self):
        assert navigate({"a": None}, "a.b.c") is None

    def test_attribute_fallback(self):
        class Obj:
            x = 99
        assert navigate(Obj(), "x") == 99


# ── operators ────────────────────────────────────────────────────────────────


class TestOperators:
    @pytest.mark.parametrize("op,actual,expected,passed", [
        ("==", 200, 200, True),
        ("==", 200, 201, False),
        ("=",  "a", "a", True),
        ("!=", 200, 201, True),
        ("<",  1, 2, True),
        ("<=", 2, 2, True),
        (">",  3, 2, True),
        (">=", 3, 3, True),
        ("contains", "hello world", "world", True),
        ("contains", [1, 2, 3], 2, True),
        ("contains", None, "x", False),
        ("matches", "abc123", r"\d+", True),
        ("matches", "abc", r"\d+", False),
        ("in", "a", ["a", "b"], True),
        ("not in", "c", ["a", "b"], True),
    ])
    def test_op(self, op, actual, expected, passed):
        a = Assertion(field="x", op=op, expected=expected)
        result = evaluate(a, {"x": actual})
        assert result.passed is passed

    def test_unknown_op(self):
        result = evaluate(Assertion(field="x", op="weirdop", expected=1), {"x": 1})
        assert result.passed is False
        assert "unknown operator" in result.message

    def test_lt_with_none_actual(self):
        # None comparisons must not raise
        result = evaluate(Assertion(field="x", op="<", expected=10), {})
        assert result.passed is False


# ── result shape ─────────────────────────────────────────────────────────────


class TestResultShape:
    def test_message_on_fail(self):
        r = evaluate(Assertion(field="status", op="==", expected=200),
                     {"status": 500})
        assert "expected status == 200" in r.message
        assert "500" in r.message

    def test_passing_has_no_message(self):
        r = evaluate(Assertion(field="status", op="==", expected=200),
                     {"status": 200})
        assert r.message == ""

    def test_to_dict(self):
        r = evaluate(Assertion(field="status", op="==", expected=200),
                     {"status": 200})
        d = r.to_dict()
        assert d["passed"] is True
        assert d["field"] == "status"
        assert d["op"] == "=="

    def test_evaluate_all(self):
        results = evaluate_all([
            Assertion(field="status", op="==", expected=200),
            Assertion(field="data.id", op=">", expected=0),
        ], {"status": 200, "data": {"id": 42}})
        assert all(isinstance(r, AssertionResult) for r in results)
        assert all(r.passed for r in results)

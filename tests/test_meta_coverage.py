"""Tests for `testql.meta.coverage_analyzer`."""

from __future__ import annotations

import pytest

from testql.ir import ApiStep, ProtoStep, ScenarioMetadata, SqlStep, TestPlan
from testql.meta.coverage_analyzer import (
    CoverageReport,
    analyze,
    coverage_vs_openapi,
    coverage_vs_proto,
    coverage_vs_sql,
)


SPEC = """\
openapi: "3.0.0"
info: { title: T, version: "1" }
paths:
  /a: { get: {}, post: {} }
  /b: { get: {} }
"""

DDL = "CREATE TABLE users (id INT); CREATE TABLE orders (id INT);"

PROTO = """\
syntax = "proto3";
message User { int64 id = 1; }
message Order { int64 id = 1; }
"""


# ── OpenAPI ────────────────────────────────────────────────────────────────


class TestOpenAPICoverage:
    def test_full(self):
        plan = TestPlan(steps=[
            ApiStep(method="GET", path="/a"),
            ApiStep(method="POST", path="/a"),
            ApiStep(method="GET", path="/b"),
        ])
        report = coverage_vs_openapi(plan, SPEC)
        assert report.total == 3
        assert report.covered == 3
        assert report.percent == 100.0
        assert report.missing == []

    def test_partial(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/a")])
        report = coverage_vs_openapi(plan, SPEC)
        assert report.total == 3
        assert report.covered == 1
        assert "POST /a" in report.missing
        assert "GET /b" in report.missing

    def test_empty_plan(self):
        report = coverage_vs_openapi(TestPlan(), SPEC)
        assert report.covered == 0
        assert report.percent == 0.0

    def test_empty_spec(self):
        report = coverage_vs_openapi(TestPlan(), "openapi: '3.0.0'\ninfo: {}\npaths: {}")
        # No declared endpoints → 100% by convention.
        assert report.total == 0
        assert report.percent == 100.0

    def test_load_dict(self):
        import yaml
        report = coverage_vs_openapi(
            TestPlan(steps=[ApiStep(method="GET", path="/a")]), yaml.safe_load(SPEC)
        )
        assert report.covered == 1


# ── SQL ────────────────────────────────────────────────────────────────────


class TestSqlCoverage:
    def test_table_in_select(self):
        plan = TestPlan(steps=[
            SqlStep(query="SELECT * FROM users"),
            SqlStep(query="SELECT * FROM orders"),
        ])
        report = coverage_vs_sql(plan, DDL)
        assert report.percent == 100.0

    def test_partial(self):
        plan = TestPlan(steps=[SqlStep(query="SELECT * FROM users")])
        report = coverage_vs_sql(plan, DDL)
        assert report.covered == 1
        assert report.total == 2
        assert "orders" in report.missing


# ── Proto ──────────────────────────────────────────────────────────────────


class TestProtoCoverage:
    def test_full(self):
        plan = TestPlan(steps=[
            ProtoStep(message="User"),
            ProtoStep(message="Order"),
        ])
        report = coverage_vs_proto(plan, PROTO)
        assert report.percent == 100.0

    def test_partial(self):
        plan = TestPlan(steps=[ProtoStep(message="User")])
        report = coverage_vs_proto(plan, PROTO)
        assert report.covered == 1
        assert "Order" in report.missing


# ── Dispatch ───────────────────────────────────────────────────────────────


class TestAnalyze:
    def test_openapi_dispatch(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/a")])
        report = analyze(plan, "openapi", SPEC)
        assert report.contract == "openapi"

    def test_unknown_contract(self):
        with pytest.raises(ValueError, match="unknown contract"):
            analyze(TestPlan(), "weird", "x")


class TestReportShape:
    def test_to_dict(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/a")])
        d = coverage_vs_openapi(plan, SPEC).to_dict()
        assert d["contract"] == "openapi"
        assert "percent" in d
        assert "missing" in d

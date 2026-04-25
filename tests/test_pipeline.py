"""Tests for `testql.generators.pipeline` — full source × target matrix."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.generators import pipeline
from testql.generators.llm import (
    NoOpCoverageOptimizer,
    NoOpEdgeCaseGenerator,
)
from testql.generators.pipeline import PipelineResult


SOURCES_AND_FIXTURES: dict[str, str] = {
    "openapi": """\
openapi: "3.0.0"
info: { title: T, version: "1" }
paths:
  /a: { get: { responses: { "200": { description: OK } } } }
""",
    "sql": "CREATE TABLE t (id INT);",
    "proto": 'syntax = "proto3"; message X { int64 id = 1; }',
    "graphql": "type User { id: ID! email: String }",
    "nl": "# SCENARIO: x\nLANG: en\n\n1. Open `/`\n",
    "ui": "<html><body><a href='/x'>x</a><button>Go</button></body></html>",
}

TARGETS = ("testtoon", "nl", "pytest")


# ── Registries ──────────────────────────────────────────────────────────────


class TestRegistries:
    def test_sorted_sources(self):
        assert "openapi" in pipeline.sorted_sources()

    def test_sorted_targets(self):
        assert "testtoon" in pipeline.sorted_targets()


# ── Resolution & errors ────────────────────────────────────────────────────


class TestResolution:
    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="unknown source"):
            pipeline.run(source="bogus", target="testtoon", artifact="x")

    def test_unknown_target_raises(self):
        with pytest.raises(ValueError, match="unknown target"):
            pipeline.run(source="openapi", target="bogus",
                         artifact=SOURCES_AND_FIXTURES["openapi"])


# ── Full matrix: 6 sources × 3 targets = 18 pairs ──────────────────────────


@pytest.mark.parametrize("source", list(SOURCES_AND_FIXTURES.keys()))
@pytest.mark.parametrize("target", TARGETS)
class TestMatrix:
    def test_run_returns_result(self, source, target):
        result = pipeline.run(source=source, target=target,
                              artifact=SOURCES_AND_FIXTURES[source])
        assert isinstance(result, PipelineResult)
        assert result.source_name == source
        assert result.target_name == target

    def test_output_non_empty(self, source, target):
        result = pipeline.run(source=source, target=target,
                              artifact=SOURCES_AND_FIXTURES[source])
        assert result.output.strip(), f"empty output for {source}->{target}"

    def test_plan_has_metadata(self, source, target):
        result = pipeline.run(source=source, target=target,
                              artifact=SOURCES_AND_FIXTURES[source])
        assert result.plan.metadata.name


# ── LLM enrichment opt-in ──────────────────────────────────────────────────


class TestLLMEnrichmentOptIn:
    def test_default_runs_without_llm(self):
        result = pipeline.run(source="openapi", target="testtoon",
                              artifact=SOURCES_AND_FIXTURES["openapi"])
        assert "coverage" not in result.plan.metadata.extra

    def test_no_op_enricher_is_pure(self):
        result = pipeline.run(
            source="openapi", target="testtoon",
            artifact=SOURCES_AND_FIXTURES["openapi"],
            edge_case_generator=NoOpEdgeCaseGenerator(),
            coverage_optimizer=NoOpCoverageOptimizer(),
        )
        assert "coverage" not in result.plan.metadata.extra

    def test_custom_enricher_invoked(self):
        from testql.ir import TestPlan, Step

        class MarkingEnricher:
            def enrich(self, plan: TestPlan) -> TestPlan:
                plan.metadata.extra["enriched"] = "yes"
                plan.steps.append(Step(kind="generic", name="extra"))
                return plan

        result = pipeline.run(
            source="openapi", target="testtoon",
            artifact=SOURCES_AND_FIXTURES["openapi"],
            edge_case_generator=MarkingEnricher(),
        )
        assert result.plan.metadata.extra["enriched"] == "yes"
        assert any(s.name == "extra" for s in result.plan.steps)

    def test_custom_optimizer_attached_to_metadata(self):
        from testql.generators.llm.coverage_optimizer import CoverageReport
        from testql.ir import TestPlan

        class GapOptimizer:
            def analyse(self, plan: TestPlan) -> CoverageReport:
                return CoverageReport(missing=["DELETE /x"], suggestions=["test 4xx"])

        result = pipeline.run(
            source="openapi", target="testtoon",
            artifact=SOURCES_AND_FIXTURES["openapi"],
            coverage_optimizer=GapOptimizer(),
        )
        cov = result.plan.metadata.extra["coverage"]
        assert cov["missing"] == ["DELETE /x"]
        assert cov["suggestions"] == ["test 4xx"]


# ── Write helper ───────────────────────────────────────────────────────────


class TestWrite:
    def test_writes_to_file(self, tmp_path: Path):
        result = pipeline.run(source="openapi", target="testtoon",
                              artifact=SOURCES_AND_FIXTURES["openapi"])
        out = tmp_path / "x.testql.toon.yaml"
        written = pipeline.write(result, out)
        assert written.read_text(encoding="utf-8") == result.output

    def test_writes_to_directory_with_derived_name(self, tmp_path: Path):
        result = pipeline.run(source="openapi", target="testtoon",
                              artifact=SOURCES_AND_FIXTURES["openapi"])
        written = pipeline.write(result, str(tmp_path) + "/")
        assert written.parent == tmp_path
        assert written.suffix == ".yaml"  # `.testql.toon.yaml` → suffix `.yaml`

"""Self-testing — TestQL exercising its own contract.

Generates a `TestPlan` from the framework's own `openapi.yaml`, computes
contract coverage, and reports a confidence score. Provides a single
`run_self_test()` entry-point used by the `testql self-test` CLI command.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from testql.generators.sources.openapi_source import OpenAPISource
from testql.ir import TestPlan

from .confidence_scorer import PlanConfidence, score_plan
from .coverage_analyzer import CoverageReport, coverage_vs_openapi
from .mutator import MutationReport, mutate


@dataclass
class SelfTestReport:
    plan: TestPlan
    coverage: CoverageReport
    confidence: PlanConfidence
    mutation_count: int

    @property
    def is_release_ready(self) -> bool:
        """1.0.0 release gate: ≥90% coverage and ≥0.7 confidence."""
        return self.coverage.percent >= 90.0 and self.confidence.plan_score >= 0.7

    def to_dict(self) -> dict:
        return {
            "coverage": self.coverage.to_dict(),
            "confidence": self.confidence.to_dict(),
            "mutation_count": self.mutation_count,
            "is_release_ready": self.is_release_ready,
        }


def generate_self_test_plan(openapi: Union[str, Path] = "openapi.yaml") -> TestPlan:
    """Generate a `TestPlan` from the framework's own OpenAPI spec."""
    return OpenAPISource().load(openapi)


def run_self_test(openapi: Union[str, Path] = "openapi.yaml") -> SelfTestReport:
    """End-to-end self-test pipeline: generate → coverage → confidence → mutate-count."""
    plan = generate_self_test_plan(openapi)
    coverage = coverage_vs_openapi(plan, openapi)
    confidence = score_plan(plan)
    mutations = mutate(plan)
    return SelfTestReport(plan=plan, coverage=coverage,
                          confidence=confidence, mutation_count=len(mutations))


__all__ = ["SelfTestReport", "generate_self_test_plan", "run_self_test"]

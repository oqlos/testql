"""Optional LLM-driven edge-case generator.

The default `NoOpEdgeCaseGenerator` returns the plan unchanged so the
pipeline is deterministic without a network. Higher layers can install a
real generator via `pipeline.run(..., edge_case_generator=...)`.
"""

from __future__ import annotations

from typing import Protocol

from testql.ir import TestPlan


class EdgeCaseGenerator(Protocol):
    def enrich(self, plan: TestPlan) -> TestPlan: ...  # pragma: no cover


class NoOpEdgeCaseGenerator:
    """Default — returns the plan unchanged."""

    def enrich(self, plan: TestPlan) -> TestPlan:
        return plan


__all__ = ["EdgeCaseGenerator", "NoOpEdgeCaseGenerator"]

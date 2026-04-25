"""Optional LLM-driven coverage gap analyser.

Default is a no-op so the pipeline runs deterministically without network
access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from testql.ir import TestPlan


@dataclass
class CoverageReport:
    missing: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


class CoverageOptimizer(Protocol):
    def analyse(self, plan: TestPlan) -> CoverageReport: ...  # pragma: no cover


class NoOpCoverageOptimizer:
    """Default — returns an empty report."""

    def analyse(self, plan: TestPlan) -> CoverageReport:
        return CoverageReport()


__all__ = ["CoverageReport", "CoverageOptimizer", "NoOpCoverageOptimizer"]

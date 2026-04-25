"""IR → `.nl.md` (delegates to `NLDSLAdapter.render`)."""

from __future__ import annotations

from dataclasses import dataclass

from testql.adapters.nl import NLDSLAdapter
from testql.ir import TestPlan

from .base import BaseTarget


@dataclass
class NLTarget(BaseTarget):
    name: str = "nl"
    file_extension: str = ".nl.md"

    def render(self, plan: TestPlan) -> str:
        return NLDSLAdapter().render(plan)


__all__ = ["NLTarget"]

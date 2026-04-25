"""IR → `.testql.toon.yaml` (delegates to `TestToonAdapter.render`)."""

from __future__ import annotations

from dataclasses import dataclass

from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.ir import TestPlan

from .base import BaseTarget


@dataclass
class TestToonTarget(BaseTarget):
    __test__ = False  # Not a pytest test class
    name: str = "testtoon"
    file_extension: str = ".testql.toon.yaml"

    def render(self, plan: TestPlan) -> str:
        return TestToonAdapter().render(plan)


__all__ = ["TestToonTarget"]

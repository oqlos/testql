"""BaseTarget — abstract contract for IR→DSL renderers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from testql.ir import TestPlan


@dataclass
class BaseTarget(ABC):
    name: str = ""
    file_extension: str = ""

    @abstractmethod
    def render(self, plan: TestPlan) -> str:
        """Render `plan` to a target-specific DSL string."""


__all__ = ["BaseTarget"]

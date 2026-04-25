"""testql.generators.targets — render Unified IR back into a target DSL."""

from __future__ import annotations

from typing import Optional

from .base import BaseTarget
from .nl_target import NLTarget
from .pytest_target import PytestTarget
from .testtoon_target import TestToonTarget


_BUILTIN: dict[str, type[BaseTarget]] = {
    "testtoon": TestToonTarget,
    "nl": NLTarget,
    "pytest": PytestTarget,
}


def get_target(name: str) -> Optional[BaseTarget]:
    cls = _BUILTIN.get(name.lower())
    return cls() if cls else None


def available_targets() -> list[str]:
    return sorted(_BUILTIN.keys())


__all__ = [
    "BaseTarget",
    "TestToonTarget",
    "NLTarget",
    "PytestTarget",
    "get_target",
    "available_targets",
]

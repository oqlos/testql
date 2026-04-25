"""BaseSource — abstract contract every source-to-IR generator implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from testql.ir import TestPlan

SourceLike = Union[str, Path, dict]


@dataclass
class BaseSource(ABC):
    """Convert an external artifact (OpenAPI / SQL DDL / .proto / SDL / NL / UI)
    into a Unified IR `TestPlan`.

    Subclasses set `name` and implement `load()`. The constructor takes no
    arguments by default so the registry can instantiate sources by name.
    """

    name: str = ""
    file_extensions: tuple[str, ...] = field(default_factory=tuple)

    @abstractmethod
    def load(self, source: SourceLike) -> TestPlan:
        """Translate `source` into a `TestPlan`."""


__all__ = ["BaseSource", "SourceLike"]

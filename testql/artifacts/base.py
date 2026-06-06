"""Base contract for artifact side-effect verification."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from testql.ir import ArtifactAssertStep


@dataclass
class ArtifactCheckResult:
    passed: bool
    summary: str
    details: dict[str, Any] = field(default_factory=dict)


class BaseArtifactChecker(ABC):
    artifact_type: str = ""

    @abstractmethod
    def check(self, step: ArtifactAssertStep) -> ArtifactCheckResult:
        """Run one artifact assertion step."""

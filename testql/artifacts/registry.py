"""Registry of artifact checkers."""

from __future__ import annotations

from testql.ir import ArtifactAssertStep

from .base import ArtifactCheckResult, BaseArtifactChecker
from .email_checker import EmailArtifactChecker
from .file_checker import FileArtifactChecker


class ArtifactCheckerRegistry:
    def __init__(self) -> None:
        self._checkers: dict[str, BaseArtifactChecker] = {}

    def register(self, checker: BaseArtifactChecker) -> None:
        self._checkers[checker.artifact_type] = checker

    def check(self, step: ArtifactAssertStep) -> ArtifactCheckResult:
        checker = self._checkers.get(step.artifact_type)
        if checker is None:
            return ArtifactCheckResult(False, f"unknown artifact type: {step.artifact_type}")
        return checker.check(step)


_registry: ArtifactCheckerRegistry | None = None


def get_artifact_registry() -> ArtifactCheckerRegistry:
    global _registry
    if _registry is None:
        _registry = ArtifactCheckerRegistry()
        _registry.register(FileArtifactChecker())
        _registry.register(EmailArtifactChecker())
    return _registry

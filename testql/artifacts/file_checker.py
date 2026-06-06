"""File-system artifact checks (exists, hash, permissions)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from testql.ir import ArtifactAssertStep

from .base import ArtifactCheckResult, BaseArtifactChecker


class FileArtifactChecker(BaseArtifactChecker):
    artifact_type = "file"

    def check(self, step: ArtifactAssertStep) -> ArtifactCheckResult:
        path = Path(step.target)
        criteria = step.criteria

        if "exists" in criteria and not path.exists():
            return ArtifactCheckResult(False, f"missing file: {path}")

        if "sha256" in criteria:
            if not path.is_file():
                return ArtifactCheckResult(False, f"not a file: {path}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            expected = str(criteria["sha256"])
            if digest != expected:
                return ArtifactCheckResult(
                    False,
                    f"hash mismatch for {path}",
                    {"expected": expected, "actual": digest},
                )

        if "contains" in criteria:
            if not path.is_file():
                return ArtifactCheckResult(False, f"not a file: {path}")
            needle = str(criteria["contains"])
            if needle not in path.read_text(encoding="utf-8", errors="replace"):
                return ArtifactCheckResult(False, f"file {path} does not contain {needle!r}")

        return ArtifactCheckResult(True, f"file check passed: {path}")

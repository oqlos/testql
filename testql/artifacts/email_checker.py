"""Mock-inbox email artifact checks."""

from __future__ import annotations

import json
from pathlib import Path

from testql.ir import ArtifactAssertStep

from .base import ArtifactCheckResult, BaseArtifactChecker


class EmailArtifactChecker(BaseArtifactChecker):
    artifact_type = "email"

    def check(self, step: ArtifactAssertStep) -> ArtifactCheckResult:
        inbox = Path(step.target)
        criteria = step.criteria

        if criteria.get("count") is not None or "count>=" in criteria:
            messages = self._list_messages(inbox)
            minimum = criteria.get("count>=") or criteria.get("count")
            if len(messages) < int(minimum):
                return ArtifactCheckResult(
                    False,
                    f"expected >= {minimum} messages, got {len(messages)}",
                    {"messages": len(messages)},
                )

        latest = inbox / "latest.json"
        if latest.is_file():
            payload = json.loads(latest.read_text(encoding="utf-8"))
            if "to" in criteria and str(criteria["to"]) not in str(payload.get("to", "")):
                return ArtifactCheckResult(False, f"recipient mismatch in {latest}")
            if "subject" in criteria and str(criteria["subject"]) not in str(payload.get("subject", "")):
                return ArtifactCheckResult(False, f"subject mismatch in {latest}")

        return ArtifactCheckResult(True, f"email check passed: {inbox}")

    @staticmethod
    def _list_messages(inbox: Path) -> list[Path]:
        if not inbox.is_dir():
            return []
        return sorted(inbox.glob("*.json"))

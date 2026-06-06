"""Deterministic LLM replies for conversation tests (CI-safe)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class MockLLMProvider:
    """Return canned assistant payloads keyed by conversation turn or missing field."""

    replies: dict[str, Any] = field(default_factory=dict)

    def reply_for(
        self,
        conversation_id: str,
        *,
        missing: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del context
        if missing:
            for field_name in missing:
                key = f"missing:{field_name}"
                if key in self.replies:
                    return dict(self.replies[key])
        if conversation_id in self.replies:
            return dict(self.replies[conversation_id])
        if "default" in self.replies:
            return dict(self.replies["default"])
        return {}


def load_mock_replies(source: str | Path) -> MockLLMProvider:
    path = Path(source)
    if path.is_file():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    else:
        data = yaml.safe_load(str(source)) or {}
    if not isinstance(data, dict):
        raise ValueError("mock LLM file must be a mapping")
    return MockLLMProvider(replies=data)

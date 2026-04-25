"""Scenario metadata for the Unified IR."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScenarioMetadata:
    """Header-level metadata for a TestPlan."""

    name: str = ""
    type: str = ""  # api | gui | e2e | encoder | sql | proto | graphql | nl | shell | unit | interaction
    version: Optional[str] = None
    lang: Optional[str] = None  # natural language code (e.g. "pl", "en")
    tags: list[str] = field(default_factory=list)
    extra: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        out: dict = {
            "name": self.name,
            "type": self.type,
            "tags": list(self.tags),
            "extra": dict(self.extra),
        }
        if self.version is not None:
            out["version"] = self.version
        if self.lang is not None:
            out["lang"] = self.lang
        return out

"""Fixture node for the Unified IR (setup/teardown)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Fixture:
    """Declarative setup/teardown for a TestPlan.

    Attributes:
        name: Identifier for the fixture (e.g. "db", "auth_token").
        setup: Setup payload (any structured data — adapter-specific).
        teardown: Teardown payload (optional).
        scope: "scenario" (default) | "session" | "step".
    """

    name: str
    setup: Optional[Any] = None
    teardown: Optional[Any] = None
    scope: str = "scenario"
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "setup": self.setup,
            "teardown": self.teardown,
            "scope": self.scope,
            "extra": dict(self.extra),
        }

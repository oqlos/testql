"""Placeholder for the WebSocket-based GraphQL subscription runner.

Phase 3 only declares the public surface so adapters and IR users can refer to
subscription steps. The runtime — including reuse of `interpreter._websockets`
— is intentionally deferred to the runner integration phase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubscriptionPlan:
    """Declarative description of a subscription step.

    Adapters parse subscription requests into this dataclass; the runner phase
    will consume it.
    """

    name: str
    body: str
    variables: dict[str, Any] = field(default_factory=dict)
    endpoint: str = ""
    expected_messages: int = 1
    timeout_ms: int = 5000

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "body": self.body,
            "variables": dict(self.variables),
            "endpoint": self.endpoint,
            "expected_messages": self.expected_messages,
            "timeout_ms": self.timeout_ms,
        }


__all__ = ["SubscriptionPlan"]

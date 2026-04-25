"""Optional LLM fallback for ambiguous NL lines.

Phase 1 only ships the *deterministic* path; this module is a
no-op-by-default stub so the adapter never makes an unexpected network call.
A subsequent phase can wire `costs`/`pfix` here without changing the public
interface.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol


@dataclass
class LLMSuggestion:
    """A best-guess intent + entities produced by an LLM fallback."""

    intent: str
    entities: dict
    confidence: float = 0.0
    rationale: str = ""


class LLMResolver(Protocol):
    def resolve(self, line: str, lang: str) -> Optional[LLMSuggestion]: ...  # pragma: no cover


class NoOpLLMResolver:
    """Default resolver — always returns `None` (no fallback)."""

    def resolve(self, line: str, lang: str) -> Optional[LLMSuggestion]:
        return None


_default_resolver: LLMResolver = NoOpLLMResolver()


def get_resolver() -> LLMResolver:
    return _default_resolver


def set_resolver(resolver: LLMResolver) -> None:
    """Install a custom resolver (e.g. an LLM-backed one in a higher layer)."""
    global _default_resolver
    _default_resolver = resolver


__all__ = ["LLMSuggestion", "LLMResolver", "NoOpLLMResolver", "get_resolver", "set_resolver"]

"""Resolve mock vs live LLM providers for conversation tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

from .live_llm import LiveLLMProvider
from .mock_llm import MockLLMProvider, load_mock_replies


class LLMProvider(Protocol):
    def reply_for(
        self,
        conversation_id: str,
        *,
        missing: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


def live_llm_enabled(explicit: bool | None = None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get("TESTQL_LIVE_LLM", "").strip().lower() in {"1", "true", "yes", "on"}


def resolve_llm_provider(
    *,
    live: bool | None = None,
    mock_replies: str | Path | None = None,
) -> LLMProvider:
    """Pick mock (default) or live LLM based on env / arguments."""
    if live_llm_enabled(live):
        return LiveLLMProvider.from_env()
    if mock_replies is not None:
        return load_mock_replies(mock_replies)
    env_file = os.environ.get("TESTQL_MOCK_LLM_FILE")
    if env_file:
        return load_mock_replies(env_file)
    return MockLLMProvider()

"""nlp2dsl adapter — conversation scenarios and SDK/HTTP bridge."""

from __future__ import annotations

from .client import Nlp2DslClient, Nlp2DslResponse
from .llm_provider import LLMProvider, live_llm_enabled, resolve_llm_provider
from .live_llm import LiveLLMProvider
from .mock_llm import MockLLMProvider, load_mock_replies
from .nlp2dsl_adapter import Nlp2DslAdapter

__all__ = [
    "Nlp2DslAdapter",
    "Nlp2DslClient",
    "Nlp2DslResponse",
    "LLMProvider",
    "LiveLLMProvider",
    "MockLLMProvider",
    "live_llm_enabled",
    "load_mock_replies",
    "resolve_llm_provider",
]

"""testql.adapters.nl — natural-language DSL adapter (Phase 1)."""

from __future__ import annotations

from .entity_extractor import (
    all_backticked,
    all_quoted,
    first_backtick,
    first_http_method,
    first_number,
    first_path,
    first_quoted,
    first_selector,
    split_on_preposition,
    strip_quotes_and_backticks,
    trim_field_nouns,
)
from .grammar import (
    Header,
    is_step_line,
    normalize,
    split_header_and_body,
    strip_step_prefix,
)
from .intent_recognizer import IntentMatch, recognize_intent, recognize_operator
from .lexicon import available, load_lexicon
from .llm_fallback import LLMResolver, LLMSuggestion, NoOpLLMResolver, get_resolver, set_resolver
from .nl_adapter import DEFAULT_LANG, NLDSLAdapter, parse, render

__all__ = [
    "NLDSLAdapter",
    "parse",
    "render",
    "DEFAULT_LANG",
    # Grammar / extraction primitives (re-exported for downstream tooling)
    "Header",
    "is_step_line",
    "normalize",
    "split_header_and_body",
    "strip_step_prefix",
    # Entity extractor
    "first_backtick",
    "all_backticked",
    "first_quoted",
    "all_quoted",
    "first_path",
    "first_selector",
    "first_http_method",
    "first_number",
    "split_on_preposition",
    "strip_quotes_and_backticks",
    "trim_field_nouns",
    # Recognizer
    "IntentMatch",
    "recognize_intent",
    "recognize_operator",
    # Lexicon
    "load_lexicon",
    "available",
    # LLM fallback (optional)
    "LLMSuggestion",
    "LLMResolver",
    "NoOpLLMResolver",
    "get_resolver",
    "set_resolver",
]

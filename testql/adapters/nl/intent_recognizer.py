"""Intent recognition for the NL adapter.

Given a normalised step line and a lexicon, return the best-matching intent
(longest verb-phrase wins) along with the residual text after the verb.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .grammar import normalize


@dataclass(frozen=True)
class IntentMatch:
    """Outcome of `recognize_intent`."""

    intent: str            # navigate | click | input | assert | wait | api | sql | encoder | unknown
    verb: str = ""         # the matched verb phrase (lower-cased)
    tail: str = ""         # text after the verb (preserves original casing)
    raw: str = ""          # original line
    confidence: float = 0.0
    extras: dict = field(default_factory=dict)  # e.g. {"prepositions": [...], "field_nouns": [...]}


def _intent_table(lexicon: dict) -> list[tuple[str, str, dict]]:
    """Flatten lexicon → list of `(verb_phrase, intent, extras)` sorted longest-first.

    Sorting longest-first guarantees that "wykonaj zapytanie sql" beats
    "wykonaj" when both are present.
    """
    table: list[tuple[str, str, dict]] = []
    intents = lexicon.get("intents", {})
    for intent, spec in intents.items():
        extras = {k: v for k, v in spec.items() if k != "verbs"}
        for verb in spec.get("verbs", []):
            table.append((normalize(verb), intent, extras))
    table.sort(key=lambda x: len(x[0]), reverse=True)
    return table


def recognize_intent(line: str, lexicon: dict) -> IntentMatch:
    """Return the best `IntentMatch` for `line` under `lexicon`.

    When no verb matches, the result has `intent == "unknown"`.
    """
    normalized = normalize(line)
    table = _intent_table(lexicon)
    for verb, intent, extras in table:
        if normalized == verb:
            return IntentMatch(intent=intent, verb=verb, tail="", raw=line,
                               confidence=1.0, extras=extras)
        prefix = f"{verb} "
        if normalized.startswith(prefix):
            # Recover original-case tail by chopping the same number of *raw*
            # tokens off the original line.
            verb_word_count = len(verb.split())
            raw_tokens = line.strip().split()
            tail = " ".join(raw_tokens[verb_word_count:])
            return IntentMatch(intent=intent, verb=verb, tail=tail, raw=line,
                               confidence=0.95, extras=extras)
    return IntentMatch(intent="unknown", raw=line, confidence=0.0)


# ── Operator recognition (used by ASSERT step builder) ──────────────────────


def recognize_operator(text: str, lexicon: dict) -> Optional[tuple[str, str]]:
    """Return `(canonical_op, matched_phrase)` for the first operator in `text`.

    `canonical_op` follows the IR vocabulary: `==`, `!=`, `>`, `<`, `>=`, `<=`,
    `contains`, `matches`. Returns `None` when no operator is present.
    """
    canonical = {
        "equal": "==",
        "not_equal": "!=",
        "greater": ">",
        "less": "<",
        "contains": "contains",
        "matches": "matches",
    }
    operators = lexicon.get("operators", {})
    candidates: list[tuple[int, str, str]] = []  # (start_idx, canonical, phrase)
    lowered = f" {normalize(text)} "
    for op_key, phrases in operators.items():
        if op_key not in canonical:
            continue
        for phrase in phrases:
            needle = f" {normalize(phrase)} "
            idx = lowered.find(needle)
            if idx != -1:
                candidates.append((idx, canonical[op_key], phrase))
    if not candidates:
        return None
    # Prefer the *earliest* match; on ties, prefer the longest phrase.
    candidates.sort(key=lambda x: (x[0], -len(x[2])))
    _, canon, phrase = candidates[0]
    return canon, phrase

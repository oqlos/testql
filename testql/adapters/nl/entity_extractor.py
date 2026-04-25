"""Entity extraction primitives for the NL adapter.

Each function takes a raw line (or a tail after a verb has been stripped) and
returns the best-effort extraction. They are deliberately small and composable
so a recognizer can mix-and-match them per intent.
"""

from __future__ import annotations

import re
from typing import Optional

from .grammar import (
    BACKTICK_RE,
    HTTP_METHOD_RE,
    NUMBER_RE,
    PATH_RE,
    QUOTED_RE,
    RAW_SELECTOR_RE,
)


def first_quoted(text: str) -> Optional[str]:
    """First single- or double-quoted literal in `text`, if any."""
    m = QUOTED_RE.search(text)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def all_quoted(text: str) -> list[str]:
    return [(m.group(1) if m.group(1) is not None else m.group(2)) for m in QUOTED_RE.finditer(text)]


def first_backtick(text: str) -> Optional[str]:
    m = BACKTICK_RE.search(text)
    return m.group(1) if m else None


def all_backticked(text: str) -> list[str]:
    return [m.group(1) for m in BACKTICK_RE.finditer(text)]


def first_path(text: str) -> Optional[str]:
    """First path-like token (must start with `/`)."""
    # Prefer a backticked path if present.
    bt = first_backtick(text)
    if bt and bt.startswith("/"):
        return bt
    # Then a quoted path.
    quoted = first_quoted(text)
    if quoted and quoted.startswith("/"):
        return quoted
    m = PATH_RE.search(text)
    return m.group(1) if m else None


def first_selector(text: str) -> Optional[str]:
    """First CSS-ish selector (backticked preferred, then raw)."""
    for bt in all_backticked(text):
        if bt.startswith("/"):
            continue
        if bt.startswith("[") or bt.startswith("#") or bt.startswith("."):
            return bt
        # Fall back to "anything in backticks that isn't a path"
        return bt
    m = RAW_SELECTOR_RE.search(text)
    return m.group(1) if m else None


def first_http_method(text: str) -> Optional[str]:
    m = HTTP_METHOD_RE.search(text)
    return m.group(1).upper() if m else None


def first_number(text: str) -> Optional[int]:
    m = NUMBER_RE.search(text)
    return int(m.group(1)) if m else None


def strip_quotes_and_backticks(text: str) -> str:
    """Remove all backtick / quoted spans from `text` (for residual prose)."""
    out = BACKTICK_RE.sub(" ", text)
    out = QUOTED_RE.sub(" ", out)
    return " ".join(out.split())


def split_on_preposition(text: str, prepositions: list[str]) -> tuple[str, Optional[str]]:
    """Split `text` at the first whole-word preposition.

    Returns `(before, after)`; `after` is `None` when no preposition matches.
    Prepositions are matched case-insensitively with word boundaries, so a
    preposition at the very start (or end) of `text` is also recognised.
    """
    if not prepositions:
        return text.strip(), None
    sorted_preps = sorted(prepositions, key=len, reverse=True)
    pattern = r"\b(?:" + "|".join(re.escape(p.lower()) for p in sorted_preps) + r")\b"
    m = re.search(pattern, text.lower())
    if not m:
        return text.strip(), None
    return text[:m.start()].strip(), text[m.end():].strip()


def trim_field_nouns(text: str, nouns: list[str]) -> str:
    """Remove a leading field-noun (e.g. "pole", "field") from a phrase."""
    if not nouns:
        return text.strip()
    parts = text.strip().split()
    if not parts:
        return text.strip()
    head = parts[0].lower().rstrip(":,.")
    if head in {n.lower() for n in nouns}:
        return " ".join(parts[1:]).strip()
    return text.strip()

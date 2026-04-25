"""Grammar primitives for the NL adapter.

Pure regex / string utilities — no I/O, no language data. The adapter combines
these primitives with a language-specific lexicon to recognise intents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# ── Header / metadata ───────────────────────────────────────────────────────

# `# SCENARIO: name`
SCENARIO_HEADER_RE = re.compile(r"^#\s*SCENARIO:\s*(.+)$", re.IGNORECASE)
# Either `TYPE: gui` or `# TYPE: gui` (and same for LANG, VERSION).
META_RE = re.compile(r"^#?\s*([A-Z_][A-Z0-9_]*):\s*(.+)$")

# Numbered list step: `1.`, `2)`, `- `, `* ` are accepted.
STEP_PREFIX_RE = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+")

# ── Entity primitives ───────────────────────────────────────────────────────

# Backtick-quoted blob — used for selectors and inline paths: `[data-x='y']`
BACKTICK_RE = re.compile(r"`([^`]+)`")
# Double- or single-quoted string literal.
QUOTED_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'')
# A `/path/like-this?with=query`. Must start with `/`.
PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(/[A-Za-z0-9_/\-?=&%.~]+)")
# CSS-ish selectors not in backticks (best-effort).
RAW_SELECTOR_RE = re.compile(r"(\[[^\]]+\]|#[A-Za-z][\w-]*|\.[A-Za-z][\w-]*)")
# HTTP verbs.
HTTP_METHOD_RE = re.compile(r"\b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\b", re.IGNORECASE)
# A standalone integer (HTTP status, count, ms, ...).
NUMBER_RE = re.compile(r"\b(\d+)\b")


@dataclass(frozen=True)
class Header:
    """Parsed header of a `.nl.md` file."""

    name: str = ""
    type: str = ""
    lang: Optional[str] = None
    version: Optional[str] = None
    extra: dict = None  # type: ignore[assignment]

    def merged_extra(self) -> dict:
        return dict(self.extra or {})


def is_step_line(line: str) -> bool:
    """Return True when `line` looks like a numbered/bulleted step."""
    return bool(STEP_PREFIX_RE.match(line))


def strip_step_prefix(line: str) -> str:
    """Drop the `1.`, `-`, `*` enumeration prefix from a step line."""
    return STEP_PREFIX_RE.sub("", line, count=1).strip()


_TOP_LEVEL_META = {"type", "lang", "version"}


def _apply_meta(key: str, value: str, state: dict) -> None:
    """Route a meta key/value pair into the right slot in `state`."""
    if key in _TOP_LEVEL_META:
        state[key] = value
    else:
        state["extra"][key] = value


def _consume_line(line: str, state: dict, steps: list[str]) -> None:
    """Classify one source line and update `state` / `steps` accordingly."""
    stripped = line.strip()
    if not stripped:
        return
    m_scenario = SCENARIO_HEADER_RE.match(stripped)
    if m_scenario:
        state["name"] = m_scenario.group(1).strip()
        return
    if is_step_line(line):
        steps.append(strip_step_prefix(line))
        return
    m_meta = META_RE.match(stripped)
    if m_meta:
        _apply_meta(m_meta.group(1).lower(), m_meta.group(2).strip(), state)


def split_header_and_body(text: str) -> tuple[Header, list[str]]:
    """Split a `.nl.md` source into a `Header` + ordered list of step lines.

    Skips blank lines, markdown headings (other than `# SCENARIO:`), and inline
    comments. Step lines retain their original text (minus the enumeration
    prefix) so downstream extractors see the raw content.
    """
    state: dict = {"name": "", "type": "", "lang": None, "version": None, "extra": {}}
    steps: list[str] = []
    for raw in text.splitlines():
        _consume_line(raw.rstrip(), state, steps)
    return Header(**state), steps


def normalize(text: str) -> str:
    """Lower-case + collapse whitespace. Used for verb / phrase matching."""
    return re.sub(r"\s+", " ", text.strip().lower())

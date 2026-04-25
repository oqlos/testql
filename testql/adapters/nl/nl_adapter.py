"""NLDSLAdapter — natural-language test scenarios → Unified IR.

Phase 1 deterministic path:

    text → split_header_and_body → for each step:
        recognize_intent(line, lexicon) → IntentMatch
        intent-specific builder → IR Step
    → TestPlan
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from testql.ir import (
    ApiStep,
    Assertion,
    EncoderStep,
    GuiStep,
    NlStep,
    ScenarioMetadata,
    SqlStep,
    Step,
    TestPlan,
)

from ..base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source
from . import entity_extractor as ee
from .grammar import Header, normalize, split_header_and_body
from .intent_recognizer import IntentMatch, recognize_intent, recognize_operator
from .lexicon import available as available_lexicons
from .lexicon import load_lexicon
from .llm_fallback import LLMSuggestion, get_resolver

DEFAULT_LANG = "en"


# ── Per-intent step builders ────────────────────────────────────────────────

def _build_navigate(match: IntentMatch, line: str) -> Step:
    path = ee.first_path(match.tail) or ee.first_path(line) or "/"
    return GuiStep(action="navigate", path=path, name="navigate")


def _build_click(match: IntentMatch, line: str) -> Step:
    selector = ee.first_selector(match.tail) or ee.first_selector(line)
    label = ee.first_quoted(match.tail) or ee.first_quoted(line)
    step = GuiStep(action="click", selector=selector, name="click")
    if label and not selector:
        step.value = label
    return step


def _build_input(match: IntentMatch, line: str) -> Step:
    preps = match.extras.get("prepositions", [])
    field_nouns = match.extras.get("field_nouns", [])
    value = ee.first_quoted(match.tail) or ee.first_quoted(line)
    # Selector resolution: search *after* the preposition first so quoted
    # values (e.g. "admin@example.com") don't poison `.com`-style selectors.
    residual = ee.strip_quotes_and_backticks(match.tail)
    _before, after = ee.split_on_preposition(residual, preps)
    selector: Optional[str] = None
    if after:
        selector = ee.first_selector(after) or ee.trim_field_nouns(after, field_nouns) or after
    if not selector:
        selector = ee.first_selector(match.tail) or ee.first_selector(line)
    return GuiStep(action="input", selector=selector, value=value, name="input")


def _build_assert(match: IntentMatch, line: str, lexicon: dict) -> Step:
    op_match = recognize_operator(match.tail, lexicon)
    op = op_match[0] if op_match else "=="
    field_name = _assert_field(match.tail, lexicon)
    expected = _assert_expected(match.tail)
    return Step(
        kind="assert",
        name="assert",
        asserts=[Assertion(field=field_name, op=op, expected=expected)],
    )


def _assert_field(tail: str, lexicon: dict) -> str:
    """Pick the best field name from an ASSERT tail."""
    nouns = lexicon.get("field_nouns", {})
    lowered = normalize(tail)
    for field_key, synonyms in nouns.items():
        for syn in synonyms:
            if normalize(syn) in lowered:
                return field_key
    selector = ee.first_selector(tail)
    if selector:
        return selector
    path = ee.first_path(tail)
    if path:
        return "url"
    bt = ee.first_backtick(tail)
    if bt:
        return bt
    return "result"


def _assert_expected(tail: str):
    """Pick the most plausible expected value from an ASSERT tail."""
    quoted = ee.first_quoted(tail)
    if quoted is not None:
        return quoted
    path = ee.first_path(tail)
    if path is not None:
        return path
    number = ee.first_number(tail)
    if number is not None:
        return number
    return None


def _build_wait(match: IntentMatch, line: str) -> Step:
    ms = ee.first_number(match.tail) or ee.first_number(line) or 100
    return Step(kind="wait", name="wait", wait_ms=int(ms))


def _api_status_part(status) -> tuple[list[Assertion], Optional[int]]:
    if status is None:
        return [], None
    return [Assertion(field="status", op="==", expected=int(status))], int(status)


def _build_api(match: IntentMatch, line: str) -> Step:
    method = ee.first_http_method(match.tail) or ee.first_http_method(line) or "GET"
    path = ee.first_path(match.tail) or ee.first_path(line) or "/"
    status = ee.first_number(match.tail) or ee.first_number(line)
    asserts, expect = _api_status_part(status)
    return ApiStep(method=method, path=path, expect_status=expect, asserts=asserts, name="api")


def _build_sql(match: IntentMatch, line: str) -> Step:
    quoted = ee.first_quoted(match.tail)
    bt = ee.first_backtick(match.tail)
    query = quoted or bt or match.tail.strip()
    return SqlStep(query=query, name="sql")


_ENCODER_VERB_TOKENS: tuple[tuple[str, str], ...] = (
    ("włącz", "on"), ("turn on", "on"),
    ("wyłącz", "off"), ("turn off", "off"),
    ("obróć", "scroll"), ("rotate", "scroll"),
    ("kliknij", "click"), ("click", "click"),
)


def _resolve_encoder_action(verb: str) -> str:
    lowered = verb.lower()
    for token, action in _ENCODER_VERB_TOKENS:
        if token in lowered:
            return action
    return "click"


def _build_encoder(match: IntentMatch, line: str) -> Step:
    action = _resolve_encoder_action(match.verb)
    target = ee.first_backtick(match.tail) or ee.first_quoted(match.tail)
    value = ee.first_number(match.tail)
    return EncoderStep(action=action, target=target, value=value, name="encoder")


_BUILDERS: dict[str, Callable[..., Step]] = {
    "navigate": _build_navigate,
    "click": _build_click,
    "input": _build_input,
    "wait": _build_wait,
    "api": _build_api,
    "sql": _build_sql,
    "encoder": _build_encoder,
}


def _build_step(match: IntentMatch, line: str, lexicon: dict, lang: str) -> Step:
    """Dispatch an `IntentMatch` to its builder; return an `NlStep` on miss."""
    if match.intent == "assert":
        return _build_assert(match, line, lexicon)
    builder = _BUILDERS.get(match.intent)
    if builder is not None:
        return builder(match, line)
    return _build_unresolved(line, lang)


def _build_unresolved(line: str, lang: str) -> Step:
    """Last-resort: optional LLM fallback, otherwise a raw `NlStep`."""
    suggestion: Optional[LLMSuggestion] = get_resolver().resolve(line, lang)
    if suggestion is None:
        return NlStep(text=line, lang=lang, name="nl-unresolved")
    return NlStep(text=line, lang=lang, name=f"nl-llm[{suggestion.intent}]",
                  extra={"llm_intent": suggestion.intent,
                         "llm_entities": suggestion.entities,
                         "llm_confidence": suggestion.confidence})


# ── IR → NL renderer ────────────────────────────────────────────────────────

def _render_api(step: ApiStep, en: bool) -> str:
    verb = "Send" if en else "Wyślij"
    suffix = f" ({step.expect_status})" if step.expect_status is not None else ""
    return f"{verb} {step.method} `{step.path}`{suffix}"


def _render_sql(step: SqlStep, en: bool) -> str:
    verb = "Run SQL query" if en else "Wykonaj zapytanie SQL"
    return f"{verb} `{step.query}`"


def _render_encoder(step: EncoderStep, en: bool) -> str:
    verb = "Encoder" if en else "Enkoder"
    return f"{verb} {step.action} {step.target or ''}".strip()


def _render_assert(step: Step, en: bool) -> str:
    if not step.asserts:
        return ("Check" if en else "Sprawdź")
    a = step.asserts[0]
    verb = "Check" if en else "Sprawdź"
    return f"{verb} that `{a.field}` {a.op} {a.expected!r}"


def _render_wait(step: Step, en: bool) -> str:
    return ("Wait" if en else "Poczekaj") + f" {step.wait_ms or 0} ms"


def _render_nl(step: NlStep, en: bool) -> str:
    return step.text


_GUI_RENDERERS: dict[str, Callable[..., str]] = {
    "navigate": lambda s, en: ("Open" if en else "Otwórz") + f" `{s.path or '/'}`",
    "click": lambda s, en: ("Click" if en else "Kliknij") + (f" `{s.selector or s.value or ''}`" if (s.selector or s.value) else ""),
    "input": lambda s, en: f'{"Type" if en else "Wprowadź"} "{s.value or ""}" {"into" if en else "do"} `{s.selector or ""}`',
}


def _render_gui(step: GuiStep, en: bool) -> str:
    renderer = _GUI_RENDERERS.get(step.action)
    return renderer(step, en) if renderer else f"GUI {step.action}"


# Type-keyed dispatch — kept tiny so radon CC stays low.
_RENDERERS_BY_TYPE: tuple[tuple[type, Callable[..., str]], ...] = (
    (GuiStep, lambda s, en: _render_gui(s, en)),
    (ApiStep, _render_api),
    (SqlStep, _render_sql),
    (EncoderStep, _render_encoder),
    (NlStep, _render_nl),
)


def _render_by_kind(step: Step, en: bool) -> Optional[str]:
    if step.kind == "assert":
        return _render_assert(step, en)
    if step.kind == "wait":
        return _render_wait(step, en)
    return None


def _render_step(step: Step, lang: str) -> str:
    """Inverse of the parsing pipeline (best-effort, deterministic verbs)."""
    en = lang != "pl"
    for cls, fn in _RENDERERS_BY_TYPE:
        if isinstance(step, cls):
            return fn(step, en)
    by_kind = _render_by_kind(step, en)
    if by_kind is not None:
        return by_kind
    return f"# unrendered: {step.kind}"


# ── Adapter ─────────────────────────────────────────────────────────────────

@dataclass
class NLDSLAdapter(BaseDSLAdapter):
    """Adapter for `*.nl.md` natural-language scenarios."""

    name: str = "nl"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".nl.md", ".nl.markdown"))

    # ── Detection ───────────────────────────────────────────────────────────

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.95, reason=f"extension {ext}")
        # Heuristic: numbered list with NL header.
        if "# SCENARIO:" in text and ("LANG:" in text or "TYPE:" in text):
            return DSLDetectionResult(matches=True, confidence=0.7, reason="NL header")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no NL markers")

    # ── Parse / render ──────────────────────────────────────────────────────

    def parse(self, source: SourceLike) -> TestPlan:
        text, _ = read_source(source)
        header, step_lines = split_header_and_body(text)
        lang = header.lang or DEFAULT_LANG
        lexicon = self._load_lexicon_safe(lang)
        plan = TestPlan(metadata=_metadata_from_header(header, lang))
        for line in step_lines:
            match = recognize_intent(line, lexicon)
            plan.steps.append(_build_step(match, line, lexicon, lang))
        return plan

    def render(self, plan: TestPlan) -> str:
        lang = plan.metadata.lang or DEFAULT_LANG
        out: list[str] = []
        if plan.metadata.name:
            out.append(f"# SCENARIO: {plan.metadata.name}")
        if plan.metadata.type:
            out.append(f"TYPE: {plan.metadata.type}")
        out.append(f"LANG: {lang}")
        out.append("")
        for i, step in enumerate(plan.steps, start=1):
            out.append(f"{i}. {_render_step(step, lang)}")
        return "\n".join(out) + "\n"

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _load_lexicon_safe(lang: str) -> dict:
        try:
            return load_lexicon(lang)
        except FileNotFoundError:
            if lang != DEFAULT_LANG and DEFAULT_LANG in available_lexicons():
                return load_lexicon(DEFAULT_LANG)
            raise


def _metadata_from_header(header: Header, lang: str) -> ScenarioMetadata:
    return ScenarioMetadata(
        name=header.name,
        type=header.type or "nl",
        version=header.version,
        lang=lang,
        extra=header.merged_extra(),
    )


# ── Convenience module-level helpers ─────────────────────────────────────

def parse(source: SourceLike) -> TestPlan:
    return NLDSLAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return NLDSLAdapter().render(plan)


__all__ = ["NLDSLAdapter", "parse", "render", "DEFAULT_LANG"]

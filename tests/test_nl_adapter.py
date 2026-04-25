"""Tests for `testql.adapters.nl.nl_adapter`."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.nl import (
    NLDSLAdapter,
    LLMSuggestion,
    parse,
    render,
    set_resolver,
)
from testql.adapters.nl.llm_fallback import NoOpLLMResolver
from testql.ir import (
    ApiStep,
    EncoderStep,
    GuiStep,
    NlStep,
    SqlStep,
    Step,
    TestPlan,
)


PL_LOGIN = """\
# SCENARIO: Logowanie użytkownika
TYPE: gui
LANG: pl

1. Otwórz `/login`
2. Wprowadź "admin@example.com" do pola email
3. Wprowadź "password123" do pola hasło
4. Kliknij `[data-testid='submit']`
5. Sprawdź że widoczny jest element `[data-testid='dashboard']`
6. Sprawdź że URL zawiera "/dashboard"
"""

EN_API = """\
# SCENARIO: API smoke
TYPE: api
LANG: en

1. Send GET /api/health
2. Check that status is 200
3. Send POST /api/items
4. Wait 500
"""


class TestDetect:
    def test_detect_by_extension(self, tmp_path: Path):
        p = tmp_path / "x.nl.md"
        p.write_text(PL_LOGIN, encoding="utf-8")
        result = NLDSLAdapter().detect(p)
        assert result.matches
        assert result.confidence >= 0.9

    def test_detect_by_header(self):
        result = NLDSLAdapter().detect(PL_LOGIN)
        assert result.matches

    def test_negative(self):
        result = NLDSLAdapter().detect("just text\n")
        assert not result.matches


class TestParseHeader:
    def test_metadata(self):
        plan = parse(PL_LOGIN)
        assert plan.metadata.name == "Logowanie użytkownika"
        assert plan.metadata.type == "gui"
        assert plan.metadata.lang == "pl"

    def test_default_lang_when_missing(self):
        plan = parse("# SCENARIO: x\nTYPE: gui\n\n1. Open `/`")
        assert plan.metadata.lang == "en"

    def test_default_type_when_missing(self):
        plan = parse("# SCENARIO: x\nLANG: en\n\n1. Open `/`")
        assert plan.metadata.type == "nl"


class TestParsePolishLoginScenario:
    @pytest.fixture
    def plan(self) -> TestPlan:
        return parse(PL_LOGIN)

    def test_step_count(self, plan):
        assert len(plan.steps) == 6

    def test_navigate(self, plan):
        s = plan.steps[0]
        assert isinstance(s, GuiStep)
        assert s.action == "navigate"
        assert s.path == "/login"

    def test_input_email(self, plan):
        s = plan.steps[1]
        assert isinstance(s, GuiStep)
        assert s.action == "input"
        assert s.value == "admin@example.com"
        assert s.selector == "email"

    def test_input_password(self, plan):
        s = plan.steps[2]
        assert isinstance(s, GuiStep)
        assert s.action == "input"
        assert s.value == "password123"
        assert s.selector == "hasło"

    def test_click(self, plan):
        s = plan.steps[3]
        assert isinstance(s, GuiStep)
        assert s.action == "click"
        assert s.selector == "[data-testid='submit']"

    def test_assert_visible(self, plan):
        s = plan.steps[4]
        assert s.kind == "assert"
        a = s.asserts[0]
        # Visible-element check resolves field to selector.
        assert a.field in {"[data-testid='dashboard']", "visible", "element"}

    def test_assert_url_contains(self, plan):
        s = plan.steps[5]
        assert s.kind == "assert"
        a = s.asserts[0]
        assert a.field == "url"
        assert a.op == "contains"
        assert a.expected == "/dashboard"


class TestParseEnglishApiScenario:
    @pytest.fixture
    def plan(self) -> TestPlan:
        return parse(EN_API)

    def test_count(self, plan):
        assert len(plan.steps) == 4

    def test_get(self, plan):
        s = plan.steps[0]
        assert isinstance(s, ApiStep)
        assert s.method == "GET"
        assert s.path == "/api/health"

    def test_status_assert(self, plan):
        s = plan.steps[1]
        assert s.kind == "assert"
        a = s.asserts[0]
        assert a.field == "status"
        assert a.op == "=="
        assert a.expected == 200

    def test_post(self, plan):
        s = plan.steps[2]
        assert isinstance(s, ApiStep)
        assert s.method == "POST"

    def test_wait(self, plan):
        s = plan.steps[3]
        assert s.kind == "wait"
        assert s.wait_ms == 500


class TestParseUnresolved:
    def test_unknown_line_becomes_nl_step(self):
        plan = parse("# SCENARIO: x\nLANG: en\n\n1. Definitely-not-a-verb something\n")
        s = plan.steps[0]
        assert isinstance(s, NlStep)
        assert s.text == "Definitely-not-a-verb something"

    def test_llm_fallback_when_resolver_set(self):
        class Stub(NoOpLLMResolver):
            def resolve(self, line: str, lang: str):
                return LLMSuggestion(intent="navigate", entities={"path": "/x"}, confidence=0.42)

        set_resolver(Stub())
        try:
            plan = parse("# SCENARIO: x\nLANG: en\n\n1. Foozle bar\n")
            s = plan.steps[0]
            assert isinstance(s, NlStep)
            assert "llm" in (s.name or "")
            assert s.extra["llm_intent"] == "navigate"
            assert s.extra["llm_confidence"] == 0.42
        finally:
            set_resolver(NoOpLLMResolver())


class TestSqlAndEncoder:
    def test_sql_intent(self):
        plan = parse("# SCENARIO: q\nLANG: pl\n\n1. Wykonaj zapytanie SQL `SELECT 1`\n")
        s = plan.steps[0]
        assert isinstance(s, SqlStep)
        assert s.query == "SELECT 1"

    def test_encoder_on(self):
        plan = parse("# SCENARIO: e\nLANG: pl\n\n1. Włącz enkoder\n")
        s = plan.steps[0]
        assert isinstance(s, EncoderStep)
        assert s.action == "on"

    def test_encoder_click(self):
        plan = parse("# SCENARIO: e\nLANG: pl\n\n1. Kliknij enkoder\n")
        s = plan.steps[0]
        assert isinstance(s, EncoderStep)
        assert s.action == "click"


class TestRender:
    def test_round_trip_preserves_intents(self):
        plan = parse(PL_LOGIN)
        rendered = render(plan)
        plan2 = parse(rendered)
        assert len(plan.steps) == len(plan2.steps)
        # First step should still be a navigate.
        assert isinstance(plan2.steps[0], GuiStep)
        assert plan2.steps[0].action == "navigate"
        assert plan2.steps[0].path == "/login"

    def test_render_includes_header(self):
        plan = parse(PL_LOGIN)
        out = render(plan)
        assert "# SCENARIO: Logowanie użytkownika" in out
        assert "TYPE: gui" in out
        assert "LANG: pl" in out


class TestAdapterRegistration:
    def test_registered(self):
        from testql.adapters import registry
        a = registry.get("nl")
        assert a is not None
        assert isinstance(a, NLDSLAdapter)

    def test_extension_lookup(self, tmp_path: Path):
        from testql.adapters import registry
        p = tmp_path / "x.nl.md"
        p.write_text(EN_API, encoding="utf-8")
        a = registry.by_extension(p)
        assert a is not None
        assert a.name == "nl"


class TestDeterministicCoverage:
    """Plan gate: ≥95% of intent-bearing lines resolve deterministically."""

    PHRASES_PL = [
        "Otwórz /login",
        "Przejdź do /dashboard",
        "Idź na /home",
        "Wejdź na /admin",
        "Kliknij `#login`",
        "Naciśnij przycisk `#submit`",
        'Wprowadź "X" do pola email',
        'Wpisz "Y" w polu hasło',
        "Sprawdź że status to 200",
        "Zweryfikuj że URL zawiera /dashboard",
        "Poczekaj 500",
        "Wykonaj GET /api/x",
        "Wyślij POST /api/y",
        "Wykonaj zapytanie SQL `SELECT 1`",
        "Włącz enkoder",
        "Wyłącz enkoder",
        "Kliknij enkoder",
    ]

    def test_polish_coverage(self):
        from testql.adapters.nl.intent_recognizer import recognize_intent
        from testql.adapters.nl.lexicon import load_lexicon
        lex = load_lexicon("pl")
        unresolved = [p for p in self.PHRASES_PL if recognize_intent(p, lex).intent == "unknown"]
        # ≥95% deterministic (i.e. ≤5% unknown)
        assert len(unresolved) / len(self.PHRASES_PL) <= 0.05, f"unresolved: {unresolved}"

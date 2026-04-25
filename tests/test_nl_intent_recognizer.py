"""Tests for `testql.adapters.nl.intent_recognizer`."""

from __future__ import annotations

import pytest

from testql.adapters.nl.intent_recognizer import recognize_intent, recognize_operator
from testql.adapters.nl.lexicon import load_lexicon


@pytest.fixture
def pl():
    return load_lexicon("pl")


@pytest.fixture
def en():
    return load_lexicon("en")


class TestRecognizeIntentPolish:
    def test_navigate(self, pl):
        m = recognize_intent("Otwórz /login", pl)
        assert m.intent == "navigate"
        assert m.tail == "/login"
        assert m.confidence >= 0.95

    def test_navigate_multi_word(self, pl):
        m = recognize_intent("Przejdź do /dashboard", pl)
        assert m.intent == "navigate"
        assert m.tail == "/dashboard"

    def test_click(self, pl):
        m = recognize_intent("Kliknij `[data-x='y']`", pl)
        assert m.intent == "click"

    def test_input(self, pl):
        m = recognize_intent('Wprowadź "X" do pola email', pl)
        assert m.intent == "input"
        assert "prepositions" in m.extras
        assert "field_nouns" in m.extras

    def test_assert(self, pl):
        m = recognize_intent("Sprawdź że status to 200", pl)
        assert m.intent == "assert"

    def test_wait(self, pl):
        m = recognize_intent("Poczekaj 500", pl)
        assert m.intent == "wait"

    def test_api(self, pl):
        m = recognize_intent("Wykonaj GET /api/health", pl)
        assert m.intent == "api"

    def test_sql(self, pl):
        m = recognize_intent("Zapytaj SELECT * FROM users", pl)
        assert m.intent == "sql"

    def test_encoder(self, pl):
        m = recognize_intent("Włącz enkoder", pl)
        assert m.intent == "encoder"

    def test_unknown(self, pl):
        m = recognize_intent("blah blah blah", pl)
        assert m.intent == "unknown"
        assert m.confidence == 0.0


class TestRecognizeIntentEnglish:
    def test_navigate(self, en):
        m = recognize_intent("Open /login", en)
        assert m.intent == "navigate"

    def test_navigate_multi_word(self, en):
        m = recognize_intent("Go to /home", en)
        assert m.intent == "navigate"
        assert m.tail == "/home"

    def test_click(self, en):
        m = recognize_intent("Click `#login`", en)
        assert m.intent == "click"

    def test_input(self, en):
        m = recognize_intent('Type "X" into field', en)
        assert m.intent == "input"

    def test_api(self, en):
        m = recognize_intent("Send GET /api/x", en)
        assert m.intent == "api"

    def test_assert(self, en):
        m = recognize_intent("Check that status is 200", en)
        assert m.intent == "assert"


class TestLongestMatchWins:
    def test_wykonaj_zapytanie_sql_beats_wykonaj(self, pl):
        m = recognize_intent("Wykonaj zapytanie SQL SELECT 1", pl)
        # Longest verb wins → sql, not api ("wykonaj")
        assert m.intent == "sql"


class TestRecognizeOperator:
    def test_equal_pl(self, pl):
        op = recognize_operator("status to 200", pl)
        assert op is not None
        assert op[0] == "=="

    def test_contains(self, pl):
        op = recognize_operator("URL zawiera /dashboard", pl)
        assert op is not None
        assert op[0] == "contains"

    def test_greater(self, pl):
        op = recognize_operator("liczba większa niż 5", pl)
        assert op is not None
        assert op[0] == ">"

    def test_no_operator(self, pl):
        assert recognize_operator("nothing", pl) is None

    def test_not_equal_takes_precedence_over_equal_when_same_position(self, pl):
        # "nie jest" appears earlier than "jest" in the line — earliest wins.
        op = recognize_operator("status nie jest 500", pl)
        assert op is not None
        # Earliest match wins; "nie jest" starts before "jest".
        assert op[0] == "!="

    def test_english_equal(self, en):
        op = recognize_operator("status is 200", en)
        assert op is not None
        assert op[0] == "=="

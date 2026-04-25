"""Tests for `testql.adapters.nl.entity_extractor`."""

from __future__ import annotations

from testql.adapters.nl.entity_extractor import (
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


class TestQuoted:
    def test_double_quoted(self):
        assert first_quoted('Type "hello" into x') == "hello"

    def test_single_quoted(self):
        assert first_quoted("type 'hello' into x") == "hello"

    def test_no_match(self):
        assert first_quoted("nothing here") is None

    def test_all_quoted(self):
        assert all_quoted('"a" and "b"') == ["a", "b"]


class TestBacktick:
    def test_first(self):
        assert first_backtick("click `#login`") == "#login"

    def test_all(self):
        assert all_backticked("`a` and `b`") == ["a", "b"]

    def test_none(self):
        assert first_backtick("plain text") is None


class TestPath:
    def test_backticked_path(self):
        assert first_path("Open `/login`") == "/login"

    def test_quoted_path(self):
        assert first_path('Open "/login"') == "/login"

    def test_raw_path(self):
        assert first_path("Open /login now") == "/login"

    def test_path_with_query(self):
        assert first_path("GET /api/users?id=1") == "/api/users?id=1"

    def test_no_path(self):
        assert first_path("nothing") is None

    def test_does_not_match_word_with_slash(self):
        # word/word should not be treated as a path (no leading boundary).
        assert first_path("foo/bar") is None


class TestSelector:
    def test_attribute_selector(self):
        assert first_selector("click `[data-testid='x']`") == "[data-testid='x']"

    def test_id_selector(self):
        assert first_selector("click `#login`") == "#login"

    def test_class_selector(self):
        assert first_selector("click `.btn-primary`") == ".btn-primary"

    def test_raw_selector(self):
        assert first_selector("click [data-x='y']") == "[data-x='y']"

    def test_skips_path(self):
        # `/login` is a path, not a selector — selector should miss.
        assert first_selector("Open `/login` now") is None

    def test_none(self):
        assert first_selector("nothing") is None


class TestHttpMethod:
    def test_get(self):
        assert first_http_method("Send GET /api/x") == "GET"

    def test_lowercase(self):
        assert first_http_method("send post /api/x") == "POST"

    def test_no_method(self):
        assert first_http_method("ping") is None


class TestNumber:
    def test_simple(self):
        assert first_number("status 200") == 200

    def test_negative_not_supported(self):
        # Phase 1: numbers are unsigned; first non-negative wins.
        assert first_number("delta -5 then 200") == 5

    def test_no_number(self):
        assert first_number("none") is None


class TestStripQuotesAndBackticks:
    def test_removes_all(self):
        assert strip_quotes_and_backticks('Type "X" into `#login`') == "Type into"


class TestSplitOnPreposition:
    def test_polish_do(self):
        before, after = split_on_preposition("Wprowadź email do pole_email", ["do", "w", "na"])
        assert before == "Wprowadź email"
        assert after == "pole_email"

    def test_english_into(self):
        before, after = split_on_preposition("Type X into field", ["into", "in", "to"])
        assert before == "Type X"
        assert after == "field"

    def test_no_preposition(self):
        before, after = split_on_preposition("Wprowadź email", ["do", "w"])
        assert before == "Wprowadź email"
        assert after is None

    def test_picks_earliest(self):
        before, after = split_on_preposition("type x in y in z", ["in"])
        assert before == "type x"
        assert after == "y in z"

    def test_empty_prepositions(self):
        before, after = split_on_preposition("anything", [])
        assert before == "anything"
        assert after is None


class TestTrimFieldNouns:
    def test_trims_pole(self):
        assert trim_field_nouns("pole email", ["pole", "pola"]) == "email"

    def test_trims_pola(self):
        assert trim_field_nouns("pola hasło", ["pole", "pola"]) == "hasło"

    def test_does_not_trim_other_words(self):
        assert trim_field_nouns("input email", ["pole", "pola"]) == "input email"

    def test_empty(self):
        assert trim_field_nouns("", ["pole"]) == ""
        assert trim_field_nouns("pole", []) == "pole"

"""Tests for `testql.adapters.nl.grammar`."""

from __future__ import annotations

from testql.adapters.nl.grammar import (
    Header,
    is_step_line,
    normalize,
    split_header_and_body,
    strip_step_prefix,
)


class TestStepDetection:
    def test_numbered_dot(self):
        assert is_step_line("1. Otwórz /login")

    def test_numbered_paren(self):
        assert is_step_line("1) Click")

    def test_dash_bullet(self):
        assert is_step_line("- Click")

    def test_star_bullet(self):
        assert is_step_line("* Open page")

    def test_indented_bullet(self):
        assert is_step_line("  - Click")

    def test_not_a_step(self):
        assert not is_step_line("# SCENARIO: x")
        assert not is_step_line("LANG: pl")
        assert not is_step_line("")


class TestStripPrefix:
    def test_dot(self):
        assert strip_step_prefix("1. Open") == "Open"

    def test_paren(self):
        assert strip_step_prefix("12) Open") == "Open"

    def test_dash(self):
        assert strip_step_prefix("- Open") == "Open"

    def test_idempotent_for_non_steps(self):
        assert strip_step_prefix("Open") == "Open"


class TestSplitHeaderAndBody:
    def test_basic(self):
        text = """\
# SCENARIO: Login
TYPE: gui
LANG: pl
VERSION: 1.0
TAGS: smoke

1. Otwórz `/login`
2. Kliknij `[data-testid='submit']`
"""
        header, steps = split_header_and_body(text)
        assert header.name == "Login"
        assert header.type == "gui"
        assert header.lang == "pl"
        assert header.version == "1.0"
        assert header.extra == {"tags": "smoke"}
        assert len(steps) == 2
        assert steps[0].startswith("Otwórz")
        assert steps[1].startswith("Kliknij")

    def test_handles_hash_prefix_meta(self):
        header, steps = split_header_and_body("# SCENARIO: x\n# TYPE: api\n# LANG: en\n\n1. Open `/`\n")
        assert header.type == "api"
        assert header.lang == "en"
        assert len(steps) == 1

    def test_empty(self):
        header, steps = split_header_and_body("")
        assert header == Header(name="", type="", lang=None, version=None, extra={})
        assert steps == []

    def test_only_steps_no_header(self):
        header, steps = split_header_and_body("1. Open `/`\n2. Click `#x`\n")
        assert header.name == ""
        assert header.type == ""
        assert len(steps) == 2

    def test_skips_blank_and_unknown_lines(self):
        text = "# SCENARIO: x\n\nrandom prose\n\n1. Open\n"
        _, steps = split_header_and_body(text)
        assert steps == ["Open"]


class TestNormalize:
    def test_lowers_and_collapses_whitespace(self):
        assert normalize("  Open\tThe\nPage  ") == "open the page"

    def test_idempotent(self):
        assert normalize(normalize("HELLO  WORLD")) == "hello world"

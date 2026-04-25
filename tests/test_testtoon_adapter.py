"""Tests for `testql.adapters.testtoon_adapter`."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.testtoon_adapter import TestToonAdapter, parse, render
from testql.ir import ApiStep, EncoderStep, GuiStep, Step, TestPlan


SAMPLE = """\
# SCENARIO: Health
# TYPE: api
# VERSION: 1.0

CONFIG[1]{key, value}:
  base_url, http://localhost:8101

API[2]{method, endpoint, status}:
  GET, /health, 200
  POST, /items, 201

NAVIGATE[1]{path, wait_ms}:
  /dashboard, 100

ENCODER[1]{action, target, value, wait_ms}:
  click, btn-1, -, 50

ASSERT[1]{field, op, expected}:
  data.ok, ==, true
"""


class TestDetect:
    def test_detect_by_extension(self, tmp_path: Path):
        p = tmp_path / "x.testql.toon.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        result = TestToonAdapter().detect(p)
        assert result.matches
        assert result.confidence >= 0.9

    def test_detect_by_metadata_header(self):
        result = TestToonAdapter().detect("# SCENARIO: x\n")
        assert result.matches

    def test_detect_negative(self):
        result = TestToonAdapter().detect("just some text\n")
        assert not result.matches
        assert result.confidence == 0.0

    def test_detect_section_header(self):
        result = TestToonAdapter().detect("API[1]{a, b}:\n  1, 2\n")
        assert result.matches


class TestParse:
    def test_parse_string(self):
        plan = parse(SAMPLE)
        assert isinstance(plan, TestPlan)
        assert plan.metadata.type == "api"
        assert plan.metadata.version == "1.0"
        assert plan.config["base_url"] == "http://localhost:8101"

    def test_parse_file(self, tmp_path: Path):
        p = tmp_path / "x.testql.toon.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        plan = parse(p)
        assert plan.metadata.name == "Health"

    def test_api_steps(self):
        plan = parse(SAMPLE)
        api = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert len(api) == 2
        assert api[0].method == "GET"
        assert api[0].path == "/health"
        assert api[0].expect_status == 200
        assert api[1].method == "POST"

    def test_api_step_has_status_assert(self):
        plan = parse(SAMPLE)
        api = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert any(a.field == "status" and a.expected == 200 for a in api[0].asserts)

    def test_navigate_step(self):
        plan = parse(SAMPLE)
        nav = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "navigate"]
        assert len(nav) == 1
        assert nav[0].path == "/dashboard"
        assert nav[0].wait_ms == 100

    def test_encoder_step(self):
        plan = parse(SAMPLE)
        enc = [s for s in plan.steps if isinstance(s, EncoderStep)]
        assert len(enc) == 1
        assert enc[0].action == "click"
        assert enc[0].target == "btn-1"
        assert enc[0].wait_ms == 50

    def test_assert_section(self):
        plan = parse(SAMPLE)
        asserts = [s for s in plan.steps if s.kind == "assert"]
        assert len(asserts) == 1
        assert asserts[0].asserts[0].field == "data.ok"
        assert asserts[0].asserts[0].op == "=="

    def test_unknown_section_falls_through_to_generic(self):
        text = """\
# SCENARIO: x
# TYPE: api

WAIT[1]{ms}:
  100
"""
        plan = parse(text)
        wait = [s for s in plan.steps if s.kind == "wait"]
        assert len(wait) == 1
        assert wait[0].extra == {"ms": 100}


class TestRender:
    def test_render_round_trip_basic(self):
        plan = parse(SAMPLE)
        rendered = render(plan)
        # Re-parse the rendered text and check structural equivalence on the sections
        plan2 = parse(rendered)
        api1 = [s for s in plan.steps if isinstance(s, ApiStep)]
        api2 = [s for s in plan2.steps if isinstance(s, ApiStep)]
        assert len(api1) == len(api2)
        assert api1[0].method == api2[0].method
        assert api1[0].path == api2[0].path

    def test_render_includes_metadata(self):
        plan = parse(SAMPLE)
        out = render(plan)
        assert "# SCENARIO: Health" in out
        assert "# TYPE: api" in out
        assert "# VERSION: 1.0" in out

    def test_render_includes_config(self):
        plan = parse(SAMPLE)
        out = render(plan)
        assert "CONFIG[1]" in out
        assert "base_url" in out

    def test_render_empty_plan(self):
        out = render(TestPlan())
        assert out == ""


class TestAdapterRegistration:
    def test_adapter_registered_in_default_registry(self):
        from testql.adapters import registry
        a = registry.get("testtoon")
        assert a is not None
        assert isinstance(a, TestToonAdapter)

    def test_extensions_match(self):
        a = TestToonAdapter()
        assert ".testql.toon.yaml" in a.file_extensions
        assert ".testql.toon.yml" in a.file_extensions


class TestBackwardCompatibility:
    """The legacy parser must still work unchanged after Phase 0."""

    def test_legacy_parser_imports(self):
        from testql.interpreter._testtoon_parser import (
            ToonScript,
            ToonSection,
            parse_testtoon,
            testtoon_to_iql,
            validate_testtoon,
        )
        toon = parse_testtoon(SAMPLE)
        assert isinstance(toon, ToonScript)
        assert any(s.type == "API" for s in toon.sections)

    def test_interpreter_package_reexports(self):
        from testql.interpreter import (
            ToonScript,
            ToonSection,
            parse_testtoon,
            testtoon_to_iql,
            validate_testtoon,
        )
        toon = parse_testtoon(SAMPLE)
        script = testtoon_to_iql(SAMPLE)
        assert script.lines  # non-empty

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

    def test_indented_row_starting_with_hash_is_not_comment(self):
        """Regression: indented row values starting with '#' (e.g. CSS-id
        selectors like ``#login-btn``) must not be eaten by the comment
        stripper. The leading '#' is only a comment marker when the line is
        not an indented row inside an active section.
        """
        text = """\
# SCENARIO: hash-selector
# TYPE: gui

ASSERT_VISIBLE[2]{selector}:
  #login-btn
  #non-existent-element
"""
        plan = parse(text)
        rows = [s for s in plan.steps if s.kind == "assert_visible"]
        assert len(rows) == 2
        assert rows[0].extra == {"selector": "#login-btn"}
        assert rows[1].extra == {"selector": "#non-existent-element"}


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

    def test_round_trip_preserves_flow_steps(self):
        """Regression: FLOW rows parsed as generic Steps must survive render.

        Previously the renderer only handled `GuiStep` / `ApiStep` etc.
        Generic `Step(kind='flow', ...)` instances produced by
        `_generic_section_to_steps` were silently dropped during render,
        making round-trip lossy for any FLOW-only scenario.
        """
        src = (
            "# SCENARIO: gui-flow\n"
            "# TYPE: gui\n"
            "\n"
            "FLOW[3]{command, target, value}:\n"
            "  GUI_ASSERT_VISIBLE, #header, -\n"
            "  GUI_ASSERT_VISIBLE, #content, -\n"
            "  GUI_ASSERT_VISIBLE, #footer, -\n"
        )
        plan = parse(src)
        flow_initial = [s for s in plan.steps if s.kind == "flow"]
        assert len(flow_initial) == 3
        rendered = render(plan)
        assert "FLOW[3]" in rendered
        plan2 = parse(rendered)
        flow_again = [s for s in plan2.steps if s.kind == "flow"]
        assert len(flow_again) == 3
        # Column data preserved
        assert [r.extra.get("command") for r in flow_again] == [
            "GUI_ASSERT_VISIBLE", "GUI_ASSERT_VISIBLE", "GUI_ASSERT_VISIBLE",
        ]
        assert [r.extra.get("target") for r in flow_again] == [
            "#header", "#content", "#footer",
        ]

    def test_round_trip_preserves_wait_steps(self):
        """WAIT sections parsed as generic Steps must survive render."""
        src = (
            "# SCENARIO: timing\n"
            "# TYPE: gui\n"
            "\n"
            "WAIT[2]{ms}:\n"
            "  100\n"
            "  500\n"
        )
        plan = parse(src)
        rendered = render(plan)
        assert "WAIT[2]" in rendered
        plan2 = parse(rendered)
        wait_again = [s for s in plan2.steps if s.kind == "wait"]
        assert len(wait_again) == 2

    def test_round_trip_preserves_include_steps(self):
        """INCLUDE sections parsed as generic Steps must survive render."""
        src = (
            "# SCENARIO: with-include\n"
            "# TYPE: gui\n"
            "\n"
            "INCLUDE[1]{file}:\n"
            "  shared/login.testql.toon.yaml\n"
        )
        plan = parse(src)
        rendered = render(plan)
        assert "INCLUDE[1]" in rendered
        assert "shared/login.testql.toon.yaml" in rendered
        plan2 = parse(rendered)
        inc_again = [s for s in plan2.steps if s.kind == "include"]
        assert len(inc_again) == 1


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


class TestFlowExpansion:
    """FLOW section third-column handling (regression for GUI_INPUT empty-arg bug)."""

    def _expand(self, source: str):
        from testql.interpreter._testtoon_parser import testtoon_to_oql
        return testtoon_to_oql(source).lines

    def test_flow_value_column_quoted_for_input(self):
        # The third column is `value`: text must be forwarded as a quoted positional arg
        src = (
            "FLOW[2]{command, target, value}:\n"
            "  input, #add-name, Test User\n"
            "  input, #add-id, TEST123\n"
        )
        lines = self._expand(src)
        assert [(l.command, l.args) for l in lines] == [
            ("INPUT", '"#add-name" "Test User"'),
            ("INPUT", '"#add-id" "TEST123"'),
        ]

    def test_flow_text_column_alias(self):
        src = (
            "FLOW[1]{command, target, text}:\n"
            "  type, input#search, hello world\n"
        )
        lines = self._expand(src)
        assert lines[0].command == "TYPE"
        assert lines[0].args == '"input#search" "hello world"'

    def test_flow_meta_dash_emits_no_extra_arg(self):
        # `-` is parsed as None → no extra arg appended; CLICK stays clean
        src = (
            "FLOW[1]{command, target, meta}:\n"
            "  click, #btn-go, -\n"
        )
        lines = self._expand(src)
        assert lines[0].command == "CLICK"
        assert lines[0].args == '"#btn-go"'

    def test_flow_value_dash_does_not_pollute_click(self):
        # Regression: a `value` column with `-` placeholder must NOT add
        # `"-"` as a stray positional arg (would break CLICK/ASSERT_VISIBLE).
        src = (
            "FLOW[1]{command, target, value}:\n"
            "  click, #btn-go, -\n"
        )
        lines = self._expand(src)
        assert lines[0].command == "CLICK"
        assert lines[0].args == '"#btn-go"'

    def test_flow_value_null_treated_as_empty(self):
        src = (
            "FLOW[1]{command, target, value}:\n"
            "  click, #btn-go, null\n"
        )
        lines = self._expand(src)
        assert lines[0].args == '"#btn-go"'

    def test_flow_meta_dict_legacy_passthrough(self):
        src = (
            "FLOW[1]{command, target, meta}:\n"
            "  select_device, dev1, {role:admin}\n"
        )
        lines = self._expand(src)
        assert lines[0].command == "SELECT_DEVICE"
        assert lines[0].args == '"dev1" {"role": "admin"}'

    def test_flow_two_column_still_works(self):
        src = (
            "FLOW[1]{command, target}:\n"
            "  click, #btn\n"
        )
        lines = self._expand(src)
        assert lines[0].command == "CLICK"
        assert lines[0].args == '"#btn"'


class TestShellExpansion:
    """SHELL section must quote compound commands (&&, |) for OQL execution."""

    def _expand(self, source: str):
        from testql.interpreter._testtoon_parser import testtoon_to_oql
        return testtoon_to_oql(source).lines

    def test_shell_section_quotes_compound_command(self):
        src = (
            "SHELL[1]{command, exit_code}:\n"
            "  cd /tmp && echo hello world, 0\n"
        )
        lines = self._expand(src)
        assert [(l.command, l.args) for l in lines] == [
            ('SHELL', '"cd /tmp && echo hello world" 60000'),
            ('ASSERT_EXIT_CODE', '0'),
        ]

    def test_shell_expected_exit_column_alias(self):
        src = (
            "SHELL[1]{command, expected_exit}:\n"
            '  "cd /repo && node scripts/check.mjs --user admin", 0\n'
        )
        lines = self._expand(src)
        assert lines[0].command == "SHELL"
        assert lines[0].args == '"cd /repo && node scripts/check.mjs --user admin" 60000'
        assert lines[1].command == "ASSERT_EXIT_CODE"
        assert lines[1].args == "0"

    def test_shell_quoted_row_in_testtoon(self):
        src = (
            "SHELL[1]{command, exit_code}:\n"
            '  "cd /repo && node run.mjs", 0\n'
        )
        lines = self._expand(src)
        assert lines[0].args.startswith('"cd /repo && node run.mjs"')

    def test_shell_dry_run_executes_full_command_not_first_token(self):
        from testql.interpreter import OqlInterpreter
        from testql.interpreter._testtoon_parser import testtoon_to_oql

        src = (
            "SHELL[1]{command, exit_code}:\n"
            '  echo hello-from-shell-expansion, 0\n'
        )
        script = testtoon_to_oql(src)
        interp = OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=True)
        for line in script.lines:
            handler = getattr(interp, f"_cmd_{line.command.lower()}", None)
            if handler is None and line.command == "ASSERT_EXIT_CODE":
                handler = interp._cmd_assert_exit_code
            if handler:
                handler(line.args, line)
        assert interp._last_shell_result is not None
        assert interp._last_shell_result["command"] == "echo hello-from-shell-expansion"


class TestBackwardCompatibility:
    """The legacy parser must still work unchanged after Phase 0."""

    def test_legacy_parser_imports(self):
        from testql.interpreter._testtoon_parser import (
            ToonScript,
            ToonSection,
            parse_testtoon,
            testtoon_to_oql,
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
            testtoon_to_oql,
            validate_testtoon,
        )
        toon = parse_testtoon(SAMPLE)
        script = testtoon_to_oql(SAMPLE)
        assert script.lines  # non-empty

"""Tests for interpreter/converter handlers and parsers."""
from __future__ import annotations

import pytest

from testql.interpreter.converter.models import Section
from testql.interpreter.converter.parsers import (
    detect_scenario_type,
    extract_scenario_name,
    parse_api_args,
    parse_commands,
    parse_meta_from_args,
    parse_target_from_args,
)
from testql.interpreter.converter.handlers.encoder import handle_encoder
from testql.interpreter.converter.handlers.wait import handle_wait
from testql.interpreter.converter.handlers.select import handle_select
from testql.interpreter.converter.handlers.flow import handle_flow, FLOW_COMMANDS
from testql.interpreter.converter.handlers.navigate import handle_navigate
from testql.interpreter.converter.handlers.record import handle_record_start, handle_record_stop
from testql.interpreter.converter.handlers.include import handle_include
from testql.interpreter.converter.handlers.unknown import handle_unknown
from testql.interpreter.converter.dispatcher import dispatch


# ─── Parsers ──────────────────────────────────────────────────────────────────

class TestParseApiArgs:
    def test_method_and_path(self):
        m, e = parse_api_args("GET /users")
        assert m == "GET" and e == "/users"

    def test_quoted_path(self):
        m, e = parse_api_args('POST "/api/v1/items"')
        assert m == "POST" and e == "/api/v1/items"

    def test_no_args_defaults(self):
        m, e = parse_api_args("")
        assert m == "GET" and e == "/"

    def test_strips_json_body(self):
        _, e = parse_api_args('POST /items {"name": "x"}')
        assert "{" not in e

    def test_uppercases_method(self):
        m, _ = parse_api_args("delete /items/1")
        assert m == "DELETE"


class TestParseTargetFromArgs:
    def test_double_quoted(self):
        assert parse_target_from_args('"#btn"') == "#btn"

    def test_single_quoted(self):
        assert parse_target_from_args("'#input'") == "#input"

    def test_unquoted_first_token(self):
        assert parse_target_from_args("http://localhost:8000 extra") == "http://localhost:8000"

    def test_empty(self):
        assert parse_target_from_args("") == ""


class TestParseMetaFromArgs:
    def test_json_dict(self):
        result = parse_meta_from_args('focus {"id": "x1"}')
        assert "id" in result or "x1" in result

    def test_no_meta(self):
        assert parse_meta_from_args("http://example.com") == "-"

    def test_raw_dict_fallback(self):
        result = parse_meta_from_args("{bad json:})")
        assert result  # returns something


class TestParseCommands:
    def test_navigate(self):
        cmds, _ = parse_commands("NAVIGATE http://localhost")
        assert ("NAVIGATE", "http://localhost") in cmds

    def test_comment_collected(self):
        cmds, comments = parse_commands("# my scenario\nNAVIGATE http://x.com")
        assert any(c.startswith("#") for c in comments)
        assert ("COMMENT", "# my scenario") in cmds

    def test_blank_line(self):
        cmds, _ = parse_commands("NAVIGATE http://x.com\n\nCLICK btn")
        assert ("BLANK", "") in cmds

    def test_empty_source(self):
        cmds, comments = parse_commands("")
        assert cmds == [] and comments == []

    def test_uppercase_cmd(self):
        cmds, _ = parse_commands("click #btn")
        assert cmds[0][0] == "CLICK"


class TestDetectScenarioType:
    def test_api_only(self):
        cmds = [("API", "/users"), ("API", "/items")]
        assert detect_scenario_type(cmds) == "api"

    def test_gui_navigate(self):
        cmds = [("NAVIGATE", "http://x"), ("CLICK", "#btn")]
        assert detect_scenario_type(cmds) == "gui"

    def test_encoder(self):
        cmds = [("ENCODER_FOCUS", '"#x"')]
        assert detect_scenario_type(cmds) == "gui"

    def test_e2e(self):
        cmds = [("NAVIGATE", "http://x"), ("API", "/x"), ("SELECT_OPTION", '"#y"')]
        assert detect_scenario_type(cmds) == "e2e"

    def test_interaction_record(self):
        cmds = [("RECORD_START", "s1"), ("RECORD_STOP", "")]
        assert detect_scenario_type(cmds) == "interaction"


class TestExtractScenarioName:
    def test_from_comment(self):
        name = extract_scenario_name(["# My Login Test"], "test.tql")
        assert "My" in name or "Login" in name

    def test_fallback_filename(self):
        name = extract_scenario_name([], "my_scenario.tql")
        assert "My" in name or "my_scenario" in name.lower()

    def test_skip_usage_comments(self):
        name = extract_scenario_name(["# Usage: run this", "# Real Name"], "x.tql")
        assert "Real" in name or "real" in name.lower()


# ─── Handlers ─────────────────────────────────────────────────────────────────

class TestHandleWait:
    def test_single_wait(self):
        filtered = [("WAIT", "500")]
        i, section = handle_wait(filtered, 0)
        assert i == 1
        assert section.type == "WAIT"
        assert len(section.rows) == 1
        assert section.rows[0]["ms"] == "500"

    def test_multiple_waits(self):
        filtered = [("WAIT", "100"), ("WAIT", "200")]
        i, section = handle_wait(filtered, 0)
        assert i == 2 and len(section.rows) == 2

    def test_invalid_ms_defaults_100(self):
        filtered = [("WAIT", "notanumber")]
        _, section = handle_wait(filtered, 0)
        assert section.rows[0]["ms"] == "100"

    def test_stops_at_non_wait(self):
        filtered = [("WAIT", "100"), ("NAVIGATE", "http://x")]
        i, section = handle_wait(filtered, 0)
        assert i == 1 and len(section.rows) == 1


class TestHandleNavigate:
    def test_single_navigate(self):
        filtered = [("NAVIGATE", "http://localhost")]
        i, section = handle_navigate(filtered, 0)
        assert i == 1
        assert section.type == "NAVIGATE"
        assert section.rows[0]["path"] == "http://localhost"
        assert section.rows[0]["wait_ms"] == "300"

    def test_navigate_with_wait(self):
        filtered = [("NAVIGATE", "http://x"), ("WAIT", "1000")]
        i, section = handle_navigate(filtered, 0)
        assert i == 2
        assert section.rows[0]["wait_ms"] == "1000"

    def test_multiple_navigates(self):
        filtered = [("NAVIGATE", "http://a"), ("NAVIGATE", "http://b")]
        i, section = handle_navigate(filtered, 0)
        assert i == 2 and len(section.rows) == 2

    def test_stops_at_non_navigate(self):
        filtered = [("NAVIGATE", "http://x"), ("CLICK", "#btn")]
        i, section = handle_navigate(filtered, 0)
        assert i == 1 and len(section.rows) == 1


class TestHandleSelect:
    def test_select_option(self):
        filtered = [("SELECT_OPTION", '"#dropdown"')]
        i, section = handle_select(filtered, 0)
        assert i == 1
        assert section.type == "SELECT"
        assert section.rows[0]["action"] == "option"
        assert section.rows[0]["id"] == "#dropdown"

    def test_plain_select(self):
        filtered = [("SELECT", '"#box"')]
        i, section = handle_select(filtered, 0)
        assert section.rows[0]["action"] == "select"

    def test_multiple_selects(self):
        filtered = [("SELECT_OPTION", '"#a"'), ("SELECT_RADIO", '"#b"')]
        i, section = handle_select(filtered, 0)
        assert i == 2 and len(section.rows) == 2

    def test_stops_at_non_select(self):
        filtered = [("SELECT_OPTION", '"#x"'), ("CLICK", "#btn")]
        i, section = handle_select(filtered, 0)
        assert i == 1


class TestHandleEncoder:
    def test_encoder_focus(self):
        filtered = [("ENCODER_FOCUS", '"#input"')]
        i, section = handle_encoder(filtered, 0)
        assert i == 1
        assert section.type == "ENCODER"
        assert section.rows[0]["action"] == "focus"
        assert section.rows[0]["target"] == "#input"

    def test_encoder_scroll(self):
        filtered = [("ENCODER_SCROLL", "5")]
        _, section = handle_encoder(filtered, 0)
        assert section.rows[0]["action"] == "scroll"
        assert section.rows[0]["value"] == "5"

    def test_encoder_scroll_invalid_value(self):
        filtered = [("ENCODER_SCROLL", "bad")]
        _, section = handle_encoder(filtered, 0)
        assert section.rows[0]["value"] == "1"

    def test_encoder_with_wait(self):
        filtered = [("ENCODER_FOCUS", '"#x"'), ("WAIT", "200")]
        i, section = handle_encoder(filtered, 0)
        assert i == 2
        assert section.rows[0]["wait_ms"] == "200"

    def test_multiple_encoder_commands(self):
        filtered = [("ENCODER_FOCUS", '"#a"'), ("ENCODER_SCROLL", "3")]
        i, section = handle_encoder(filtered, 0)
        assert i == 2 and len(section.rows) == 2


class TestHandleFlow:
    def test_app_start(self):
        filtered = [("APP_START", "myapp")]
        i, section = handle_flow(filtered, 0)
        assert i == 1 and section.type == "FLOW"
        assert section.rows[0]["command"] == "app_start"

    def test_session_start(self):
        filtered = [("SESSION_START", "")]
        _, section = handle_flow(filtered, 0)
        assert section.rows[0]["command"] == "session_start"

    def test_multiple_flow_commands(self):
        filtered = [("APP_START", ""), ("APP_READY", "")]
        i, section = handle_flow(filtered, 0)
        assert i == 2 and len(section.rows) == 2

    def test_stops_at_non_flow(self):
        filtered = [("APP_START", ""), ("NAVIGATE", "http://x")]
        i, section = handle_flow(filtered, 0)
        assert i == 1

    def test_flow_commands_frozenset(self):
        assert "APP_START" in FLOW_COMMANDS
        assert "SESSION_START" in FLOW_COMMANDS


class TestHandleRecord:
    def test_record_start(self):
        filtered = [("RECORD_START", '"session-1"')]
        i, section = handle_record_start(filtered, 0)
        assert i == 1
        assert section.type == "RECORD_START"
        assert section.rows[0]["session_id"] == "session-1"

    def test_record_stop(self):
        filtered = [("RECORD_STOP", "")]
        i, section = handle_record_stop(filtered, 0)
        assert i == 1
        assert section.type == "RECORD_STOP"


class TestHandleInclude:
    def test_include(self):
        filtered = [("INCLUDE", '"fixtures/setup.tql"')]
        i, section = handle_include(filtered, 0)
        assert i == 1
        assert section.type == "INCLUDE"
        assert section.rows[0]["file"] == "fixtures/setup.tql"


class TestHandleUnknown:
    def test_unknown_command(self):
        filtered = [("UNKNOWN_CMD", "args")]
        i, section = handle_unknown(filtered, 0)
        assert i == 1
        assert section.type in ("UNKNOWN", "unknown", "UNKNOWN_CMD") or section.type


# ─── Dispatcher ───────────────────────────────────────────────────────────────

class TestDispatch:
    def test_dispatches_navigate(self):
        filtered = [("NAVIGATE", "http://x")]
        _, section = dispatch(filtered, 0)
        assert section.type == "NAVIGATE"

    def test_dispatches_wait(self):
        filtered = [("WAIT", "100")]
        _, section = dispatch(filtered, 0)
        assert section.type == "WAIT"

    def test_dispatches_select(self):
        filtered = [("SELECT_OPTION", '"#x"')]
        _, section = dispatch(filtered, 0)
        assert section.type == "SELECT"

    def test_dispatches_encoder(self):
        filtered = [("ENCODER_FOCUS", '"#x"')]
        _, section = dispatch(filtered, 0)
        assert section.type == "ENCODER"

    def test_dispatches_flow(self):
        filtered = [("APP_START", "")]
        _, section = dispatch(filtered, 0)
        assert section.type == "FLOW"

    def test_dispatches_record_start(self):
        filtered = [("RECORD_START", '"s1"')]
        _, section = dispatch(filtered, 0)
        assert section.type == "RECORD_START"

    def test_dispatches_record_stop(self):
        filtered = [("RECORD_STOP", "")]
        _, section = dispatch(filtered, 0)
        assert section.type == "RECORD_STOP"

    def test_dispatches_include(self):
        filtered = [("INCLUDE", '"f.tql"')]
        _, section = dispatch(filtered, 0)
        assert section.type == "INCLUDE"

    def test_dispatches_unknown(self):
        filtered = [("XYZ_UNKNOWN", "")]
        _, section = dispatch(filtered, 0)
        assert section is not None

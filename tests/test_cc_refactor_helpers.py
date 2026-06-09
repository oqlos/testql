"""Regression tests for CC refactor helpers."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [
    str(_ROOT / "packages/dsl2testql/src"),
    str(_ROOT / "packages/uri2testql/src"),
    str(_ROOT / "packages/cli2testql/src"),
]

import pytest

from testql.context.runtime import RuntimeProfile, _coerce_profile_dict
from testql.interpreter._gui_expand import expand_gui_row, quote_gui_token
from testql.interpreter._parser import OqlLine
from testql.nlp2env.scenarios import _index_expects, _index_prompt_fields, _prompt_id_column


def test_quote_gui_token_preserves_interpolation() -> None:
    assert quote_gui_token("${target_url}") == "${target_url}"
    assert quote_gui_token("button") == '"button"'


def test_expand_gui_row_emits_start_and_input() -> None:
    lines: list[OqlLine] = []
    line_num = 1

    def append(target_lines: list[OqlLine], num: int, command: str, args: str = "") -> int:
        raw = command if not args else f"{command} {args}"
        target_lines.append(OqlLine(number=num, command=command, args=args, raw=raw))
        return num + 1

    row = {"action": "navigate", "selector": "-", "value": "https://example.com", "wait_ms": 100}
    line_num, session_open = expand_gui_row(
        row,
        lines=lines,
        line_num=line_num,
        session_open=False,
        append=append,
    )
    assert session_open is True
    assert lines[0].command == "GUI_START"
    assert lines[-1].command == "WAIT"


def test_scenario_index_helpers() -> None:
    fields = _index_prompt_fields(
        {"rows": [{"prompt_id": "a", "key": "host", "value": "smtp.example.com"}]},
    )
    expects = _index_expects(
        {"rows": [{"prompt_id": "a", "expect": "SMTP_HOST=smtp.example.com"}]},
    )
    assert fields["a"]["host"] == "smtp.example.com"
    assert expects["a"] == ["SMTP_HOST=smtp.example.com"]
    assert _prompt_id_column(["id", "lang"]) == "id"


def test_coerce_profile_dict_accepts_dotted_keys() -> None:
    profile = _coerce_profile_dict(
        {
            "os": "linux",
            "browser.engine": "firefox",
            "browser.headless": "false",
            "runtime.source": "nlp2cmd",
            "capabilities": "api,gui",
        },
    )
    assert isinstance(profile, RuntimeProfile)
    assert profile.os_family == "linux"
    assert profile.browser_engine == "firefox"
    assert profile.browser_headless is False
    assert profile.capabilities == ["api", "gui"]


def test_dsl2testql_grammar_parse_line() -> None:
    pytest.importorskip("google.protobuf")
    from dsl2testql.grammar import parse_line

    assert parse_line('QUERY app FILE app.testql.less FORMAT json') == {
        "verb": "QUERY",
        "target": "app",
        "file": "app.testql.less",
        "format": "json",
    }


def test_dsl2testql_envelope_roundtrip() -> None:
    pytest.importorskip("google.protobuf")
    from dsl2testql.grammar import parse_line
    from dsl2testql.pb_codec import decode_protobuf, encode_protobuf

    cmd = parse_line('PATCH entity/user WITH patch/user.less FILE app.testql.less')
    assert cmd is not None
    payload = encode_protobuf(cmd)
    restored = decode_protobuf(payload)
    assert restored["verb"] == "PATCH"
    assert restored["target"] == "entity/user"
    assert restored["with_path"] == "patch/user.less"
    assert restored["file"] == "app.testql.less"


def test_uri_block_resolver_app_selector() -> None:
    from uri2testql.block_resolver import parse_block_ref, selector_from_ref

    ref = parse_block_ref(["app"])
    assert selector_from_ref(ref) == "app"


def test_expand_gui_row_click_and_stop() -> None:
    lines: list[OqlLine] = []
    line_num = 1

    def append(target_lines: list[OqlLine], num: int, command: str, args: str = "") -> int:
        raw = command if not args else f"{command} {args}"
        target_lines.append(OqlLine(number=num, command=command, args=args, raw=raw))
        return num + 1

    line_num, session_open = expand_gui_row(
        {"action": "click", "selector": "button[type='submit']", "value": "-"},
        lines=lines,
        line_num=line_num,
        session_open=True,
        append=append,
    )
    assert session_open is True
    assert lines[-1].command == "GUI_CLICK"

    line_num, session_open = expand_gui_row(
        {"action": "close", "selector": "-", "value": "-"},
        lines=lines,
        line_num=line_num,
        session_open=True,
        append=append,
    )
    assert session_open is False
    assert lines[-1].command == "GUI_STOP"


def test_cli2testql_cmd_exec_line_reports_failure(capsys) -> None:
    pytest.importorskip("google.protobuf")
    import argparse

    from cli2testql.cli_handlers import cmd_exec_line

    args = argparse.Namespace(command="QUERY missing://block/app", file=None, json=False)
    assert cmd_exec_line(args) == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err or captured.out == ""

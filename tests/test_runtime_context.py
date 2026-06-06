"""Tests for runtime environment profiles and TestTOON expansion."""

from __future__ import annotations

from testql.context.runtime import RuntimeProfile, apply_profile, detect_runtime_profile, profile_to_variables
from testql.export.scenario_builder import ScenarioBuilder
from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import parse_oql
from testql.interpreter._testtoon_parser import testtoon_to_oql as expand_testtoon


def test_detect_runtime_profile_has_browser_or_api() -> None:
    profile = detect_runtime_profile(app_type="web", source_runtime="test")
    assert profile.os_family
    assert "api" in profile.capabilities


def test_profile_to_variables_flattens_browser_keys() -> None:
    profile = RuntimeProfile(browser_engine="firefox", app_type="canvas", source_runtime="nlp2cmd")
    vars_map = profile_to_variables(profile)
    assert vars_map["browser.engine"] == "firefox"
    assert vars_map["runtime.source"] == "nlp2cmd"


def test_environment_section_expands_to_context_apply() -> None:
    source = """# SCENARIO: env-smoke
# TYPE: e2e

ENVIRONMENT[3]{key, value}:
  os, linux
  browser.engine, chromium
  runtime.source, nlp2cmd

CONTEXT[1]{key, value}:
  task, login

COMMANDS[1]{command}:
  LOG "ok"
"""
    script = expand_testtoon(source, "env-smoke.testql.toon.yaml")
    commands = [line.command for line in script.lines]
    assert "SET" in commands
    assert "CONTEXT_APPLY" in commands
    assert "LOG" in commands


def test_gui_section_expands_to_gui_commands() -> None:
    source = """# SCENARIO: gui-login
# TYPE: gui

CONFIG[2]{key, value}:
  target_url, https://example.com
  username, demo

GUI[3]{action, selector, value, wait_ms}:
  navigate, -, ${target_url}, 1000
  input, #user, ${username}, -
  click, button[type='submit'], -, 500
"""
    script = expand_testtoon(source, "gui-login.testql.toon.yaml")
    commands = [line.command for line in script.lines]
    assert "GUI_START" in commands
    assert "GUI_INPUT" in commands
    assert "GUI_CLICK" in commands
    assert "GUI_STOP" in commands


def test_context_detect_command_sets_variables() -> None:
    interp = OqlInterpreter(quiet=True, dry_run=True)
    parsed = parse_oql('CONTEXT_DETECT app=web source=test\nLOG "done"', "<test>")
    result = interp.execute(parsed)
    assert result.ok
    assert interp.vars.get("runtime.source") == "test"
    assert interp.vars.get("app.type") == "web"


def test_scenario_builder_roundtrip_parseable() -> None:
    text = (
        ScenarioBuilder(name="builder-smoke", scenario_type="gui")
        .environment({"os": "linux", "browser.engine": "chromium"})
        .config({"target_url": "https://example.com"})
        .gui([{"action": "click", "selector": "button", "value": "-", "wait_ms": 200}])
        .build()
    )
    script = expand_testtoon(text, "builder-smoke.testql.toon.yaml")
    assert any(line.command == "GUI_CLICK" for line in script.lines)

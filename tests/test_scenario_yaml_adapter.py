"""Tests for the new declarative `*.testql.yaml` ScenarioYamlAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters import ScenarioYamlAdapter, registry
from testql.adapters.scenario_yaml import parse, render
from testql.ir import (
    ApiStep,
    EncoderStep,
    GuiStep,
    ShellStep,
    UnitStep,
)


SAMPLE_API = """\
scenario: API Health Check
type: api
version: 2

targets:
  api:
    base_url: http://localhost:8101
    timeout_ms: 5000

steps:
  - request: GET /api/health
    expect:
      status: 200
  - request:
      method: POST
      path: /api/v3/scenarios
    expect:
      status: 201
    capture:
      scenario_id: response.data.id
"""


SAMPLE_GUI = """\
scenario: Login Form
type: gui

targets:
  browser:
    base_url: https://example.com

vars:
  username: testuser

steps:
  - open: ${browser.base_url}/login
  - input: "#username"
    value: ${username}
  - click: "button[type='submit']"
  - expect:
      visible: "[data-testid='dashboard']"
"""


SAMPLE_MIXED = """\
scenario: Cross-environment smoke
type: mixed

steps:
  - run: echo Hello TestQL
    expect:
      exit_code: 0
  - request: GET /api/health
    using: api
    expect:
      status: 200
  - encoder:
      action: focus
      target: column1
  - unit: tests/test_math.py::test_basic
"""


class TestDetect:
    def test_detect_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "smoke.testql.yaml"
        path.write_text(SAMPLE_API, encoding="utf-8")
        result = ScenarioYamlAdapter().detect(path)
        assert result.matches
        assert result.confidence >= 0.9

    def test_detect_content(self) -> None:
        result = ScenarioYamlAdapter().detect(SAMPLE_API)
        assert result.matches

    def test_detect_negative(self) -> None:
        result = ScenarioYamlAdapter().detect("just text")
        assert not result.matches


class TestParseApi:
    def test_metadata(self) -> None:
        plan = parse(SAMPLE_API)
        assert plan.metadata.name == "API Health Check"
        assert plan.metadata.type == "api"
        assert plan.metadata.version == "2"

    def test_targets_become_config(self) -> None:
        plan = parse(SAMPLE_API)
        assert plan.config.get("api.base_url") == "http://localhost:8101"
        assert plan.config.get("base_url") == "http://localhost:8101"

    def test_steps_typed(self) -> None:
        plan = parse(SAMPLE_API)
        api = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert len(api) == 2
        assert api[0].method == "GET"
        assert api[0].path == "/api/health"
        assert api[0].expect_status == 200
        assert api[1].method == "POST"
        assert api[1].path == "/api/v3/scenarios"
        assert api[1].expect_status == 201

    def test_capture(self) -> None:
        plan = parse(SAMPLE_API)
        api = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert api[1].captures
        capture = api[1].captures[0]
        assert capture.var_name == "scenario_id"
        assert capture.from_path == "data.id"


class TestParseGui:
    def test_navigate_and_form(self) -> None:
        plan = parse(SAMPLE_GUI)
        gui_steps = [s for s in plan.steps if isinstance(s, GuiStep)]
        actions = [s.action for s in gui_steps]
        assert "navigate" in actions
        assert "input" in actions
        assert "click" in actions
        assert "assert_visible" in actions


class TestParseMixed:
    def test_step_kinds(self) -> None:
        plan = parse(SAMPLE_MIXED)
        kinds = [step.kind for step in plan.steps]
        assert kinds == ["shell", "api", "encoder", "unit"]

    def test_using_overrides_propagate(self) -> None:
        plan = parse(SAMPLE_MIXED)
        api = next(s for s in plan.steps if isinstance(s, ApiStep))
        assert api.extra.get("using") == "api"

    def test_shell_expect_exit_code(self) -> None:
        plan = parse(SAMPLE_MIXED)
        shell = next(s for s in plan.steps if isinstance(s, ShellStep))
        assert shell.expect_exit_code == 0

    def test_encoder_target(self) -> None:
        plan = parse(SAMPLE_MIXED)
        encoder = next(s for s in plan.steps if isinstance(s, EncoderStep))
        assert encoder.action == "focus"
        assert encoder.target == "column1"

    def test_unit_target(self) -> None:
        plan = parse(SAMPLE_MIXED)
        unit = next(s for s in plan.steps if isinstance(s, UnitStep))
        assert unit.target == "tests/test_math.py::test_basic"


class TestRender:
    def test_round_trip_metadata_steps(self) -> None:
        plan = parse(SAMPLE_API)
        rendered = render(plan)
        plan2 = parse(rendered)
        assert plan.metadata.name == plan2.metadata.name
        assert plan.metadata.type == plan2.metadata.type
        kinds1 = [s.kind for s in plan.steps]
        kinds2 = [s.kind for s in plan2.steps]
        assert kinds1 == kinds2


class TestRegistration:
    def test_registered_in_default_registry(self) -> None:
        adapter = registry.get("scenario_yaml")
        assert isinstance(adapter, ScenarioYamlAdapter)

    def test_extension_lookup_picks_scenario_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "scenario.testql.yaml"
        path.write_text(SAMPLE_API, encoding="utf-8")
        adapter = registry.by_extension(path)
        assert adapter is not None
        assert adapter.name == "scenario_yaml"

    def test_extension_lookup_keeps_testtoon(self, tmp_path: Path) -> None:
        path = tmp_path / "scenario.testql.toon.yaml"
        path.write_text("# SCENARIO: x\n# TYPE: api\n", encoding="utf-8")
        adapter = registry.by_extension(path)
        assert adapter is not None
        assert adapter.name == "testtoon"


class TestParseErrors:
    def test_non_mapping_root(self) -> None:
        with pytest.raises(ValueError):
            parse("- just\n- a list\n")

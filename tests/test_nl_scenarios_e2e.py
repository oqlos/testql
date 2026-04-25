"""End-to-end tests for the bundled `*.nl.md` scenarios.

These scenarios are committed under `testql-scenarios/nl/` and act as the
"contract" for the NL adapter — every step must resolve to a typed IR step
(no `NlStep` fallthroughs).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.nl import NLDSLAdapter
from testql.ir import (
    ApiStep,
    EncoderStep,
    GuiStep,
    NlStep,
    Step,
    TestPlan,
)


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "testql-scenarios" / "nl"


def _scenario_files() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.nl.md"))


@pytest.fixture(params=_scenario_files(), ids=lambda p: p.name)
def scenario(request) -> Path:
    return request.param


class TestScenarioFilesParse:
    def test_scenario_dir_not_empty(self):
        assert _scenario_files(), "no .nl.md scenarios found in testql-scenarios/nl/"

    def test_parse_succeeds(self, scenario: Path):
        plan = NLDSLAdapter().parse(scenario)
        assert isinstance(plan, TestPlan)
        assert plan.metadata.name, f"scenario {scenario.name} has no name"
        assert plan.steps, f"scenario {scenario.name} has zero steps"

    def test_no_unresolved_nl_steps(self, scenario: Path):
        plan = NLDSLAdapter().parse(scenario)
        unresolved = [s for s in plan.steps if isinstance(s, NlStep)]
        assert not unresolved, (
            f"scenario {scenario.name} has unresolved NL steps: "
            f"{[u.text for u in unresolved]}"
        )

    def test_round_trip_preserves_step_count(self, scenario: Path):
        adapter = NLDSLAdapter()
        plan1 = adapter.parse(scenario)
        rendered = adapter.render(plan1)
        plan2 = adapter.parse(rendered)
        assert len(plan1.steps) == len(plan2.steps), (
            f"round-trip changed step count for {scenario.name}"
        )


class TestSpecificScenarios:
    def test_login_pl(self):
        plan = NLDSLAdapter().parse(SCENARIO_DIR / "login.nl.md")
        assert plan.metadata.lang == "pl"
        assert plan.metadata.type == "gui"
        # First step is navigate to /login
        assert isinstance(plan.steps[0], GuiStep)
        assert plan.steps[0].path == "/login"

    def test_api_smoke_pl(self):
        plan = NLDSLAdapter().parse(SCENARIO_DIR / "api-smoke.nl.md")
        api_steps = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert len(api_steps) == 3
        methods = [s.method for s in api_steps]
        assert "GET" in methods and "POST" in methods

    def test_encoder_flow_pl(self):
        plan = NLDSLAdapter().parse(SCENARIO_DIR / "encoder-flow.nl.md")
        encoder_steps = [s for s in plan.steps if isinstance(s, EncoderStep)]
        actions = {s.action for s in encoder_steps}
        assert {"on", "click", "off"} <= actions

    def test_login_en(self):
        plan = NLDSLAdapter().parse(SCENARIO_DIR / "login-en.nl.md")
        assert plan.metadata.lang == "en"
        assert isinstance(plan.steps[0], GuiStep)
        assert plan.steps[0].action == "navigate"

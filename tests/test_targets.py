"""Tests for `testql.generators.targets.*`."""

from __future__ import annotations

import pytest

from testql.generators.targets import (
    BaseTarget,
    NLTarget,
    PytestTarget,
    TestToonTarget,
    available_targets,
    get_target,
)
from testql.ir import ApiStep, Assertion, GuiStep, ScenarioMetadata, SqlStep, TestPlan


def _sample_plan() -> TestPlan:
    return TestPlan(
        metadata=ScenarioMetadata(name="Sample", type="api", lang="en"),
        steps=[
            ApiStep(method="GET", path="/health", expect_status=200,
                    asserts=[Assertion(field="status", op="==", expected=200)],
                    name="getHealth"),
            ApiStep(method="POST", path="/items", expect_status=201, name="createItem"),
        ],
    )


class TestRegistry:
    def test_three_builtin_targets(self):
        assert set(available_targets()) == {"testtoon", "nl", "pytest"}

    @pytest.mark.parametrize("name", ["testtoon", "nl", "pytest"])
    def test_get(self, name):
        t = get_target(name)
        assert isinstance(t, BaseTarget)
        assert t.name == name

    def test_get_unknown(self):
        assert get_target("nope") is None


class TestTestToonTarget:
    def test_extension(self):
        assert TestToonTarget().file_extension == ".testql.toon.yaml"

    def test_render_includes_meta(self):
        out = TestToonTarget().render(_sample_plan())
        assert "# SCENARIO: Sample" in out
        assert "# TYPE: api" in out
        assert "API[2]" in out


class TestNLTarget:
    def test_extension(self):
        assert NLTarget().file_extension == ".nl.md"

    def test_render(self):
        out = NLTarget().render(_sample_plan())
        # English: "Send GET ..." / "Send POST ..."
        assert "Send GET" in out
        assert "Send POST" in out


class TestPytestTarget:
    def test_extension(self):
        assert PytestTarget().file_extension == ".py"

    def test_emits_one_test_per_step(self):
        out = PytestTarget().render(_sample_plan())
        assert out.count("def test_") == 2

    def test_safe_idents(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/x", name="weird name with spaces!")])
        out = PytestTarget().render(plan)
        assert "def test_weird_name_with_spaces" in out

    def test_summary_in_docstring(self):
        out = PytestTarget().render(_sample_plan())
        assert "GET /health" in out

    def test_handles_unnamed_steps(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/x")])
        out = PytestTarget().render(plan)
        assert "def test_api" in out  # the kind-derived default

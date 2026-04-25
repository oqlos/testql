"""Tests for `testql.meta.confidence_scorer`."""

from __future__ import annotations

from testql.ir import ApiStep, Assertion, NlStep, ScenarioMetadata, Step, TestPlan
from testql.meta.confidence_scorer import (
    PlanConfidence,
    StepConfidence,
    score_plan,
)


class TestPlanConfidence:
    def test_empty_plan_zero(self):
        result = score_plan(TestPlan())
        assert isinstance(result, PlanConfidence)
        assert result.plan_score == 0.0
        assert result.step_scores == []

    def test_strong_step_high_score(self):
        plan = TestPlan(steps=[
            ApiStep(method="GET", path="/a", name="a",
                    asserts=[Assertion(field="status", expected=200)]),
        ])
        result = score_plan(plan)
        # baseline 0.5 + assertion 0.3 + typed 0.2 = 1.0
        assert result.plan_score >= 0.95

    def test_step_without_asserts_lower(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/a", name="a")])
        result = score_plan(plan)
        # baseline 0.5 + typed 0.2 = 0.7
        assert 0.65 <= result.plan_score <= 0.75

    def test_nl_unresolved_lower(self):
        plan = TestPlan(steps=[NlStep(text="Foozle bar", name="nl-unresolved")])
        result = score_plan(plan)
        # baseline 0.5 only → 0.5
        assert result.plan_score == 0.5

    def test_nl_llm_resolved_lowest(self):
        plan = TestPlan(steps=[NlStep(text="Foozle bar", name="nl-llm[navigate]")])
        result = score_plan(plan)
        # baseline 0.5 - 0.3 (LLM) = 0.2
        assert result.plan_score == 0.2

    def test_multi_assert_bonus(self):
        plan = TestPlan(steps=[
            ApiStep(method="GET", path="/a", name="a",
                    asserts=[
                        Assertion(field="status", expected=200),
                        Assertion(field="data.x", expected=1),
                    ]),
        ])
        result = score_plan(plan)
        # 0.5 + 0.3 + 0.1 (multi) + 0.2 (typed) = 1.1 → clamped to 1.0
        assert result.plan_score == 1.0

    def test_per_step_scores_recorded(self):
        plan = TestPlan(steps=[
            ApiStep(method="GET", path="/a", name="strong",
                    asserts=[Assertion(field="status", expected=200)]),
            ApiStep(method="POST", path="/b", name="weak"),
        ])
        result = score_plan(plan)
        assert len(result.step_scores) == 2
        names = [s.name for s in result.step_scores]
        assert "strong" in names and "weak" in names

    def test_clamping(self):
        sc = StepConfidence(name="x", kind="api", score=1.5)
        assert sc.to_dict()["score"] == 1.5  # to_dict preserves what was set

    def test_to_dict(self):
        plan = TestPlan(steps=[
            ApiStep(method="GET", path="/a", name="a",
                    asserts=[Assertion(field="status", expected=200)]),
        ])
        d = score_plan(plan).to_dict()
        assert "plan_score" in d
        assert d["step_scores"][0]["name"] == "a"
        assert "reasons" in d["step_scores"][0]


class TestStepReasons:
    def test_reasons_explain_score(self):
        plan = TestPlan(steps=[ApiStep(method="GET", path="/a", name="a")])
        result = score_plan(plan)
        reasons = result.step_scores[0].reasons
        assert any("baseline" in r for r in reasons)
        assert any("typed" in r.lower() for r in reasons)

    def test_llm_reason(self):
        plan = TestPlan(steps=[NlStep(text="x", name="nl-llm[navigate]")])
        result = score_plan(plan)
        assert any("LLM" in r for r in result.step_scores[0].reasons)

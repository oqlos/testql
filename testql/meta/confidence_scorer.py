"""Per-step + plan-level confidence scoring for generated tests.

Each step is rated 0.0 — 1.0:

    +0.5 baseline (the step is in the plan at all)
    +0.3 when the step has at least one assertion
    +0.2 when the step is a typed IR node (not an unresolved NL fallback)
    -0.3 when the step's name marks it as LLM-resolved (`nl-llm[…]`)
    +0.1 when the step has multiple assertions (extra guard rails)

The plan score is the arithmetic mean of step scores. Both numbers are clamped
to [0.0, 1.0].
"""

from __future__ import annotations

from dataclasses import dataclass, field

from testql.ir import NlStep, Step, TestPlan


@dataclass
class StepConfidence:
    name: str
    kind: str
    score: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "score": round(self.score, 3),
            "reasons": list(self.reasons),
        }


@dataclass
class PlanConfidence:
    plan_score: float = 0.0
    step_scores: list[StepConfidence] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plan_score": round(self.plan_score, 3),
            "step_scores": [s.to_dict() for s in self.step_scores],
        }


def _is_llm_resolved(step: Step) -> bool:
    return isinstance(step, NlStep) and "llm" in (step.name or "")


def _score_assertions(step: Step) -> tuple[float, list[str]]:
    if not step.asserts:
        return 0.0, []
    reasons = [f"has {len(step.asserts)} assertion(s)"]
    bonus = 0.3 + (0.1 if len(step.asserts) > 1 else 0.0)
    return bonus, reasons


def _score_typed(step: Step) -> tuple[float, list[str]]:
    if isinstance(step, NlStep):
        return 0.0, []
    return 0.2, ["deterministic typed step"]


def _score_step(step: Step) -> StepConfidence:
    name = step.name or step.kind
    score = 0.5
    reasons = ["baseline"]
    if _is_llm_resolved(step):
        score -= 0.3
        reasons.append("LLM-resolved (lower confidence)")
    a_bonus, a_reasons = _score_assertions(step)
    score += a_bonus
    reasons.extend(a_reasons)
    t_bonus, t_reasons = _score_typed(step)
    score += t_bonus
    reasons.extend(t_reasons)
    return StepConfidence(name=name, kind=step.kind,
                          score=max(0.0, min(1.0, score)), reasons=reasons)


def score_plan(plan: TestPlan) -> PlanConfidence:
    """Return the per-step + aggregate confidence for `plan`."""
    step_scores = [_score_step(s) for s in plan.steps]
    if not step_scores:
        return PlanConfidence(plan_score=0.0, step_scores=[])
    plan_score = sum(s.score for s in step_scores) / len(step_scores)
    return PlanConfidence(plan_score=plan_score, step_scores=step_scores)


__all__ = ["StepConfidence", "PlanConfidence", "score_plan"]

"""Deterministic IR-level mutations for `TestPlan` mutation testing.

Each mutator returns the *full list* of mutations applicable to a plan; the
caller can then run each mutated plan through an executor to check whether
mutations are killed (i.e. the test still fails when the contract is broken).

All mutators are pure: they deep-copy the plan and return new instances.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Callable, Optional

from testql.ir import ApiStep, Assertion, Step, TestPlan


@dataclass
class Mutation:
    """One mutated plan plus a description of what changed."""

    kind: str
    description: str
    plan: TestPlan
    target: Optional[str] = None  # step name / path being mutated

    def to_dict(self) -> dict:
        return {"kind": self.kind, "description": self.description, "target": self.target}


# ── Operator flips ──────────────────────────────────────────────────────────


_OP_FLIPS: dict[str, str] = {
    "==": "!=", "!=": "==",
    ">": "<=", "<": ">=",
    ">=": "<", "<=": ">",
    "contains": "!=",
}


def _flipped_op(op: str) -> Optional[str]:
    return _OP_FLIPS.get(op)


def mutations_flip_assertion_op(plan: TestPlan) -> list[Mutation]:
    """Flip every assertion's operator (`==` → `!=`, `>` → `<=`, …)."""
    out: list[Mutation] = []
    for step_idx, step in enumerate(plan.steps):
        for a_idx, assertion in enumerate(step.asserts):
            new_op = _flipped_op(assertion.op)
            if new_op is None:
                continue
            mutated = copy.deepcopy(plan)
            mutated.steps[step_idx].asserts[a_idx].op = new_op
            out.append(Mutation(
                kind="flip_op",
                description=f"{step.name or step.kind}.assert[{a_idx}]: {assertion.op} → {new_op}",
                plan=mutated, target=step.name,
            ))
    return out


# ── Status tweaks ──────────────────────────────────────────────────────────


def _next_status(status: int) -> int:
    return status + 1 if status < 599 else status - 1


def _tweak_status_mutation(plan: TestPlan, step_idx: int, step: ApiStep) -> Mutation:
    new_status = _next_status(step.expect_status)  # type: ignore[arg-type]
    mutated = copy.deepcopy(plan)
    mutated.steps[step_idx].expect_status = new_status
    for a in mutated.steps[step_idx].asserts:
        if a.field == "status":
            a.expected = new_status
    return Mutation(
        kind="tweak_status",
        description=f"{step.name or 'api'}: status {step.expect_status} → {new_status}",
        plan=mutated, target=step.name,
    )


def mutations_tweak_status(plan: TestPlan) -> list[Mutation]:
    """Bump every `expect_status` on `ApiStep`s by one."""
    out: list[Mutation] = []
    for step_idx, step in enumerate(plan.steps):
        if isinstance(step, ApiStep) and step.expect_status is not None:
            out.append(_tweak_status_mutation(plan, step_idx, step))
    return out


# ── Step removals ──────────────────────────────────────────────────────────


def mutations_remove_step(plan: TestPlan) -> list[Mutation]:
    """Remove each step in turn."""
    out: list[Mutation] = []
    for step_idx, step in enumerate(plan.steps):
        mutated = copy.deepcopy(plan)
        del mutated.steps[step_idx]
        out.append(Mutation(
            kind="remove_step",
            description=f"removed {step.kind} step {step.name!r}",
            plan=mutated, target=step.name,
        ))
    return out


# ── Value scrambles ────────────────────────────────────────────────────────


def _scrambled(value: object) -> object:
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if isinstance(value, float):
        return value + 1.0
    if isinstance(value, str):
        return value + "_mutated"
    return value


def mutations_scramble_assertion_value(plan: TestPlan) -> list[Mutation]:
    """Perturb each non-status assertion's `expected` value."""
    out: list[Mutation] = []
    for step_idx, step in enumerate(plan.steps):
        for a_idx, assertion in enumerate(step.asserts):
            if assertion.field == "status":
                continue
            new_value = _scrambled(assertion.expected)
            if new_value == assertion.expected:
                continue
            mutated = copy.deepcopy(plan)
            mutated.steps[step_idx].asserts[a_idx].expected = new_value
            out.append(Mutation(
                kind="scramble_value",
                description=f"{step.name or step.kind}.assert[{a_idx}].expected: "
                            f"{assertion.expected!r} → {new_value!r}",
                plan=mutated, target=step.name,
            ))
    return out


# ── Aggregator ─────────────────────────────────────────────────────────────


_ALL_MUTATORS: tuple[Callable[[TestPlan], list[Mutation]], ...] = (
    mutations_flip_assertion_op,
    mutations_tweak_status,
    mutations_remove_step,
    mutations_scramble_assertion_value,
)


def mutate(plan: TestPlan) -> list[Mutation]:
    """Return every mutation produced by every built-in mutator."""
    out: list[Mutation] = []
    for fn in _ALL_MUTATORS:
        out.extend(fn(plan))
    return out


# ── Mutation-test harness ──────────────────────────────────────────────────


@dataclass
class MutationReport:
    total: int = 0
    killed: int = 0
    survivors: list[Mutation] = None  # type: ignore[assignment]

    @property
    def killed_ratio(self) -> float:
        return self.killed / self.total if self.total else 1.0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "killed": self.killed,
            "killed_ratio": self.killed_ratio,
            "survivors": [m.to_dict() for m in (self.survivors or [])],
        }


def run_mutation_test(
    plan: TestPlan,
    executor: Callable[[TestPlan], bool],
) -> MutationReport:
    """Run `executor(plan)` for the original and each mutation.

    A mutation is "killed" iff `executor(mutated)` returns False (i.e. the
    contract-break is detected). Plans where the *original* fails return an
    empty report — testing weakness can't be assessed without a green baseline.
    """
    if not executor(plan):
        return MutationReport(total=0, killed=0, survivors=[])
    mutations = mutate(plan)
    survivors = [m for m in mutations if executor(m.plan)]
    return MutationReport(
        total=len(mutations),
        killed=len(mutations) - len(survivors),
        survivors=survivors,
    )


__all__ = [
    "Mutation",
    "MutationReport",
    "mutate",
    "mutations_flip_assertion_op",
    "mutations_tweak_status",
    "mutations_remove_step",
    "mutations_scramble_assertion_value",
    "run_mutation_test",
]

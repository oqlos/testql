"""Tests for `testql.meta.mutator`."""

from __future__ import annotations

from testql.ir import (
    ApiStep,
    Assertion,
    GuiStep,
    ScenarioMetadata,
    Step,
    TestPlan,
)
from testql.meta.mutator import (
    Mutation,
    MutationReport,
    mutate,
    mutations_flip_assertion_op,
    mutations_remove_step,
    mutations_scramble_assertion_value,
    mutations_tweak_status,
    run_mutation_test,
)


def _sample_plan() -> TestPlan:
    return TestPlan(
        metadata=ScenarioMetadata(name="x", type="api"),
        steps=[
            ApiStep(
                method="GET", path="/health", expect_status=200,
                asserts=[Assertion(field="status", op="==", expected=200)],
                name="getHealth",
            ),
            ApiStep(
                method="POST", path="/items", expect_status=201,
                asserts=[
                    Assertion(field="status", op="==", expected=201),
                    Assertion(field="data.id", op="==", expected=42),
                ],
                name="createItem",
            ),
        ],
    )


# ── Operator flips ──────────────────────────────────────────────────────────


class TestFlipOp:
    def test_flips_eq_to_ne(self):
        plan = _sample_plan()
        muts = mutations_flip_assertion_op(plan)
        # 3 assertions: status==200, status==201, data.id!=None → 3 flips
        assert len(muts) == 3
        assert all(m.kind == "flip_op" for m in muts)

    def test_flip_does_not_mutate_original(self):
        plan = _sample_plan()
        before = plan.steps[0].asserts[0].op
        mutations_flip_assertion_op(plan)
        assert plan.steps[0].asserts[0].op == before

    def test_unknown_op_skipped(self):
        plan = TestPlan(steps=[
            Step(asserts=[Assertion(field="x", op="weird-op", expected=1)])
        ])
        assert mutations_flip_assertion_op(plan) == []


# ── Status tweaks ──────────────────────────────────────────────────────────


class TestTweakStatus:
    def test_one_per_api_step(self):
        plan = _sample_plan()
        muts = mutations_tweak_status(plan)
        assert len(muts) == 2

    def test_status_assertion_also_updated(self):
        plan = _sample_plan()
        muts = mutations_tweak_status(plan)
        first = muts[0].plan.steps[0]
        # status was 200 → expect 201; matching status assertion updated.
        assert first.expect_status == 201
        assert first.asserts[0].expected == 201

    def test_skips_non_api(self):
        plan = TestPlan(steps=[GuiStep(action="click", selector="x")])
        assert mutations_tweak_status(plan) == []


# ── Step removal ───────────────────────────────────────────────────────────


class TestRemoveStep:
    def test_one_mutation_per_step(self):
        plan = _sample_plan()
        muts = mutations_remove_step(plan)
        assert len(muts) == 2

    def test_each_mutation_has_one_fewer_step(self):
        plan = _sample_plan()
        muts = mutations_remove_step(plan)
        for m in muts:
            assert len(m.plan.steps) == len(plan.steps) - 1


# ── Scramble values ────────────────────────────────────────────────────────


class TestScrambleValue:
    def test_skips_status_assertions(self):
        plan = _sample_plan()
        muts = mutations_scramble_assertion_value(plan)
        # Only the data.id assertion is non-status → 1 mutation
        assert len(muts) == 1

    def test_int_increments(self):
        plan = TestPlan(steps=[Step(asserts=[Assertion(field="x", expected=5)])])
        muts = mutations_scramble_assertion_value(plan)
        assert muts[0].plan.steps[0].asserts[0].expected == 6

    def test_bool_negated(self):
        plan = TestPlan(steps=[Step(asserts=[Assertion(field="x", expected=True)])])
        muts = mutations_scramble_assertion_value(plan)
        assert muts[0].plan.steps[0].asserts[0].expected is False

    def test_string_suffixed(self):
        plan = TestPlan(steps=[Step(asserts=[Assertion(field="x", expected="abc")])])
        muts = mutations_scramble_assertion_value(plan)
        assert muts[0].plan.steps[0].asserts[0].expected == "abc_mutated"

    def test_unscrambleable_skipped(self):
        plan = TestPlan(steps=[Step(asserts=[Assertion(field="x", expected=None)])])
        # None can't be scrambled (returns None unchanged) → no mutation
        assert mutations_scramble_assertion_value(plan) == []


# ── Aggregator ─────────────────────────────────────────────────────────────


class TestMutate:
    def test_combines_all_mutators(self):
        plan = _sample_plan()
        muts = mutate(plan)
        kinds = {m.kind for m in muts}
        assert {"flip_op", "tweak_status", "remove_step", "scramble_value"} <= kinds


# ── Mutation harness ───────────────────────────────────────────────────────


class TestMutationHarness:
    def test_perfect_executor_kills_all(self):
        """An executor that snapshots the exact plan kills every mutation."""
        plan = _sample_plan()
        snapshot = plan.to_dict()

        def executor(p: TestPlan) -> bool:
            return p.to_dict() == snapshot

        report = run_mutation_test(plan, executor)
        assert report.total > 0
        assert report.killed == report.total
        assert report.killed_ratio == 1.0

    def test_weak_executor_lets_mutations_survive(self):
        """An executor that always passes catches no mutations."""
        plan = _sample_plan()
        report = run_mutation_test(plan, lambda _p: True)
        assert report.total > 0
        assert report.killed == 0
        assert report.killed_ratio == 0.0

    def test_failing_baseline_returns_empty(self):
        """If the original plan already fails, mutation testing is meaningless."""
        plan = _sample_plan()
        report = run_mutation_test(plan, lambda _p: False)
        assert report.total == 0
        assert report.killed_ratio == 1.0  # by convention: 0/0 → 1.0


class TestReportShape:
    def test_to_dict(self):
        plan = _sample_plan()
        report = run_mutation_test(plan, lambda _p: True)
        d = report.to_dict()
        assert "total" in d and "killed" in d and "killed_ratio" in d
        assert isinstance(d["survivors"], list)

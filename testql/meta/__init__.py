"""testql.meta — meta-testing primitives (Phase 5).

Combines four small modules:

    * `mutator`            — deterministic IR mutations + run_mutation_test
    * `coverage_analyzer`  — plan vs OpenAPI/DDL/Proto contract coverage
    * `confidence_scorer`  — per-step + plan-level confidence scoring
    * `self_test`          — generate + analyse the framework's own contract
"""

from __future__ import annotations

from .confidence_scorer import PlanConfidence, StepConfidence, score_plan
from .coverage_analyzer import (
    CoverageReport,
    analyze,
    coverage_vs_openapi,
    coverage_vs_proto,
    coverage_vs_sql,
)
from .mutator import (
    Mutation,
    MutationReport,
    mutate,
    mutations_flip_assertion_op,
    mutations_remove_step,
    mutations_scramble_assertion_value,
    mutations_tweak_status,
    run_mutation_test,
)
from .self_test import SelfTestReport, generate_self_test_plan, run_self_test

__all__ = [
    "Mutation", "MutationReport", "mutate", "run_mutation_test",
    "mutations_flip_assertion_op", "mutations_tweak_status",
    "mutations_remove_step", "mutations_scramble_assertion_value",
    "CoverageReport", "coverage_vs_openapi", "coverage_vs_sql",
    "coverage_vs_proto", "analyze",
    "StepConfidence", "PlanConfidence", "score_plan",
    "SelfTestReport", "generate_self_test_plan", "run_self_test",
]

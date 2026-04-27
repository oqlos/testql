"""Validate llm-decision.kimi.json and llm-decision.swe.json against schema."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
REPORTS = ROOT / ".testql" / "reports"
SCHEMA_PATH = ROOT / ".testql" / "schemas" / "llm-decision.schema.json"


def _load(name: str) -> dict:
    return json.loads((REPORTS / name).read_text())


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _check_required(data: dict, schema: dict) -> list[str]:
    return [f"missing required field: {f}" for f in schema.get("required", []) if f not in data]


def _check_decision(data: dict, schema: dict) -> list[str]:
    enum = schema["properties"]["decision"]["enum"]
    val = data.get("decision")
    return [] if val in enum else [f"invalid decision: {val!r}, must be one of {enum}"]


def _check_metrics(data: dict, schema: dict) -> list[str]:
    required = schema["properties"]["metrics"]["required"]
    metrics = data.get("metrics", {})
    return [f"metrics missing: {m}" for m in required if m not in metrics]


def _check_numerics(data: dict) -> list[str]:
    errors = []
    for field in ("confidence", "risk_score"):
        val = data.get(field)
        if not isinstance(val, (int, float)) or not 0 <= val <= 1:
            errors.append(f"{field}={val!r} must be number in [0,1]")
    return errors


def _check_next_actions(data: dict) -> list[str]:
    actions = data.get("next_actions", [])
    if not isinstance(actions, list) or not actions:
        return ["next_actions must be non-empty array"]
    return [
        f"next_actions[{i}] missing {key!r}"
        for i, action in enumerate(actions)
        for key in ("tool", "args")
        if key not in action
    ]


def _validate(data: dict, schema: dict) -> list[str]:
    return (
        _check_required(data, schema)
        + _check_decision(data, schema)
        + _check_metrics(data, schema)
        + _check_numerics(data)
        + _check_next_actions(data)
    )


class TestKimiDecision:
    def test_file_exists(self):
        assert (REPORTS / "llm-decision.kimi.json").exists()

    def test_valid_json(self):
        data = _load("llm-decision.kimi.json")
        assert isinstance(data, dict)

    def test_schema_valid(self):
        data = _load("llm-decision.kimi.json")
        schema = _schema()
        errors = _validate(data, schema)
        assert errors == [], f"Schema errors: {errors}"

    def test_decision_value(self):
        data = _load("llm-decision.kimi.json")
        schema = _schema()
        assert data["decision"] in schema["properties"]["decision"]["enum"]

    def test_confidence_high(self):
        data = _load("llm-decision.kimi.json")
        assert data["confidence"] >= 0.8, "KIMI should be high-confidence"

    def test_has_topology_focus(self):
        data = _load("llm-decision.kimi.json")
        assert len(data.get("topology_focus", [])) > 0


class TestSWEDecision:
    def test_file_exists(self):
        assert (REPORTS / "llm-decision.swe.json").exists()

    def test_valid_json(self):
        data = _load("llm-decision.swe.json")
        assert isinstance(data, dict)

    def test_schema_valid(self):
        data = _load("llm-decision.swe.json")
        schema = _schema()
        errors = _validate(data, schema)
        assert errors == [], f"Schema errors: {errors}"

    def test_decision_value(self):
        data = _load("llm-decision.swe.json")
        schema = _schema()
        assert data["decision"] in schema["properties"]["decision"]["enum"]

    def test_conservative_risk(self):
        data = _load("llm-decision.swe.json")
        assert data["risk_score"] >= 0.3, "SWE should flag higher risk conservatively"

    def test_has_multiple_next_actions(self):
        data = _load("llm-decision.swe.json")
        assert len(data.get("next_actions", [])) >= 2


class TestModelComparison:
    def test_both_same_iteration(self):
        kimi = _load("llm-decision.kimi.json")
        swe = _load("llm-decision.swe.json")
        assert kimi["iteration"] == swe["iteration"] == 1

    def test_both_valid_decisions(self):
        schema = _schema()
        enum = schema["properties"]["decision"]["enum"]
        kimi = _load("llm-decision.kimi.json")
        swe = _load("llm-decision.swe.json")
        assert kimi["decision"] in enum
        assert swe["decision"] in enum

    def test_kimi_higher_confidence_than_swe(self):
        kimi = _load("llm-decision.kimi.json")
        swe = _load("llm-decision.swe.json")
        assert kimi["confidence"] >= swe["confidence"], (
            f"KIMI ({kimi['confidence']}) should be >= SWE ({swe['confidence']})"
        )

    def test_swe_higher_risk_than_kimi(self):
        kimi = _load("llm-decision.kimi.json")
        swe = _load("llm-decision.swe.json")
        assert swe["risk_score"] >= kimi["risk_score"], (
            f"SWE ({swe['risk_score']}) should be >= KIMI ({kimi['risk_score']})"
        )

    def test_summary(self):
        kimi = _load("llm-decision.kimi.json")
        swe = _load("llm-decision.swe.json")
        print(f"\n{'Field':<15} {'KIMI':<30} {'SWE':<30}")
        print("-" * 75)
        for f in ["decision", "reason_code", "confidence", "risk_score"]:
            print(f"{f:<15} {str(kimi.get(f)):<30} {str(swe.get(f)):<30}")

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from testql.assertion_suite import (
    AssertionSuiteSyntaxError,
    evaluate_expression,
    parse_assertion_suite,
    parse_expression,
    run_assertion_suite,
)
from testql.cli import cli


SOURCE = """\
VERSION: 1
SUITE continuity authority:
  TEST deputy route:
    EXPECT founder.signals >= 2
    EXPECT resolution.actor == "human:deputy-founder"
    EXPECT resolution.channels contains "email"
  TEST legal implication:
    EXPECT task.risk >= "R3" implies task.human_approval == true
  TEST optional mandate:
    EXPECT mandate.id exists false
"""


def test_assertion_suite_parses_all_assertions_and_preflight_alias() -> None:
    suite = parse_assertion_suite(
        SOURCE.replace("VERSION: 1", "TESTQL_VERSION 1").replace(
            "SUITE continuity authority:",
            "SUITE continuity-authority TYPE PREFLIGHT:",
        )
    )
    assert suite.version == 1
    assert suite.suite_type == "PREFLIGHT"
    assert suite.assertion_count == 5


def test_assertion_expression_supports_boolean_logic_implication_and_exists() -> None:
    context = {
        "task": {"risk": "R3", "human_approval": True},
        "mandate": {},
        "pup": {"remote": True, "remote_rules_signed": True},
    }
    assert evaluate_expression(parse_expression('task.risk >= "R3" implies task.human_approval == true'), context)
    assert evaluate_expression(parse_expression("mandate.id exists false"), context)
    assert evaluate_expression(parse_expression("pup.remote == false or pup.remote_rules_signed == true"), context)


def test_unknown_instruction_and_empty_test_fail_closed() -> None:
    with pytest.raises(AssertionSuiteSyntaxError, match="unknown_testql_instruction"):
        parse_assertion_suite(SOURCE + "  APPROVE everything\n")
    with pytest.raises(AssertionSuiteSyntaxError, match="testql_assertions_missing"):
        parse_assertion_suite("VERSION: 1\nSUITE x:\n  TEST empty:\n")


def test_dry_run_validates_without_claiming_assertions_passed() -> None:
    result = run_assertion_suite(SOURCE, dry_run=True)
    assert result.ok
    assert result.passed == 0
    assert result.validated == 5
    assert result.executed == 0
    assert result.skipped == 5


def test_live_run_requires_real_context_and_executes_assertions() -> None:
    failed = run_assertion_suite(SOURCE, context={})
    assert not failed.ok
    assert failed.failed > 0

    passed = run_assertion_suite(
        SOURCE,
        context={
            "founder": {"signals": 2},
            "resolution": {"actor": "human:deputy-founder", "channels": ["email"]},
            "task": {"risk": "R3", "human_approval": True},
            "mandate": {},
        },
    )
    assert passed.ok
    assert passed.passed == 5
    assert passed.executed == 5


def test_cli_routes_dot_testql_to_strict_assertion_profile(tmp_path) -> None:
    scenario = tmp_path / "continuity.testql"
    scenario.write_text(SOURCE, encoding="utf-8")

    dry = CliRunner().invoke(cli, ["run", str(scenario), "--dry-run", "--output", "json", "--quiet"])
    assert dry.exit_code == 0, dry.output
    dry_payload = json.loads(dry.output)
    assert dry_payload["profile"] == "testql:assertion-suite/v1"
    assert dry_payload["passed"] == 0
    assert dry_payload["validated"] == 5
    assert dry_payload["executed"] == 0

    context = tmp_path / "context.json"
    context.write_text(
        json.dumps(
            {
                "founder": {"signals": 2},
                "resolution": {"actor": "human:deputy-founder", "channels": ["email"]},
                "task": {"risk": "R3", "human_approval": True},
                "mandate": {},
            }
        ),
        encoding="utf-8",
    )
    live = CliRunner().invoke(
        cli,
        ["run", str(scenario), "--context", str(context), "--output", "json", "--quiet"],
    )
    assert live.exit_code == 0, live.output
    live_payload = json.loads(live.output)
    assert live_payload["passed"] == 5
    assert live_payload["executed"] == 5


def test_cli_rejects_unknown_legacy_command_by_default(tmp_path) -> None:
    scenario = tmp_path / "legacy.oql"
    scenario.write_text("FROBNICATE anything\n", encoding="utf-8")
    result = CliRunner().invoke(
        cli,
        ["run", str(scenario), "--dry-run", "--quiet", "--output", "json"],
    )
    assert result.exit_code == 1
    assert "unknown_testql_command:FROBNICATE" in json.loads(result.output)["errors"][0]

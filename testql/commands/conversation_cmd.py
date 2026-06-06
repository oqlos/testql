"""CLI: testql conversation — multi-turn nlp2dsl scenario runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click

from testql.adapters.nlp2dsl import Nlp2DslAdapter, live_llm_enabled, resolve_llm_provider

if TYPE_CHECKING:
    from testql.conversation import ConversationRunResult, TestPlan


def _validate_scenario(adapter: Nlp2DslAdapter, scenario: Path) -> tuple[TestPlan, list]:
    """Parse and validate scenario; return (plan, error_issues)."""
    plan = adapter.parse(scenario)
    issues = [i for i in adapter.validate(plan) if i.severity == "error"]
    return plan, issues


def _resolve_base_url(api_url: str | None, plan: TestPlan) -> str:
    """Resolve nlp2dsl base URL from CLI option, plan config, or default."""
    return api_url or plan.config.get("nlp2dsl_base_url") or plan.config.get("base_url") or "http://localhost:8080"


def _create_runner(api_url: str, dry_run: bool, live_llm: bool, mock_replies: str | None):
    """Factory for ConversationRunner with resolved dependencies."""
    from testql.conversation import ConversationRunner
    return ConversationRunner(
        dry_run=dry_run,
        api_url=api_url,
        live_llm=live_llm or live_llm_enabled(),
        mock_replies=mock_replies,
    )


def _format_mode(dry_run: bool, live_llm: bool) -> str:
    """Determine execution mode label for output."""
    if dry_run:
        return "dry-run"
    if live_llm or live_llm_enabled():
        return "live-llm"
    return "mock-llm"


def _output_json(result: ConversationRunResult) -> None:
    """Emit result as formatted JSON."""
    click.echo(json.dumps(result.to_report_dict(), indent=2))


def _output_text(result: ConversationRunResult, scenario: Path, plan: TestPlan, dry_run: bool, live_llm: bool) -> None:
    """Emit result as human-readable text."""
    mode = _format_mode(dry_run, live_llm)
    click.echo(f"scenario: {plan.metadata.name or scenario.name} [{mode}]")
    for turn in result.turns:
        mark = "✓" if turn.status == "passed" else ("~" if turn.status == "skipped" else "✗")
        click.echo(f"  {mark} [{turn.kind}] {turn.summary}")
    click.echo(f"result: {'PASS' if result.passed else 'FAIL'}")


@click.group()
def conversation():
    """Run conversation TestQL scenarios against nlp2dsl."""
    pass


@conversation.command("run")
@click.argument("scenario", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--api-url", default=None, help="nlp2dsl base URL (default: NLP2DSL_URL or plan config)")
@click.option("--dry-run", is_flag=True, help="Validate IR only; skip HTTP/LLM")
@click.option("--mock-replies", type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help="YAML file with canned LLM replies")
@click.option("--live-llm", is_flag=True, help="Use live LLM (TESTQL_LIVE_LLM=1); requires API key")
@click.option("--output", "output_fmt", type=click.Choice(["text", "json"]), default="text")
def conversation_run(
    scenario: Path,
    api_url: str | None,
    dry_run: bool,
    mock_replies: Path | None,
    live_llm: bool,
    output_fmt: str,
) -> None:
    """Execute a `.testql.toon.yaml` conversation scenario."""
    adapter = Nlp2DslAdapter()
    plan, issues = _validate_scenario(adapter, scenario)
    if issues:
        for issue in issues:
            click.echo(f"validation error: {issue.message}", err=True)
        raise click.ClickException("scenario validation failed")

    base = _resolve_base_url(api_url, plan)
    runner = _create_runner(base, dry_run, live_llm, str(mock_replies) if mock_replies else None)
    result = runner.run(plan)

    if output_fmt == "json":
        _output_json(result)
    else:
        _output_text(result, scenario, plan, dry_run, live_llm)

    if not result.passed:
        raise SystemExit(1)


__all__ = ["conversation", "conversation_run"]

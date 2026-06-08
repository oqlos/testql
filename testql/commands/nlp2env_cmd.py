"""CLI: testql nlp2env — NL → MCP → .env scenario runner."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import click

from testql.adapters.nlp2env import Nlp2EnvAdapter
from testql.nlp2env.runner import Nlp2EnvRunner


def _validate(path: Path) -> None:
    adapter = Nlp2EnvAdapter()
    plan = adapter.parse(path)
    issues = [i for i in adapter.validate(plan) if i.severity == "error"]
    if issues:
        for issue in issues:
            click.echo(f"validation error: {issue.message}", err=True)
        raise click.ClickException("scenario validation failed")


@click.group()
def nlp2env():
    """Run TYPE: nlp2env TestTOON scenarios (NL → nlp2env MCP → .env)."""
    pass


@nlp2env.command("run")
@click.argument("scenario", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--workdir", type=click.Path(file_okay=False, path_type=Path), default=None)
@click.option("--example-dir", type=click.Path(file_okay=True, path_type=Path), default=None)
@click.option("--dry-run", is_flag=True, help="Parse/validate only; skip MCP/LLM")
@click.option("--skip-llm", is_flag=True, help="Skip source=llm prompts")
@click.option("--llm-only", is_flag=True, help="Run only source=llm prompts")
@click.option("--force-ollama", is_flag=True, help="Require Ollama for LLM prompts")
@click.option("--output", "output_fmt", type=click.Choice(["text", "json"]), default="text")
def nlp2env_run(
    scenario: Path,
    workdir: Path | None,
    example_dir: Path | None,
    dry_run: bool,
    skip_llm: bool,
    llm_only: bool,
    force_ollama: bool,
    output_fmt: str,
) -> None:
    """Execute a `.testql.toon.yaml` file with `# TYPE: nlp2env`."""
    _validate(scenario)
    runner = Nlp2EnvRunner(
        workdir=workdir,
        example_dir=example_dir or scenario.parent,
        dry_run=dry_run,
        skip_llm=skip_llm or os.getenv("NLP2ENV_SKIP_LLM", "").lower() in {"1", "true", "yes"},
        only_llm=llm_only or os.getenv("NLP2ENV_LLM_ONLY", "").lower() in {"1", "true", "yes"},
        force_ollama=force_ollama or os.getenv("NLP2ENV_FORCE_OLLAMA", "").lower() in {"1", "true", "yes"},
    )
    result = runner.run_file(scenario)
    if output_fmt == "json":
        click.echo(json.dumps({
            "source": result.source,
            "ok": result.ok,
            "passed": result.passed,
            "failed": result.failed,
            "duration_ms": round(result.duration_ms, 1),
            "errors": result.errors,
            "steps": [
                {"name": s.name, "status": s.status.value, "message": s.message}
                for s in result.steps
            ],
        }, indent=2))
    else:
        click.echo(result.summary())
        for step in result.steps:
            icon = "✓" if step.status.value == "passed" else "✗"
            click.echo(f"  {icon} [{step.name}] {step.message}")
    if not result.ok:
        raise SystemExit(1)


__all__ = ["nlp2env", "nlp2env_run"]

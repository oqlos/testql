"""`testql run-ir <file>` — execute a Unified IR `TestPlan`.

Sits next to the legacy `testql run` command without replacing it. Use
`run-ir` for SQL / Proto / GraphQL plans (which the legacy interpreter cannot
execute) and for typed step-by-step debugging of any TestTOON / NL scenario.
"""

from __future__ import annotations

import json
import sys

import click

from testql.ir_runner import run_plan


def _emit_json(result) -> None:
    click.echo(json.dumps({
        "source": result.source,
        "ok": result.ok,
        "passed": result.passed,
        "failed": result.failed,
        "steps": [
            {"name": s.name, "status": s.status.value,
             "message": s.message, "duration_ms": round(s.duration_ms, 2)}
            for s in result.steps
        ],
        "duration_ms": round(result.duration_ms, 2),
        "errors": result.errors,
        "warnings": result.warnings,
    }, indent=2))


def _emit_console(result) -> None:
    click.echo(result.summary())
    for s in result.steps:
        icon = {"passed": "  ✅", "failed": "  ❌", "error": "  💥",
                "skipped": "  ⏭️", "warning": "  ⚠️"}.get(s.status.value, "  •")
        click.echo(f"{icon} [{s.status.value}] {s.name}"
                   + (f" — {s.message}" if s.message else ""))


@click.command(name="run-ir")
@click.argument("file", type=click.Path(exists=True))
@click.option("--api-url", default="http://localhost:8101", help="Default base URL for ApiSteps")
@click.option("--encoder-url", default="http://localhost:8105", help="Encoder service URL")
@click.option("--graphql-url", default="http://localhost:8101/graphql", help="Default GraphQL endpoint")
@click.option("--dry-run", is_flag=True, help="Resolve + dispatch without executing")
@click.option("--output", type=click.Choice(["console", "json"]), default="console")
def run_ir(file: str, api_url: str, encoder_url: str, graphql_url: str,
           dry_run: bool, output: str) -> None:
    """Execute a Unified IR TestPlan from FILE."""
    result = run_plan(
        file, api_url=api_url, encoder_url=encoder_url,
        graphql_url=graphql_url, dry_run=dry_run, quiet=True,
    )
    if output == "json":
        _emit_json(result)
    else:
        _emit_console(result)
    sys.exit(0 if result.ok else 1)


__all__ = ["run_ir"]

"""CLI command: testql run — execute a single .testql.toon.yaml scenario."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--url", default="http://localhost:8101", help="Base API URL")
@click.option("--dry-run", is_flag=True, help="Parse and validate without executing")
@click.option(
    "--output",
    type=click.Choice(["console", "json"]),
    default="console",
    help="Output format",
)
@click.option("--quiet", is_flag=True, help="Suppress step-by-step output")
@click.option("--planfile", is_flag=True, help="Auto-create tickets for failures via planfile")
@click.option("--timeout", type=int, default=None, help="Global timeout in milliseconds for operations")
def run(file: str, url: str, dry_run: bool, output: str, quiet: bool, planfile: bool, timeout: int | None) -> None:
    """Run a TestQL (.testql.toon.yaml) scenario."""
    from testql.interpreter import IqlInterpreter

    source = Path(file).read_text(encoding="utf-8")
    filename = Path(file).name

    interp = IqlInterpreter(
        api_url=url,
        dry_run=dry_run,
        quiet=quiet,
        include_paths=[str(Path(file).parent), "."],
        timeout_ms=timeout,
    )
    result = interp.run(source, filename)

    if output == "json":
        import json

        print(
            json.dumps(
                {
                    "source": result.source,
                    "ok": result.ok,
                    "passed": result.passed,
                    "failed": result.failed,
                    "steps": len(result.steps),
                    "duration_ms": round(result.duration_ms, 1),
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
                indent=2,
            )
        )

    if not result.ok and planfile:
        from testql.integrations.planfile_hook import create_test_failure_ticket
        from testql.base import StepStatus
        error_msgs = []
        # Collect failed steps
        for step in result.steps:
            if step.status in (StepStatus.FAILED, StepStatus.ERROR):
                msg = f"`{step.name}`"
                if step.message:
                    msg += f": {step.message}"
                error_msgs.append(msg)
        
        # Add system errors if not already represented
        for err in result.errors:
            err_str = str(err)
            if not any(err_str in m for m in error_msgs):
                error_msgs.append(err_str)
            
        create_test_failure_ticket(error_msgs, filename)

    sys.exit(0 if result.ok else 1)

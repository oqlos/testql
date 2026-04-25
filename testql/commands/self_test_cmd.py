"""`testql self-test` — generate + analyse the framework's own contract."""

from __future__ import annotations

import json

import click

from testql.meta import run_self_test


def _print_human(report) -> None:
    cov = report.coverage
    conf = report.confidence
    click.echo(
        f"Coverage: {cov.covered}/{cov.total} endpoints "
        f"({cov.percent:.1f}%) of {cov.contract!r}"
    )
    click.echo(f"Confidence: {conf.plan_score:.2f}")
    click.echo(f"Mutations available: {report.mutation_count}")
    if cov.missing:
        click.echo("Missing endpoints:")
        for m in cov.missing:
            click.echo(f"  - {m}")
    click.echo(
        "Release-ready (1.0.0 gate ≥90% coverage & ≥0.7 confidence): "
        f"{'YES' if report.is_release_ready else 'NO'}"
    )


@click.command(name="self-test")
@click.option("--openapi", default="openapi.yaml",
              help="Path to the framework's OpenAPI spec (default: openapi.yaml)")
@click.option("--json", "as_json", is_flag=True, default=False,
              help="Emit machine-readable JSON instead of a human summary")
def self_test(openapi: str, as_json: bool) -> None:
    """Generate a TestPlan from `--openapi` and report coverage + confidence."""
    report = run_self_test(openapi)
    if as_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return
    _print_human(report)


__all__ = ["self_test"]

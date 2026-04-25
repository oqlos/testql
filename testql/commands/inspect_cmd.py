from __future__ import annotations

from pathlib import Path

import click

from testql.results import inspect_source, render_inspection, render_refactor_plan, render_result_envelope, write_inspection_artifacts


@click.command(name="inspect")
@click.argument("source", default=".", required=False)
@click.option("--format", "fmt", type=click.Choice(["toon", "yaml", "json", "nlp"]), default="toon")
@click.option("--artifact", type=click.Choice(["inspection", "result", "refactor-plan"]), default="inspection")
@click.option("--scan-network", is_flag=True, help="Enable network probes for URL sources")
@click.option("--browser", is_flag=True, help="Enable Playwright browser probe for URL sources")
@click.option("--out-dir", type=click.Path(file_okay=False, dir_okay=True), default=None, help="Write full inspection bundle, e.g. .testql")
def inspect(source: str, fmt: str, artifact: str, scan_network: bool, browser: bool, out_dir: str | None) -> None:
    source_path = Path(source)
    if not source.startswith(("http://", "https://")) and not source_path.exists():
        raise click.ClickException(f"source does not exist: {source}")
    topology, envelope, plan = inspect_source(source, scan_network=scan_network, use_browser=browser)
    if out_dir:
        written = write_inspection_artifacts(topology, envelope, plan, out_dir)
        click.echo(f"wrote {len(written)} files to {out_dir}")
        return
    if artifact == "result":
        click.echo(render_result_envelope(envelope, fmt), nl=False)
    elif artifact == "refactor-plan":
        click.echo(render_refactor_plan(plan, fmt), nl=False)
    else:
        click.echo(render_inspection(topology, envelope, plan, fmt), nl=False)


__all__ = ["inspect"]

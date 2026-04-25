from __future__ import annotations

from pathlib import Path

import click

from testql.topology import build_topology, render_topology


@click.command(name="topology")
@click.argument("source", default=".", required=False)
@click.option("--format", "fmt", type=click.Choice(["toon", "yaml", "json"]), default="toon")
@click.option("--include-manifest", is_flag=True, help="Include embedded ArtifactManifest on root node")
@click.option("--scan-network", is_flag=True, help="Enable network probes for URL sources")
def topology(source: str, fmt: str, include_manifest: bool, scan_network: bool) -> None:
    source_path = Path(source)
    if not source.startswith(("http://", "https://")) and not source_path.exists():
        raise click.ClickException(f"source does not exist: {source}")
    graph = build_topology(source, scan_network=scan_network)
    click.echo(render_topology(graph, fmt, include_manifest=include_manifest), nl=False)


__all__ = ["topology"]

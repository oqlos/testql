"""CLI: testql generate-topology — convert topology traces to executable scenarios."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from testql.topology import build_topology
from testql.topology.generator import TopologyScenarioGenerator


@click.command(name="generate-topology")
@click.argument("source", type=click.Path(exists=True), default=".")
@click.option("--trace-id", "-t", help="Trace ID to convert (default: first trace)")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--format", "fmt", type=click.Choice(["testtoon", "ir-json"]), default="testtoon")
@click.option("--scan-network", is_flag=True, help="Include live network scanning")
def generate_topology(source: str, trace_id: str | None, output: str | None, fmt: str, scan_network: bool) -> None:
    """Generate an executable scenario from a topology trace."""
    import json

    topology = build_topology(source, scan_network=scan_network)

    trace = _pick_trace(topology, trace_id)
    if trace is None:
        click.echo(f"❌ No trace found (requested: {trace_id or 'first'})")
        sys.exit(1)

    gen = TopologyScenarioGenerator(topology)
    plan = gen.from_trace(trace)

    if fmt == "testtoon":
        content = gen.to_testtoon(plan)
    else:
        content = json.dumps(plan.to_dict(), indent=2, default=str) + "\n"

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        click.echo(f"✅ Written {out_path}")
    else:
        click.echo(content, nl=False)

    sys.exit(0)


def _pick_trace(topology, trace_id: str | None):
    if not topology.traces:
        return None
    if trace_id is None:
        return topology.traces[0]
    return next((t for t in topology.traces if t.id == trace_id), None)


__all__ = ["generate_topology"]

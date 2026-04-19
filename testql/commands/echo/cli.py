"""CLI command for echo."""

from __future__ import annotations

import json
from pathlib import Path

import click

from .context import generate_context
from .formatters.text import format_text_output


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="text")
@click.option("--no-toon", is_flag=True, help="Exclude toon/API layer")
@click.option("--no-doql", is_flag=True, help="Exclude doql/system layer")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def echo(path: str, fmt: str, no_toon: bool, no_doql: bool, output: str | None):
    """Generate AI-friendly project context (echo) from toon + doql."""
    target = Path(path)

    context = generate_context(
        target,
        include_toon=not no_toon,
        include_doql=not no_doql,
    )

    if fmt == "json":
        output_str = json.dumps(context, indent=2, default=str)
    else:
        output_str = format_text_output(context)

    if output:
        Path(output).write_text(output_str)
        click.echo(f"✅ Project context saved: {output}")
    else:
        click.echo(output_str)

from __future__ import annotations

import json
from pathlib import Path

import click
import yaml

from testql.discovery import discover_path


@click.command(name="discover")
@click.argument("source", default=".", required=False)
@click.option("--format", "fmt", type=click.Choice(["summary", "manifest", "json"]), default="summary")
def discover(source: str, fmt: str) -> None:
    source_path = Path(source)
    if not source.startswith(("http://", "https://")) and not source_path.exists():
        raise click.ClickException(f"source does not exist: {source}")
    manifest = discover_path(source)
    if fmt == "json":
        click.echo(json.dumps(manifest.to_dict(include_raw=True), indent=2, sort_keys=True))
    elif fmt == "manifest":
        click.echo(yaml.safe_dump(manifest.to_dict(), sort_keys=False, allow_unicode=True), nl=False)
    else:
        _print_summary(manifest)


def _print_summary(manifest) -> None:
    data = manifest.to_dict()
    click.echo(f"Source: {data['source']['location']}")
    click.echo(f"Confidence: {data['confidence']}")
    detected = ", ".join(data["types"]) if data["types"] else "none"
    click.echo(f"Detected: {detected}")
    if data["metadata"]:
        name = data["metadata"].get("name")
        version = data["metadata"].get("version")
        if name or version:
            click.echo(f"Metadata: {name or '-'} {version or ''}".rstrip())
    click.echo(f"Evidence: {len(data['evidence'])}")
    for item in data["evidence"][:10]:
        detail = f" — {item['detail']}" if item.get("detail") else ""
        click.echo(f"  - {item['kind']}: {item['location']}{detail}")


__all__ = ["discover"]

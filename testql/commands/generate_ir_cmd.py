"""`testql generate-ir` — new IR-pipeline generator.

Sits alongside the legacy `testql generate` command (unchanged) so existing
CLI users see no behavioural change. Format of `--from` is `<source>:<path>`,
e.g. `openapi:./openapi.yaml`, `sql:./schema.sql`, `proto:./user.proto`,
`graphql:./schema.graphql`, `nl:./scenario.nl.md`, `ui:./snapshot.html`.
"""

from __future__ import annotations

import click

from testql.generators import pipeline
from testql.generators.sources import available_sources
from testql.generators.targets import available_targets


def _split_from_arg(value: str) -> tuple[str, str]:
    """Split `<source>:<path>` into (source_name, path). Errors clearly on bad input."""
    if ":" not in value:
        raise click.UsageError(
            f"--from must be '<source>:<path>'; got {value!r}. "
            f"Sources: {', '.join(available_sources())}"
        )
    source_name, _, path = value.partition(":")
    return source_name.strip(), path.strip()


@click.command(name="generate-ir")
@click.option("--from", "from_", required=True,
              help="Source artifact in '<source>:<path>' form, e.g. 'openapi:./api.yaml'")
@click.option("--to", "to_", required=True,
              help=f"Target DSL: one of {', '.join(available_targets())}")
@click.option("--out", "out", default=None,
              help="Output file or directory (defaults to stdout)")
@click.option("--no-llm", is_flag=True, default=True,
              help="Disable LLM enrichment (default: disabled — kept for forward compat)")
def generate_ir(from_: str, to_: str, out: str | None, no_llm: bool) -> None:
    """Generate scenarios from a source artifact via the IR pipeline."""
    source_name, path = _split_from_arg(from_)
    result = pipeline.run(source=source_name, target=to_, artifact=path)
    if out:
        written = pipeline.write(result, out)
        click.echo(f"wrote {written}")
    else:
        click.echo(result.output, nl=False)


__all__ = ["generate_ir"]

"""TestQL CLI — run .tql scenarios from the command line."""

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
def main(file: str, url: str, dry_run: bool, output: str, quiet: bool) -> None:
    """Run a TestQL (.tql) scenario."""
    from testql.interpreter import IqlInterpreter

    source = Path(file).read_text(encoding="utf-8")
    filename = Path(file).name

    interp = IqlInterpreter(
        api_url=url,
        dry_run=dry_run,
        quiet=quiet,
        include_paths=[str(Path(file).parent), "."],
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

    sys.exit(0 if result.ok else 1)


if __name__ == "__main__":
    main()

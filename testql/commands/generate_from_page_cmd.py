"""CLI: ``testql generate-from-page <url>``.

Drives Playwright against a live URL, extracts focusable elements via the
accessibility-aware DOM walker in
:mod:`testql.generators.sources.page_source`, builds a
:class:`testql.ir.TestPlan` via :mod:`testql.generators.page_analyzer`, and
renders it as a deterministic ``*.testql.toon.yaml`` scenario.

Use ``--from-elements <file.json>`` to skip Playwright entirely and feed
pre-extracted element descriptors (the same shape the JS extractor returns).
This is what the test suite uses to keep CI hermetic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.generators.page_analyzer import PageSnapshot, snapshot_to_plan
from testql.generators.sources.page_source import PageSource


def _default_output(url: str) -> Path:
    """Pick a sensible output filename derived from URL path."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    slug = (parsed.path or "/").strip("/").replace("/", "-") or "home"
    return Path(f"generated-page-{slug}.testql.toon.yaml")


@click.command("generate-from-page")
@click.argument("url", type=str)
@click.option(
    "--output", "-o", "output", type=click.Path(dir_okay=False, path_type=Path),
    default=None, help="Output .testql.toon.yaml path (default: derived from URL)",
)
@click.option(
    "--max-steps", type=int, default=50, show_default=True,
    help="Cap the number of generated GUI steps.",
)
@click.option(
    "--headless/--headed", default=True, show_default=True,
    help="Run Playwright headless or headed.",
)
@click.option(
    "--from-elements", "from_elements", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None, help="Skip Playwright; load element descriptors from a JSON file.",
)
@click.option(
    "--print", "print_only", is_flag=True,
    help="Print the rendered scenario to stdout instead of writing a file.",
)
def generate_from_page(
    url: str,
    output: Path | None,
    max_steps: int,
    headless: bool,
    from_elements: Path | None,
    print_only: bool,
) -> None:
    """Auto-generate a TestTOON GUI scenario from a live URL."""
    if from_elements is not None:
        elements = json.loads(from_elements.read_text(encoding="utf-8"))
        from urllib.parse import urlparse
        parsed = urlparse(url)
        snap = PageSnapshot(
            url=url,
            title=url,
            path=parsed.path or "/",
            elements=elements,
        )
        base_url = (
            f"{parsed.scheme}://{parsed.netloc}"
            if parsed.scheme and parsed.netloc else None
        )
        plan = snapshot_to_plan(snap, base_url=base_url, max_steps=max_steps)
    else:
        try:
            source = PageSource(headless=headless, max_steps=max_steps)
            plan = source.load(url)
        except RuntimeError as exc:
            click.echo(f"❌ {exc}", err=True)
            sys.exit(2)

    rendered = TestToonAdapter().render(plan)

    if print_only:
        click.echo(rendered)
        return

    out_path = output or _default_output(url)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(rendered, encoding="utf-8")
    click.echo(f"✅ Wrote {out_path} ({len(plan.steps)} steps)")

"""CLI: ``testql heal-scenario <file> --url <url>``.

Loads an existing ``*.testql.toon.yaml``, drives Playwright against ``--url``,
and for every selector that no longer resolves on the live page, attempts to
find a replacement via accessible-name match
(:func:`testql.generators.page_analyzer.find_replacement`).

The healed scenario is written next to the original (suffix ``.healed.testql.toon.yaml``)
or in place when ``--write`` is given. A diff-style summary is always printed.

Selectors are detected with a deliberately conservative regex over the raw
text — this preserves comments, blank lines and column ordering exactly,
which is important for human-edited scenarios.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import click


# Match strings that *look like* CSS selectors inside a TestTOON FLOW/ASSERT row
# or a bare GUI_* command. Keeps things text-based so we can rewrite in place.
#
# Examples we want to capture:
#   FLOW: "  click,  #btn-go,  -"             → "#btn-go"
#   ASSERT: "  .qr-scanner-container, visible" → ".qr-scanner-container"
#   GUI_CLICK "[data-testid=submit]"          → "[data-testid=submit]"
#
# False positives we deliberately reject:
#   FLOW[3]{...}    →  `[3]` (numeric — TOON section header)
#   user@gmail.com  →  `.com` (alphanumeric prefix — part of email/url)
_SELECTOR_RE = re.compile(
    r"""
    (?<![A-Za-z0-9_])                     # selector must not be glued to a word
    (?P<sel>
        \[ \s* [A-Za-z][\w\-]* [^\]\n]* \] # [attr=...]; first char of attr must be a letter
        | \# [A-Za-z][\w\-]*                # #id (must start with letter, not digit)
        | \. [A-Za-z][\w\-]*                # .class (must start with letter)
    )
    """,
    re.VERBOSE,
)


@dataclass
class HealReport:
    file: Path
    url: str
    total_selectors: int = 0
    valid: int = 0
    healed: int = 0
    unhealable: list[tuple[str, str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.unhealable is None:
            self.unhealable = []


# ---------------------------------------------------------------------------
# Selector validation + replacement against a Playwright page
# ---------------------------------------------------------------------------

def _collect_selectors(text: str) -> list[str]:
    """Return the set of distinct selectors present in the scenario text."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _SELECTOR_RE.finditer(text):
        sel = m.group("sel").strip()
        if sel not in seen:
            seen.add(sel)
            out.append(sel)
    return out


def _selector_resolves(page: Any, selector: str) -> bool:
    try:
        return page.locator(selector).count() > 0
    except Exception:
        return False


def _healed_path(file: Path) -> Path:
    """Compute the ``.healed.testql.toon.yaml`` sibling path.

    ``Path.with_suffix`` only swaps the *last* suffix, so for a file named
    ``foo.testql.toon.yaml`` it would produce ``foo.testql.toon.healed.testql.toon.yaml``.
    Strip every recognised TestTOON suffix before re-appending the healed one.
    """
    name = file.name
    for suffix in (".testql.toon.yaml", ".testql.toon.yml", ".testql.yaml", ".testql.yml"):
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            return file.with_name(f"{stem}.healed{suffix}")
    return file.with_suffix(".healed" + file.suffix)


def _heal_text(
    text: str,
    replacements: dict[str, str],
) -> str:
    """Rewrite each broken selector with its replacement.

    Uses whole-token replacement so we don't accidentally hit a substring of
    a longer selector (e.g. `#btn` vs `#btn-go`).
    """
    if not replacements:
        return text
    out = text
    for old, new in replacements.items():
        # word-boundary regex so '#btn' doesn't match inside '#btn-go'.
        pattern = re.compile(re.escape(old) + r"(?![A-Za-z0-9_\-])")
        out = pattern.sub(new, out)
    return out


# ---------------------------------------------------------------------------
# Click command
# ---------------------------------------------------------------------------

@click.command("heal-scenario")
@click.argument("file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--url", required=True, type=str,
    help="Live URL to validate selectors against.",
)
@click.option(
    "--write", is_flag=True,
    help="Rewrite FILE in place. Without this flag a *.healed.testql.toon.yaml is created.",
)
@click.option(
    "--from-elements", "from_elements", type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Skip Playwright; load element descriptors from JSON. Used by tests.",
)
@click.option(
    "--headless/--headed", default=True, show_default=True,
    help="Run Playwright headless or headed.",
)
@click.option(
    "--report", "report_path", type=click.Path(dir_okay=False, path_type=Path),
    default=None, help="Write a JSON heal report to this path.",
)
def heal_scenario(
    file: Path,
    url: str,
    write: bool,
    from_elements: Path | None,
    headless: bool,
    report_path: Path | None,
) -> None:
    """Validate and heal selectors in an existing TestTOON scenario."""
    text = file.read_text(encoding="utf-8")
    selectors = _collect_selectors(text)

    if not selectors:
        click.echo("No CSS selectors detected — nothing to heal.")
        return

    if from_elements is not None:
        elements = json.loads(from_elements.read_text(encoding="utf-8"))
        replacements, unhealable, valid_count = _heal_with_elements(
            selectors, elements,
        )
    else:
        try:
            replacements, unhealable, valid_count = _heal_with_browser(
                url, selectors, headless=headless,
            )
        except RuntimeError as exc:
            click.echo(f"❌ {exc}", err=True)
            sys.exit(2)

    report = HealReport(
        file=file,
        url=url,
        total_selectors=len(selectors),
        valid=valid_count,
        healed=len(replacements),
        unhealable=unhealable,
    )

    healed_text = _heal_text(text, replacements)
    if replacements:
        target = file if write else _healed_path(file)
        target.write_text(healed_text, encoding="utf-8")
        click.echo(f"✅ Wrote {target}")

    _print_summary(report, replacements)
    if report_path is not None:
        report_path.write_text(
            json.dumps({
                "file": str(file),
                "url": url,
                "total_selectors": report.total_selectors,
                "valid": report.valid,
                "healed": report.healed,
                "replacements": replacements,
                "unhealable": [
                    {"selector": s, "reason": r} for s, r in report.unhealable
                ],
            }, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Healing strategies (browser / pre-extracted)
# ---------------------------------------------------------------------------

def _heal_with_elements(
    selectors: list[str],
    elements: list[dict[str, Any]],
) -> tuple[dict[str, str], list[tuple[str, str]], int]:
    """Heal using a pre-extracted element list (no browser)."""
    from testql.adapters.testtoon_adapter import _toon_safe_selector
    from testql.generators.page_analyzer import find_replacement, pick_selector

    # Selector → "valid if it matches any element's pick_selector(...) output"
    valid_selectors = {pick_selector(e) for e in elements}
    valid_selectors.discard(None)

    replacements: dict[str, str] = {}
    unhealable: list[tuple[str, str]] = []
    valid_count = 0
    for sel in selectors:
        if sel in valid_selectors:
            valid_count += 1
            continue
        new = find_replacement(sel, elements)
        if new and new != sel:
            replacements[sel] = _toon_safe_selector(new)
        else:
            unhealable.append((sel, "no fuzzy match"))
    return replacements, unhealable, valid_count


def _heal_with_browser(
    url: str,
    selectors: list[str],
    *,
    headless: bool,
) -> tuple[dict[str, str], list[tuple[str, str]], int]:
    """Heal by driving Playwright and querying the live page."""
    try:
        from playwright.sync_api import sync_playwright  # noqa: WPS433
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "heal-scenario requires playwright. Install with: "
            "pip install playwright && playwright install chromium"
        ) from exc

    from testql.adapters.testtoon_adapter import _toon_safe_selector
    from testql.generators.page_analyzer import find_replacement
    from testql.generators.sources.page_source import extract_elements_from_page

    replacements: dict[str, str] = {}
    unhealable: list[tuple[str, str]] = []
    valid_count = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            elements = extract_elements_from_page(page)
            for sel in selectors:
                if _selector_resolves(page, sel):
                    valid_count += 1
                    continue
                new = find_replacement(sel, elements)
                if new and new != sel and _selector_resolves(page, new):
                    replacements[sel] = _toon_safe_selector(new)
                else:
                    unhealable.append((sel, "no live match"))
        finally:
            browser.close()
    return replacements, unhealable, valid_count


# ---------------------------------------------------------------------------
# Pretty output
# ---------------------------------------------------------------------------

def _print_summary(report: HealReport, replacements: dict[str, str]) -> None:
    click.echo("")
    click.echo(f"📋 heal-scenario report for {report.file.name}")
    click.echo(f"   URL: {report.url}")
    click.echo(
        f"   Selectors: {report.total_selectors} total, "
        f"{report.valid} valid, {report.healed} healed, "
        f"{len(report.unhealable)} unhealable",
    )
    if replacements:
        click.echo("\n   Replacements:")
        for old, new in replacements.items():
            click.echo(f"     - {old}  →  {new}")
    if report.unhealable:
        click.echo("\n   Unhealable:")
        for sel, reason in report.unhealable:
            click.echo(f"     - {sel}  ({reason})")

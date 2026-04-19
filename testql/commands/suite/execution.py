"""Test execution utilities for suite command."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from testql.interpreter import IqlInterpreter


def run_single_file(test_file: Path, interp) -> dict:
    """Run a single test file and return result dict."""
    try:
        result = interp.run_file(str(test_file))
        status = "✅ PASS" if result.ok else "❌ FAIL"
        click.echo(
            f"    {status} ({result.passed} passed, {result.failed} failed,"
            f" {result.duration_ms:.0f}ms)"
        )
        return {
            "file": str(test_file),
            "name": test_file.name,
            "ok": result.ok,
            "passed": result.passed,
            "failed": result.failed,
            "duration_ms": result.duration_ms,
            "errors": result.errors,
        }
    except Exception as exc:
        click.echo(f"    ❌ ERROR: {exc}")
        return {
            "file": str(test_file),
            "name": test_file.name,
            "ok": False,
            "error": str(exc),
        }


def run_suite_files(
    test_files: list[Path],
    url: str,
    output: str,
    fail_fast: bool,
    config: dict,
) -> tuple[list[dict], bool]:
    """Run suite of test files and return results."""
    from testql.interpreter import IqlInterpreter

    results: list[dict] = []
    all_passed = True

    for i, test_file in enumerate(test_files, 1):
        click.echo(f"[{i}/{len(test_files)}] {test_file.name}")

        interp = IqlInterpreter(
            api_url=url or config.get("defaults", {}).get("api_url", "http://localhost:8101"),
            quiet=(output != "console"),
            include_paths=[str(test_file.parent), "."],
        )

        result = run_single_file(test_file, interp)
        results.append(result)

        if not result.get("ok"):
            all_passed = False
            if fail_fast:
                click.echo("\n⚡ Fail-fast enabled, stopping suite")
                break

    return results, all_passed

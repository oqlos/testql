"""CLI commands for suite - testql suite, testql list."""

from __future__ import annotations

import sys
from pathlib import Path

import click
import yaml

from .collection import collect_test_files, collect_list_files
from .execution import run_suite_files
from .reports import build_report_data, save_report, print_summary
from .listing import filter_tests, render_test_list


@click.command()
@click.argument("suite_name", required=False)
@click.option("--path", "-p", "base_path", type=click.Path(), default=".", help="Path to test files or testql.yaml")
@click.option("--pattern", help="Glob pattern to match test files")
@click.option("--tag", "tags", multiple=True, help="Run tests with specific tags")
@click.option("--type", "test_types", multiple=True, type=click.Choice(["gui", "api", "mixed", "encoder", "performance"]), help="Filter by test type")
@click.option("--parallel", "-j", type=int, default=1, help="Parallel execution (default: 1)")
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
@click.option("--output", "-o", type=click.Choice(["console", "json", "junit", "html"]), default="console")
@click.option("--report", "-r", type=click.Path(), help="Save report to file")
@click.option("--url", help="Override base URL")
def suite(
    suite_name: str | None,
    base_path: str,
    pattern: str | None,
    tags: tuple,
    test_types: tuple,
    parallel: int,
    fail_fast: bool,
    output: str,
    report: str | None,
    url: str | None,
) -> None:
    """Run test suite(s) — predefined or custom pattern."""
    target_path = Path(base_path)

    # Load config
    config_file = (
        target_path / "testql.yaml"
        if target_path.is_dir()
        else target_path.parent / "testql.yaml"
    )
    config: dict = {}
    if config_file.exists():
        config = yaml.safe_load(config_file.read_text()) or {}

    # Collect test files
    test_files = collect_test_files(target_path, suite_name, pattern, config)
    if not test_files:
        click.echo("❌ No test files found")
        sys.exit(1)

    click.echo(f"🧪 Running {len(test_files)} test(s)\n")

    # Run tests
    results, all_passed = run_suite_files(
        test_files, url or "", output, fail_fast, config
    )

    # Calculate totals
    total_passed = sum(r.get("passed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    total_duration = sum(r.get("duration_ms", 0) for r in results)

    # Print summary
    print_summary(results, total_passed, total_failed, total_duration)

    # Save report if requested
    if report or output in ("json", "junit", "html"):
        report_data = build_report_data(suite_name, results, total_passed, total_failed, total_duration)
        report_file = report or f"testql-report.{output}"
        save_report(report_data, report_file, output)

    sys.exit(0 if all_passed else 1)


@click.command(name="list")
@click.option("--path", "-p", type=click.Path(), default=".", help="Path to search for tests")
@click.option("--type", "test_type", type=click.Choice(["gui", "api", "mixed", "encoder", "performance", "all"]), default="all", help="Filter by type")
@click.option("--tag", help="Filter by tag")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "simple"]), default="table")
def list_tests(path: str, test_type: str, tag: str | None, fmt: str) -> None:
    """List all available tests with metadata."""
    target_path = Path(path)

    # Collect and filter
    raw_files = collect_list_files(target_path)
    tests = filter_tests(raw_files, target_path, test_type, tag, yaml)

    if not tests:
        click.echo("No test files found.")
        return

    render_test_list(tests, fmt)

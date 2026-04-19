"""Report generation utilities for suite command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    pass


def build_report_data(
    suite_name,
    results: list[dict],
    total_passed: int,
    total_failed: int,
    total_duration: float,
) -> dict:
    """Build report data structure."""
    return {
        "suite": suite_name or "custom",
        "timestamp": "now",
        "summary": {
            "files": len(results),
            "passed": len([r for r in results if r.get("ok")]),
            "failed": len([r for r in results if not r.get("ok")]),
            "tests_passed": total_passed,
            "tests_failed": total_failed,
            "duration_ms": total_duration,
        },
        "results": results,
    }


def _save_json_report(report_data: dict, report_file: str) -> None:
    """Save report as JSON."""
    Path(report_file).write_text(json.dumps(report_data, indent=2))


def _build_junit_xml(report_data: dict) -> str:
    """Build JUnit XML report content."""
    results = report_data["results"]
    total_duration = report_data["summary"]["duration_ms"]
    failures = len([r for r in results if not r.get("ok")])

    junit_xml = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<testsuites name="TestQL" tests="{len(results)}"'
        f' failures="{failures}"'
        f' time="{total_duration/1000:.3f}">\n'
    )

    for r in results:
        duration = r.get("duration_ms", 0) / 1000
        junit_xml += (
            f'  <testsuite name="{r["name"]}"'
            f' tests="{r.get("passed", 0) + r.get("failed", 0)}"'
            f' failures="{r.get("failed", 0)}"'
            f' time="{duration:.3f}">\n'
        )
        for e in r.get("errors", []):
            junit_xml += f'    <failure message="{e}"/>\n'
        junit_xml += "  </testsuite>\n"

    junit_xml += "</testsuites>"
    return junit_xml


def save_report(report_data: dict, report_file: str, output: str) -> None:
    """Save report in requested format."""
    if output == "json":
        _save_json_report(report_data, report_file)
    elif output == "junit":
        junit_xml = _build_junit_xml(report_data)
        Path(report_file).write_text(junit_xml)

    click.echo(f"📄 Report saved: {report_file}")


def print_summary(results: list[dict], total_passed: int, total_failed: int, total_duration: float) -> None:
    """Print execution summary to console."""
    passed_files = len([r for r in results if r.get("ok")])
    click.echo(f"\n{'='*50}")
    click.echo(f"Results: {passed_files}/{len(results)} files passed")
    click.echo(f"Tests: {total_passed} passed, {total_failed} failed")
    click.echo(f"Duration: {total_duration:.0f}ms")

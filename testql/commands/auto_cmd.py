"""Auto command — One-liner for generate + run + report workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from testql import __version__ as TESTQL_VERSION
from testql.results import analyze_topology, inspect_source
from testql.results.artifacts import write_inspection_artifacts
from testql.topology.builder import build_topology


@click.command(name="auto")
@click.argument("source", type=click.Path(exists=True), required=False)
@click.option("--url", default="http://localhost:8000", help="Base URL for running tests")
@click.option("--api-url", default=None, help="API URL (defaults to --url)")
@click.option("-o", "--output-dir", default=".testql-auto", help="Output directory for artifacts")
@click.option("--format", "output_format", type=click.Choice(["console", "json", "markdown"]), default="console")
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
@click.option("--keep-generated", is_flag=True, help="Keep generated test files after run")
@click.pass_context
def auto(ctx, source, url, api_url, output_dir, output_format, fail_fast, keep_generated):
    """One-liner: generate tests from service, run them, and create report.

    SOURCE is the path to inspect (default: current directory).

    Examples:

        \b
        testql auto                                  # Auto-detect and test current dir
        testql auto ./my-service --url http://localhost:3000
        testql auto /path/to/c2004 --api-url http://localhost:8101
        testql auto . --format markdown --output-dir ./reports
    """
    source = source or "."
    api_url = api_url or url
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Run phases
    topology, envelope, plan, written = _run_generation_phase(source, out_dir)
    testable_nodes = _run_analysis_phase(topology)
    report_data = _build_report_data(source, url, api_url, topology, envelope, testable_nodes, written, out_dir)
    _run_report_phase(report_data, out_dir, output_format)
    _print_summary(envelope, report_data, out_dir)

    # Exit with appropriate code
    if envelope.status == "failed":
        sys.exit(1)
    elif envelope.status == "partial":
        sys.exit(2)  # Partial success
    sys.exit(0)


def _status_color(status: str) -> str:
    return {"passed": "green", "failed": "red", "partial": "yellow"}.get(status, "white")


def _run_generation_phase(source: str, out_dir: Path):
    """Phase 1: Generate inspection artifacts."""
    click.echo(click.style("▶ Phase 1: Generating test scenarios...", fg="blue", bold=True))
    generated_dir = out_dir / "generated"
    generated_dir.mkdir(exist_ok=True)

    try:
        topology, envelope, plan = inspect_source(source)
        written = write_inspection_artifacts(topology, envelope, plan, out_dir)
        click.echo(f"  {click.style('✓', fg='green')} Generated inspection artifacts in {out_dir}")
        return topology, envelope, plan, written
    except Exception as e:
        click.echo(f"  {click.style('✗', fg='red')} Generation failed: {e}", err=True)
        sys.exit(1)


def _run_analysis_phase(topology):
    """Phase 2: Analyze testability."""
    click.echo(click.style("\n▶ Phase 2: Analyzing testability...", fg="blue", bold=True))
    testable_nodes = [n for n in topology.nodes if n.kind in ("api", "web", "service")]
    click.echo(f"  {click.style('•', fg='yellow')} Found {len(testable_nodes)} testable service(s)")
    for node in testable_nodes:
        click.echo(f"    - {node.kind}: {node.id}")
    return testable_nodes


def _build_report_data(source, url, api_url, topology, envelope, testable_nodes, written, out_dir):
    """Build report data dictionary."""
    return {
        "version": TESTQL_VERSION,
        "source": str(source),
        "url": url,
        "api_url": api_url,
        "status": envelope.status,
        "topology": {
            "nodes": len(topology.nodes),
            "edges": len(topology.edges),
            "testable": len(testable_nodes),
        },
        "checks": {
            "total": len(envelope.checks),
            "passed": len([c for c in envelope.checks if c.status == "passed"]),
            "failed": len([c for c in envelope.checks if c.status == "failed"]),
            "warnings": len([c for c in envelope.checks if c.status == "warning"]),
        },
        "findings": [
            {"id": f.id, "severity": f.severity, "summary": f.summary}
            for f in envelope.failures
        ],
        "artifacts": [str(p.relative_to(out_dir)) for p in written],
    }


def _run_report_phase(report_data: dict, out_dir: Path, output_format: str):
    """Phase 3: Generate and output report."""
    click.echo(click.style("\n▶ Phase 3: Generating report...", fg="blue", bold=True))

    # Save JSON report
    report_json = out_dir / "auto-report.json"
    report_json.write_text(json.dumps(report_data, indent=2))

    # Output based on format
    if output_format == "json":
        click.echo(json.dumps(report_data, indent=2))
    elif output_format == "markdown":
        md = _render_markdown_report(report_data, out_dir)
        report_md = out_dir / "auto-report.md"
        report_md.write_text(md)
        click.echo(f"  {click.style('✓', fg='green')} Markdown report: {report_md}")
    else:
        _render_console_report(report_data, out_dir)


def _print_summary(envelope, report_data: dict, out_dir: Path):
    """Print summary section."""
    click.echo(click.style("\n═══════════════════════════════════════════════════════════", fg="blue"))
    click.echo(click.style("  AUTO TEST COMPLETE", fg="blue", bold=True))
    click.echo(click.style("═══════════════════════════════════════════════════════════", fg="blue"))
    click.echo(f"  Status: {click.style(envelope.status.upper(), fg=_status_color(envelope.status))}")
    click.echo(f"  Checks: {report_data['checks']['total']} total")
    click.echo(f"    {click.style('✓', fg='green')} Passed: {report_data['checks']['passed']}")
    click.echo(f"    {click.style('✗', fg='red')} Failed: {report_data['checks']['failed']}")
    click.echo(f"    {click.style('⚠', fg='yellow')} Warnings: {report_data['checks']['warnings']}")
    click.echo(f"\n  Output directory: {click.style(str(out_dir.absolute()), fg='cyan', underline=True)}")
    click.echo(click.style("═══════════════════════════════════════════════════════════", fg="blue"))


def _render_console_report(data: dict, out_dir: Path) -> None:
    """Render human-readable console report."""
    click.echo(f"\n  {click.style('Topology:', bold=True)}")
    click.echo(f"    Nodes: {data['topology']['nodes']}")
    click.echo(f"    Edges: {data['topology']['edges']}")
    click.echo(f"    Testable: {data['topology']['testable']}")

    if data["findings"]:
        click.echo(f"\n  {click.style('Key Findings:', bold=True)}")
        for f in data["findings"][:5]:
            color = {"critical": "red", "high": "red", "medium": "yellow", "low": "blue"}.get(f["severity"], "white")
            click.echo(f"    {click.style('[' + f['severity'] + ']', fg=color)} {f['summary']}")

    click.echo(f"\n  {click.style('Artifacts:', bold=True)}")
    for artifact in data["artifacts"][:5]:
        click.echo(f"    - {artifact}")


def _render_markdown_report(data: dict, out_dir: Path) -> str:
    """Render markdown report."""
    lines = [
        "# Auto-Test Report",
        "",
        f"**Source:** `{data['source']}`  ",
        f"**URL:** {data['url']}  ",
        f"**Status:** {data['status'].upper()}  ",
        f"**TestQL Version:** {data['version']}",
        "",
        "## Summary",
        "",
        f"- **Nodes:** {data['topology']['nodes']}",
        f"- **Edges:** {data['topology']['edges']}",
        f"- **Testable Services:** {data['topology']['testable']}",
        "",
        "## Checks",
        "",
        f"| Total | Passed | Failed | Warnings |",
        f"|-------|--------|--------|----------|",
        f"| {data['checks']['total']} | {data['checks']['passed']} | {data['checks']['failed']} | {data['checks']['warnings']} |",
        "",
    ]

    if data["findings"]:
        lines.extend(["## Findings", ""])
        for f in data["findings"]:
            lines.append(f"- **[{f['severity'].upper()}]** {f['summary']}")
        lines.append("")

    lines.extend(["## Artifacts", ""])
    for artifact in data["artifacts"]:
        lines.append(f"- [{artifact}]({artifact})")

    return "\n".join(lines) + "\n"

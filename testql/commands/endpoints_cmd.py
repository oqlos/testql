"""CLI commands: testql endpoints, testql openapi — endpoint detection & OpenAPI generation."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--framework", help="Filter by framework (fastapi, flask, django, express)")
@click.option("--type", "endpoint_type", help="Filter by type (rest, graphql, websocket)")
@click.option("--output", "-o", type=click.Path(), help="Save to file")
def endpoints(
    path: str,
    fmt: str,
    framework: str | None,
    endpoint_type: str | None,
    output: str | None,
) -> None:
    """List all detected API endpoints in a project."""
    import csv
    import io
    import json

    from testql.endpoint_detector import UnifiedEndpointDetector

    target_path = Path(path)
    detector = UnifiedEndpointDetector(target_path)
    eps = detector.detect_all()

    if framework:
        eps = [ep for ep in eps if ep.framework == framework]
    if endpoint_type:
        eps = [ep for ep in eps if ep.endpoint_type == endpoint_type]

    if not eps:
        click.echo("❌ No endpoints detected")
        sys.exit(1)

    output_str = _format_endpoints(eps, fmt, target_path, detector)

    if output:
        Path(output).write_text(output_str)
        click.echo(f"✅ Saved {len(eps)} endpoints to {output}")
    else:
        click.echo(output_str)


def _format_endpoints_json(eps, target_path: Path) -> str:
    import json
    data = [
        {
            "path": ep.path, "method": ep.method, "framework": ep.framework,
            "type": ep.endpoint_type, "handler": ep.handler_name,
            "file": str(ep.source_file.relative_to(target_path)) if ep.source_file else None,
            "line": ep.line_number, "summary": ep.summary,
        }
        for ep in eps
    ]
    return json.dumps(data, indent=2)


def _format_endpoints_csv(eps, target_path: Path) -> str:
    import csv, io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["method", "path", "framework", "type", "handler", "file", "line", "summary"])
    for ep in eps:
        writer.writerow([
            ep.method, ep.path, ep.framework, ep.endpoint_type, ep.handler_name or "",
            str(ep.source_file.relative_to(target_path)) if ep.source_file else "",
            ep.line_number, ep.summary or "",
        ])
    return buf.getvalue()


def _format_endpoints_table(eps, detector) -> str:
    lines = [f"{'Method':<8} {'Path':<40} {'Framework':<12} {'Handler':<30}", "-" * 90]
    for ep in eps:
        handler = ep.handler_name or "-"
        if len(handler) > 28:
            handler = handler[:25] + "..."
        ep_path = ep.path if len(ep.path) < 38 else ep.path[:35] + "..."
        lines.append(f"{ep.method:<8} {ep_path:<40} {ep.framework:<12} {handler:<30}")
    lines.append("")
    lines.append(f"Total: {len(eps)} endpoints (detectors: {', '.join(detector.detectors_used)})")
    return "\n".join(lines)


def _format_endpoints(eps, fmt: str, target_path: Path, detector) -> str:
    if fmt == "json":
        return _format_endpoints_json(eps, target_path)
    if fmt == "csv":
        return _format_endpoints_csv(eps, target_path)
    return _format_endpoints_table(eps, detector)


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: openapi.yaml)")
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")
@click.option("--title", help="API title (default: project name)")
@click.option("--version", default="1.0.0", help="API version")
@click.option("--contract-tests", is_flag=True, help="Also generate contract tests")
def openapi(
    path: str,
    output: str | None,
    format: str,
    title: str | None,
    version: str,
    contract_tests: bool,
) -> None:
    """Generate OpenAPI spec from detected endpoints."""
    from testql.openapi_generator import ContractTestGenerator, OpenAPIGenerator

    target_path = Path(path)
    generator = OpenAPIGenerator(target_path)

    click.echo(f"🔍 Detecting endpoints in {target_path}...")
    spec = generator.generate(title=title, version=version)

    out_path = Path(output) if output else target_path / f"openapi.{format}"
    generator.save(out_path, format)
    click.echo(f"✅ OpenAPI spec saved: {out_path}")
    click.echo(f"   Endpoints: {len(spec.paths)}")
    click.echo(f"   Format: {format}")

    if contract_tests:
        test_file = out_path.parent / "testql-contracts.testql.toon.yaml"
        contract_gen = ContractTestGenerator(spec)
        contract_gen.generate_contract_tests(test_file)
        click.echo(f"✅ Contract tests saved: {test_file}")

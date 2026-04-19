"""CLI commands: testql generate, testql analyze — project test generation."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--output-dir", "-o", help="Output directory for generated tests")
@click.option("--analyze-only", is_flag=True, help="Only analyze, don't generate")
@click.option("--format", "fmt", type=click.Choice(["testql", "json"]), default="testql")
def generate(path: str, output_dir: str | None, analyze_only: bool, fmt: str) -> None:
    """Generate TestQL scenarios from project structure."""
    from testql.generator import TestGenerator, MultiProjectTestGenerator

    target_path = Path(path)

    if any((target_path / d).exists() for d in ["doql", "oql", "oqlos", "testql", "weboql", "www"]):
        click.echo(f"🔄 Analyzing workspace: {target_path}")
        gen = MultiProjectTestGenerator(target_path)
        profiles = gen.analyze_all()

        click.echo(f"📊 Discovered {len(profiles)} projects:")
        for name, profile in profiles.items():
            click.echo(f"  • {name}: {profile.project_type}")
            click.echo(f"    - Test patterns: {len(profile.test_patterns)}")
            click.echo(f"    - Config files: {len(profile.config)}")

        if analyze_only:
            return

        results = gen.generate_all()
        total = sum(len(files) for files in results.values())
        click.echo(f"\n✅ Generated {total} test files across {len(results)} projects")

        cross_file = gen.generate_cross_project_tests(target_path / "testql-scenarios")
        click.echo(f"🌐 Cross-project tests: {cross_file}")

    else:
        click.echo(f"🔄 Analyzing project: {target_path}")
        gen = TestGenerator(target_path)
        profile = gen.analyze()

        click.echo(f"📊 Project type: {profile.project_type}")
        click.echo(f"📊 Test patterns: {len(profile.test_patterns)}")
        click.echo(f"📊 Discovered files: {sum(len(v) for v in profile.discovered_files.values())}")

        if analyze_only:
            return

        out_dir = Path(output_dir) if output_dir else None
        generated = gen.generate_tests(out_dir)

        click.echo(f"\n✅ Generated {len(generated)} test files:")
        for f in generated:
            click.echo(f"  • {f}")

    sys.exit(0)


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
def analyze(path: str) -> None:
    """Analyze project structure and show testability report."""
    from testql.generator import TestGenerator

    target_path = Path(path)
    gen = TestGenerator(target_path)
    profile = gen.analyze()

    click.echo(f"\n📁 Project: {profile.name}")
    click.echo(f"📂 Path: {profile.root_path}")
    click.echo(f"🔧 Type: {profile.project_type}")
    click.echo("\n📊 Discovered Files:")

    for category, files in sorted(profile.discovered_files.items()):
        click.echo(f"  • {category}: {len(files)} files")

    click.echo(f"\n🧪 Test Patterns Found: {len(profile.test_patterns)}")
    for pattern in profile.test_patterns[:10]:
        click.echo(f"  • {pattern.name} ({pattern.pattern_type})")
    if len(profile.test_patterns) > 10:
        click.echo(f"  ... and {len(profile.test_patterns) - 10} more")

    _print_routes_section(profile)
    _print_scenarios_section(profile)


def _print_routes_section(profile) -> None:
    if not profile.config.get("discovered_routes"):
        return

    routes = profile.config["discovered_routes"]
    frameworks = profile.config.get("endpoint_frameworks", [])

    click.echo(f"\n🌐 API Routes Discovered: {len(routes)}")
    if frameworks:
        click.echo(f"   Detectors used: {', '.join(frameworks)}")

    routes_by_fw: dict[str, int] = {}
    routes_by_type: dict[str, int] = {}
    for route in routes:
        fw = route.get("framework", "unknown")
        et = route.get("endpoint_type", "rest")
        routes_by_fw[fw] = routes_by_fw.get(fw, 0) + 1
        routes_by_type[et] = routes_by_type.get(et, 0) + 1

    if routes_by_fw:
        click.echo("   By Framework:")
        for fw, count in sorted(routes_by_fw.items(), key=lambda x: -x[1]):
            click.echo(f"     • {fw}: {count} endpoints")

    if len(routes_by_type) > 1:
        click.echo("   By Type:")
        for et, count in routes_by_type.items():
            click.echo(f"     • {et}: {count}")

    click.echo("   Sample Endpoints:")
    for route in routes[:8]:
        fw = route.get("framework", "?")
        handler = route.get("handler", "")
        info = f"{route['method']} {route['path']}"
        if handler:
            info += f" → {handler}"
        click.echo(f"     • [{fw}] {info}")
    if len(routes) > 8:
        click.echo(f"     ... and {len(routes) - 8} more")


def _print_scenarios_section(profile) -> None:
    if not profile.config.get("scenario_patterns"):
        return
    scenarios = profile.config["scenario_patterns"]
    click.echo(f"\n⚙️ OQL/CQL Scenarios: {len(scenarios)}")
    for s in scenarios[:5]:
        click.echo(f"  • {s['name']}")

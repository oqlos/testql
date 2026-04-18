"""TestQL CLI — run .testql.toon.yaml scenarios from the command line."""

from __future__ import annotations

import sys
from pathlib import Path

import click


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """TestQL — Interface Query Language for Testing."""
    pass


@cli.command()
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
def run(file: str, url: str, dry_run: bool, output: str, quiet: bool) -> None:
    """Run a TestQL (.testql.toon.yaml) scenario."""
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


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--output-dir", "-o", help="Output directory for generated tests")
@click.option("--analyze-only", is_flag=True, help="Only analyze, don't generate")
@click.option("--format", "fmt", type=click.Choice(["testql", "json"]), default="testql")
def generate(path: str, output_dir: str | None, analyze_only: bool, fmt: str) -> None:
    """Generate TestQL scenarios from project structure."""
    from testql.generator import TestGenerator, MultiProjectTestGenerator
    from pathlib import Path

    target_path = Path(path)

    # Determine if single project or workspace
    if any((target_path / d).exists() for d in ['doql', 'oql', 'oqlos', 'testql', 'weboql', 'www']):
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

        # Generate cross-project tests
        cross_file = gen.generate_cross_project_tests(target_path / 'testql-scenarios')
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


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
def analyze(path: str) -> None:
    """Analyze project structure and show testability report."""
    from testql.generator import TestGenerator
    from pathlib import Path

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

    if profile.config.get('discovered_routes'):
        routes = profile.config['discovered_routes']
        frameworks = profile.config.get('endpoint_frameworks', [])

        click.echo(f"\n🌐 API Routes Discovered: {len(routes)}")
        if frameworks:
            click.echo(f"   Detectors used: {', '.join(frameworks)}")

        # Group by framework
        routes_by_fw = {}
        routes_by_type = {}
        for route in routes:
            fw = route.get('framework', 'unknown')
            et = route.get('endpoint_type', 'rest')
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

        # Show sample routes with handler info
        click.echo("   Sample Endpoints:")
        for route in routes[:8]:
            fw = route.get('framework', '?')
            handler = route.get('handler', '')
            summary = route.get('summary', '')
            info = f"{route['method']} {route['path']}"
            if handler:
                info += f" → {handler}"
            click.echo(f"     • [{fw}] {info}")
        if len(routes) > 8:
            click.echo(f"     ... and {len(routes) - 8} more")

    if profile.config.get('scenario_patterns'):
        scenarios = profile.config['scenario_patterns']
        click.echo(f"\n⚙️ OQL/CQL Scenarios: {len(scenarios)}")
        for s in scenarios[:5]:
            click.echo(f"  • {s['name']}")


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--framework", help="Filter by framework (fastapi, flask, django, express)")
@click.option("--type", "endpoint_type", help="Filter by type (rest, graphql, websocket)")
@click.option("--output", "-o", type=click.Path(), help="Save to file")
def endpoints(path: str, fmt: str, framework: str | None, endpoint_type: str | None, output: str | None) -> None:
    """List all detected API endpoints in a project."""
    from testql.endpoint_detector import UnifiedEndpointDetector
    from pathlib import Path
    import json
    import csv
    import io

    target_path = Path(path)
    detector = UnifiedEndpointDetector(target_path)
    eps = detector.detect_all()

    # Apply filters
    if framework:
        eps = [ep for ep in eps if ep.framework == framework]
    if endpoint_type:
        eps = [ep for ep in eps if ep.endpoint_type == endpoint_type]

    if not eps:
        click.echo("❌ No endpoints detected")
        sys.exit(1)

    # Format output
    if fmt == "json":
        data = [{
            "path": ep.path,
            "method": ep.method,
            "framework": ep.framework,
            "type": ep.endpoint_type,
            "handler": ep.handler_name,
            "file": str(ep.source_file.relative_to(target_path)) if ep.source_file else None,
            "line": ep.line_number,
            "summary": ep.summary,
        } for ep in eps]
        output_str = json.dumps(data, indent=2)

    elif fmt == "csv":
        output_buffer = io.StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(["method", "path", "framework", "type", "handler", "file", "line", "summary"])
        for ep in eps:
            writer.writerow([
                ep.method, ep.path, ep.framework, ep.endpoint_type,
                ep.handler_name or "",
                str(ep.source_file.relative_to(target_path)) if ep.source_file else "",
                ep.line_number,
                ep.summary or "",
            ])
        output_str = output_buffer.getvalue()

    else:  # table
        lines = []
        lines.append(f"{'Method':<8} {'Path':<40} {'Framework':<12} {'Handler':<30}")
        lines.append("-" * 90)
        for ep in eps:
            handler = ep.handler_name or "-"
            if len(handler) > 28:
                handler = handler[:25] + "..."
            path = ep.path if len(ep.path) < 38 else ep.path[:35] + "..."
            lines.append(f"{ep.method:<8} {path:<40} {ep.framework:<12} {handler:<30}")
        lines.append("")
        lines.append(f"Total: {len(eps)} endpoints (detectors: {', '.join(detector.detectors_used)})")
        output_str = "\n".join(lines)

    # Output
    if output:
        Path(output).write_text(output_str)
        click.echo(f"✅ Saved {len(eps)} endpoints to {output}")
    else:
        click.echo(output_str)


@cli.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--output", "-o", type=click.Path(), help="Output file (default: openapi.yaml)")
@click.option("--format", type=click.Choice(["yaml", "json"]), default="yaml", help="Output format")
@click.option("--title", help="API title (default: project name)")
@click.option("--version", default="1.0.0", help="API version")
@click.option("--contract-tests", is_flag=True, help="Also generate contract tests")
def openapi(path: str, output: str | None, format: str, title: str | None, version: str, contract_tests: bool) -> None:
    """Generate OpenAPI spec from detected endpoints."""
    from testql.openapi_generator import OpenAPIGenerator, ContractTestGenerator
    from pathlib import Path

    target_path = Path(path)
    generator = OpenAPIGenerator(target_path)

    click.echo(f"🔍 Detecting endpoints in {target_path}...")
    spec = generator.generate(title=title, version=version)

    # Determine output path
    if output:
        out_path = Path(output)
    else:
        out_path = target_path / f"openapi.{format}"

    generator.save(out_path, format)
    click.echo(f"✅ OpenAPI spec saved: {out_path}")
    click.echo(f"   Endpoints: {len(spec.paths)}")
    click.echo(f"   Format: {format}")

    # Generate contract tests if requested
    if contract_tests:
        test_file = out_path.parent / "testql-contracts.testql.toon.yaml"
        contract_gen = ContractTestGenerator(spec)
        contract_gen.generate_contract_tests(test_file)
        click.echo(f"✅ Contract tests saved: {test_file}")


@cli.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="Project path to initialize")
@click.option("--name", "-n", help="Project name (default: directory name)")
@click.option("--type", "-t", "project_type", type=click.Choice(["gui", "api", "mixed", "encoder", "all"]), default="all", help="Test types to setup")
def init(path: str, name: str | None, project_type: str) -> None:
    """Initialize TestQL project with templates and config."""
    from pathlib import Path

    target_path = Path(path).resolve()
    project_name = name or target_path.name

    # Create directories
    dirs = ["testql", "testql/fixtures", "testql/reports"]
    for d in dirs:
        (target_path / d).mkdir(parents=True, exist_ok=True)

    # Create testql.yaml config
    config_file = target_path / "testql.yaml"
    if not config_file.exists():
        config_content = f'''# TestQL Configuration
project:
  name: {project_name}
  base_url: http://localhost:8100
  api_url: http://localhost:8101
  encoder_url: http://localhost:8105

defaults:
  timeout: 30000
  wait: 500
  output: console

suites:
  smoke:
    - testql/test-gui-*.testql.toon.yaml
  regression:
    - testql/test-*.testql.toon.yaml
  api:
    - testql/test-api*.testql.toon.yaml

# Type-specific settings
types:
  gui:
    viewport: "1920x1080"
    headless: true
  api:
    timeout: 10000
  encoder:
    device: "default"
'''
        config_file.write_text(config_content)
        click.echo(f"✅ Created {config_file}")

    # Generate starter templates based on type
    templates_dir = target_path / "testql"

    if project_type in ("api", "all", "mixed"):
        api_template = templates_dir / "test-api-health.testql.toon.yaml"
        if not api_template.exists():
            api_template.write_text('''meta:
  name: "API Health Check"
  type: api
  tags: [smoke, api, health]

SET api_url = "${api_url:-http://localhost:8101}"

# Health check
GET "${api_url}/api/health"
ASSERT_STATUS 200
ASSERT_JSON path="status" equals="ok"

LOG "API health check passed"
''')
            click.echo(f"✅ Created {api_template.name}")

    if project_type in ("gui", "all", "mixed"):
        gui_template = templates_dir / "test-gui-navigation.testql.toon.yaml"
        if not gui_template.exists():
            gui_template.write_text('''meta:
  name: "GUI Navigation Test"
  type: gui
  tags: [smoke, gui, navigation]

SET base_url = "${base_url:-http://localhost:8100}"

# Navigate to home
NAVIGATE "${base_url}/"
WAIT 500

# Check main elements
ASSERT_TITLE "contains" "Home"
ASSERT_SELECTOR "nav" "exists"

LOG "Navigation test passed"
''')
            click.echo(f"✅ Created {gui_template.name}")

    if project_type in ("encoder", "all", "mixed"):
        encoder_template = templates_dir / "test-encoder-basic.testql.toon.yaml"
        if not encoder_template.exists():
            encoder_template.write_text('''meta:
  name: "Encoder Basic Test"
  type: encoder
  tags: [smoke, encoder]

SET encoder_url = "${encoder_url:-http://localhost:8105}"

# Encoder operations
ENCODER_ON
WAIT 200
ENCODER_STATUS
ASSERT_ENCODER "active"
ENCODER_OFF

LOG "Encoder test passed"
''')
            click.echo(f"✅ Created {encoder_template.name}")

    click.echo(f"\n🎯 TestQL initialized in {target_path}")
    click.echo(f"   Project: {project_name}")
    click.echo(f"   Types: {project_type}")
    click.echo("\nNext steps:")
    click.echo("  testql create <name> --type <type>  # Create new test")
    click.echo("  testql suite smoke                    # Run smoke tests")
    click.echo("  testql list                           # List all tests")


@cli.command()
@click.argument("name")
@click.option("--type", "-t", "test_type", type=click.Choice(["gui", "api", "mixed", "encoder", "performance", "workflow"]), default="gui", help="Test type template")
@click.option("--module", "-m", help="Target module (e.g., connect-id, connect-test)")
@click.option("--output", "-o", type=click.Path(), help="Output directory (default: testql/)")
@click.option("--force", is_flag=True, help="Overwrite existing file")
def create(name: str, test_type: str, module: str | None, output: str | None, force: bool) -> None:
    """Create new test file from template."""
    from pathlib import Path

    # Determine output path
    if output:
        out_dir = Path(output)
    else:
        out_dir = Path("testql")

    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{name}.testql.toon.yaml"
    filepath = out_dir / filename

    if filepath.exists() and not force:
        click.echo(f"❌ File exists: {filepath}")
        click.echo("   Use --force to overwrite")
        sys.exit(1)

    # Build test content based on type
    meta_module = module or "general"
    tags = [test_type, meta_module, "auto-generated"]

    if test_type == "gui":
        route = f"/{meta_module.replace('-', '/')}" if meta_module != "general" else "/"
        content = f'''meta:
  name: "GUI Test: {name}"
  type: gui
  module: {meta_module}
  tags: {tags}
  generated: true

SET base_url = "${{base_url:-http://localhost:8100}}"
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# Setup
NAVIGATE "${{base_url}}{route}"
WAIT 500

# Main test steps
# TODO: Add your test steps here
# Examples:
# CLICK "#button-id"
# INPUT "#input-field" "test value"
# ASSERT_SELECTOR ".result" "exists"

# Cleanup
LOG "GUI test {name} completed"
'''

    elif test_type == "api":
        content = f'''meta:
  name: "API Test: {name}"
  type: api
  module: {meta_module}
  tags: {tags}
  generated: true

SET api_url = "${{api_url:-http://localhost:8101}}"

# Setup
# TODO: Set up test data if needed
# SET test_id = "test-${{TIMESTAMP}}"

# API calls
# Examples:
# GET "${{api_url}}/api/{meta_module}/list"
# ASSERT_STATUS 200
# CAPTURE item_id FROM "data[0].id"
#
# POST "${{api_url}}/api/{meta_module}/create" {{"name": "test"}}
# ASSERT_STATUS 201

# Cleanup
LOG "API test {name} completed"
'''

    elif test_type == "mixed":
        content = f'''meta:
  name: "Mixed Test: {name}"
  type: mixed
  module: {meta_module}
  tags: {tags}
  generated: true

SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# === API Setup ===
# POST "${{api_url}}/api/{meta_module}/create" {{"test": true}}
# CAPTURE entity_id FROM "id"
# ASSERT_STATUS 201

# === GUI Verification ===
NAVIGATE "${{base_url}}/{meta_module}/detail/${{entity_id}}"
WAIT 300
ASSERT_SELECTOR "[data-testid='detail-view']" "exists"

# === Encoder Interaction (if applicable) ===
# ENCODER_ON
# ENCODER_FOCUS col1
# ENCODER_CLICK

# === API Cleanup ===
# DELETE "${{api_url}}/api/{meta_module}/${{entity_id}}"
# ASSERT_STATUS 200

LOG "Mixed test {name} completed"
'''

    elif test_type == "performance":
        content = f'''meta:
  name: "Performance Test: {name}"
  type: performance
  module: {meta_module}
  tags: {tags + ["performance"]}
  generated: true

SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"

# Warmup
NAVIGATE "${{base_url}}/{meta_module}"
WAIT 1000

# Measure load time
TIMESTAMP start_load
NAVIGATE "${{base_url}}/{meta_module}"
WAIT_FOR_SELECTOR "[data-loaded='true']" timeout=5000
TIMESTAMP end_load

CALC load_time = end_load - start_load
LOG "Load time: ${{load_time}}ms"

# API performance
TIMESTAMP start_api
GET "${{api_url}}/api/{meta_module}/list"
TIMESTAMP end_api
CALC api_time = end_api - start_api

ASSERT ${{load_time}} < 2000 "Page load should be under 2s"
ASSERT ${{api_time}} < 500 "API call should be under 500ms"

LOG "Performance test {name} completed"
'''

    elif test_type == "workflow":
        content = f'''meta:
  name: "Workflow Test: {name}"
  type: workflow
  module: {meta_module}
  tags: {tags}
  generated: true

SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"

workflow:
  name: "{name}"
  steps:
    - name: "Step 1: Setup"
      action: SETUP
      # TODO: Define setup

    - name: "Step 2: Action"
      action: EXECUTE
      # TODO: Define main action

    - name: "Step 3: Verify"
      action: ASSERT
      # TODO: Define verification

    - name: "Step 4: Cleanup"
      action: TEARDOWN
      # TODO: Define cleanup

LOG "Workflow test {name} completed"
'''

    else:  # encoder
        content = f'''meta:
  name: "Encoder Test: {name}"
  type: encoder
  module: {meta_module}
  tags: {tags}
  generated: true

SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# Setup
ENCODER_ON
WAIT 200
ENCODER_STATUS
ASSERT_ENCODER "active"

# Test steps
# Examples:
# ENCODER_FOCUS col1
# ENCODER_SCROLL 3
# ENCODER_CLICK
# ENCODER_DBLCLICK
# ENCODER_SCROLL -2

# Cleanup
ENCODER_OFF
LOG "Encoder test {name} completed"
'''

    filepath.write_text(content)
    click.echo(f"✅ Created {filepath}")
    click.echo(f"   Type: {test_type}")
    if module:
        click.echo(f"   Module: {module}")
    click.echo("\nEdit the file to add your test steps.")


@cli.command()
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
def suite(suite_name: str | None, base_path: str, pattern: str | None, tags: tuple, test_types: tuple, parallel: int, fail_fast: bool, output: str, report: str | None, url: str | None) -> None:
    """Run test suite(s) — predefined or custom pattern."""
    from pathlib import Path
    import fnmatch
    import json
    from testql.interpreter import IqlInterpreter

    target_path = Path(base_path)
    config_file = target_path / "testql.yaml" if target_path.is_dir() else target_path.parent / "testql.yaml"

    # Load config if exists
    config = {}
    if config_file.exists():
        import yaml
        config = yaml.safe_load(config_file.read_text())

    # Determine test files to run
    test_files = []

    def find_files(base_dir: Path, file_pattern: str) -> list:
        """Find files matching pattern using fnmatch."""
        import os
        matched = []
        if not base_dir.exists():
            return matched

        # Check if pattern has path components
        if '/' in file_pattern or '\\' in file_pattern:
            # Pattern has path - join with base and use rglob
            pattern_parts = file_pattern.replace('\\', '/').split('/')
            search_dir = base_dir
            for part in pattern_parts[:-1]:
                search_dir = search_dir / part
            file_only_pattern = pattern_parts[-1]
        else:
            # Pattern is just filename
            search_dir = base_dir
            file_only_pattern = file_pattern

        if not search_dir.exists():
            return matched

        for root, dirs, files in os.walk(search_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, file_only_pattern):
                    matched.append(Path(root) / filename)
        return matched

    if suite_name and config.get("suites", {}).get(suite_name):
        # Use predefined suite from config
        suite_patterns = config["suites"][suite_name]
        if isinstance(suite_patterns, str):
            suite_patterns = [suite_patterns]
        for p in suite_patterns:
            base = target_path if target_path.is_dir() else target_path.parent
            matched = find_files(base, str(p))
            test_files.extend(matched)
    elif pattern:
        # Use provided pattern
        base = target_path if target_path.is_dir() else target_path.parent
        pattern_str = str(pattern)
        test_files = find_files(base, pattern_str)
    elif target_path.is_file():
        # Single file
        test_files = [target_path]
    else:
        # Default: find all test files (backward compatible with old and new structure)
        test_dirs = [
            target_path / "testql",                    # New structure
            target_path / "testql/scenarios/tests",    # Old structure (backward compat)
            target_path / "tests",
            target_path,
        ]
        for td in test_dirs:
            if td.exists():
                test_files.extend(find_files(td, "*.testql.toon.yaml"))
                test_files.extend(find_files(td, "*.testtoon"))
                test_files.extend(find_files(td, "*.iql"))

    # Remove duplicates and filter
    seen = set()
    unique_files = []
    for f in test_files:
        f_str = str(f)
        if f_str not in seen:
            seen.add(f_str)
            unique_files.append(f)
    test_files = unique_files
    test_files = [f for f in test_files if f.exists()]

    if not test_files:
        click.echo("❌ No test files found")
        sys.exit(1)

    click.echo(f"🧪 Running {len(test_files)} test(s)\n")

    # Run tests
    results = []
    all_passed = True

    for i, test_file in enumerate(test_files, 1):
        click.echo(f"[{i}/{len(test_files)}] {test_file.name}")

        interp = IqlInterpreter(
            api_url=url or config.get("defaults", {}).get("api_url", "http://localhost:8101"),
            quiet=(output != "console"),
            include_paths=[str(test_file.parent), "."],
        )

        try:
            result = interp.run_file(str(test_file))
            results.append({
                "file": str(test_file),
                "name": test_file.name,
                "ok": result.ok,
                "passed": result.passed,
                "failed": result.failed,
                "duration_ms": result.duration_ms,
                "errors": result.errors,
            })

            status = "✅ PASS" if result.ok else "❌ FAIL"
            click.echo(f"    {status} ({result.passed} passed, {result.failed} failed, {result.duration_ms:.0f}ms)")

            if not result.ok:
                all_passed = False
                if fail_fast:
                    click.echo("\n⚡ Fail-fast enabled, stopping suite")
                    break

        except Exception as e:
            click.echo(f"    ❌ ERROR: {e}")
            results.append({"file": str(test_file), "name": test_file.name, "ok": False, "error": str(e)})
            all_passed = False
            if fail_fast:
                break

    # Summary
    total_passed = sum(r.get("passed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    total_duration = sum(r.get("duration_ms", 0) for r in results)

    click.echo(f"\n{'='*50}")
    click.echo(f"Results: {len([r for r in results if r.get('ok')])}/{len(results)} files passed")
    click.echo(f"Tests: {total_passed} passed, {total_failed} failed")
    click.echo(f"Duration: {total_duration:.0f}ms")

    # Generate report if requested
    if report or output in ("json", "junit", "html"):
        report_data = {
            "suite": suite_name or "custom",
            "timestamp": str(Path().stat().st_mtime if False else "now"),
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

        report_file = report or f"testql-report.{output}"

        if output == "json":
            Path(report_file).write_text(json.dumps(report_data, indent=2))
        elif output == "junit":
            # Simple JUnit XML
            junit_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="TestQL" tests="{len(results)}" failures="{len([r for r in results if not r.get('ok')])}" time="{total_duration/1000:.3f}">
'''
            for r in results:
                junit_xml += f'  <testsuite name="{r["name"]}" tests="{r.get("passed", 0) + r.get("failed", 0)}" failures="{r.get("failed", 0)}" time="{r.get("duration_ms", 0)/1000:.3f}">\n'
                if r.get("errors"):
                    for e in r["errors"]:
                        junit_xml += f'    <failure message="{e}"/>\n'
                junit_xml += '  </testsuite>\n'
            junit_xml += '</testsuites>'
            Path(report_file).write_text(junit_xml)

        click.echo(f"📄 Report saved: {report_file}")

    sys.exit(0 if all_passed else 1)


@cli.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="Path to search for tests")
@click.option("--type", "test_type", type=click.Choice(["gui", "api", "mixed", "encoder", "performance", "all"]), default="all", help="Filter by type")
@click.option("--tag", help="Filter by tag")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "simple"]), default="table")
def list(path: str, test_type: str, tag: str | None, fmt: str) -> None:
    """List all available tests with metadata."""
    from pathlib import Path
    import yaml
    import json

    target_path = Path(path)
    test_files = []

    # Search directories (backward compatible with old and new structure)
    search_dirs = [
        target_path / "testql",                    # New structure
        target_path / "testql/scenarios/tests",    # Old structure (backward compat)
        target_path / "tests",
        target_path,
    ]

    for sd in search_dirs:
        if sd.exists():
            test_files.extend(sd.glob("*.testql.toon.yaml"))
            test_files.extend(sd.glob("*.testtoon"))

    # Parse and filter
    tests = []
    for tf in sorted(set(test_files)):
        try:
            content = tf.read_text()
            # Extract meta section
            meta = {"name": tf.stem, "type": "unknown", "tags": []}

            if "meta:" in content:
                # Simple YAML parsing for meta block
                lines = content.split("\n")
                in_meta = False
                meta_lines = []
                for line in lines:
                    if line.strip() == "meta:":
                        in_meta = True
                        continue
                    if in_meta:
                        if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                            break
                        meta_lines.append(line)

                if meta_lines:
                    try:
                        parsed = yaml.safe_load("meta:\n" + "\n".join(meta_lines))
                        if parsed and "meta" in parsed:
                            meta.update(parsed["meta"])
                    except Exception:
                        pass

            # Filter by type
            if test_type != "all" and meta.get("type") != test_type:
                continue

            # Filter by tag
            if tag and tag not in meta.get("tags", []):
                continue

            tests.append({
                "file": str(tf.relative_to(target_path)),
                "name": meta.get("name", tf.stem),
                "type": meta.get("type", "unknown"),
                "tags": meta.get("tags", []),
            })
        except Exception:
            pass

    # Output
    if fmt == "json":
        print(json.dumps(tests, indent=2))


@cli.command()
@click.option("--toon-path", type=click.Path(), help="Path to toon test files")
@click.option("--doql-path", type=click.Path(), help="Path to doql LESS file (app.doql.less)")
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="text", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
def echo(toon_path: str | None, doql_path: str | None, fmt: str, output: str | None) -> None:
    """Generate AI-friendly project metadata echo from toon tests and doql model."""
    from pathlib import Path
    import json
    from testql.echo_schemas import ProjectEcho
    from testql.toon_parser import parse_toon_file
    from testql.doql_parser import parse_doql_file

    project_echo = ProjectEcho()

    # Parse toon tests if provided
    if toon_path:
        toon_file = Path(toon_path)
        if toon_file.is_dir():
            # Find toon files in directory
            toon_files = list(toon_file.glob("*.testql.toon.yaml")) + list(toon_file.glob("*.testtoon"))
            if toon_files:
                for tf in toon_files:
                    contract = parse_toon_file(tf)
                    # Merge contracts
                    project_echo.api_contract.endpoints.extend(contract.endpoints)
                    project_echo.api_contract.asserts.extend(contract.asserts)
                    if contract.base_url and not project_echo.api_contract.base_url:
                        project_echo.api_contract.base_url = contract.base_url
                click.echo(f"📄 Parsed {len(toon_files)} toon file(s)")
        elif toon_file.exists():
            contract = parse_toon_file(toon_file)
            project_echo.api_contract = contract
            click.echo(f"📄 Parsed toon file: {toon_file}")
        else:
            click.echo(f"⚠️  Toon path not found: {toon_path}")

    # Parse doql LESS if provided
    if doql_path:
        doql_file = Path(doql_path)
        if doql_file.exists():
            system_model = parse_doql_file(doql_file)
            project_echo.system_model = system_model
            click.echo(f"📄 Parsed doql file: {doql_file}")
        else:
            click.echo(f"⚠️  Doql path not found: {doql_path}")

    # Generate output
    if fmt == "json":
        output_str = json.dumps(project_echo.to_dict(), indent=2)
    else:
        output_str = project_echo.to_text()

    # Save or print
    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        click.echo(f"✅ Saved echo to {output}")
    else:
        click.echo("\n" + output_str)


@cli.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="Path to watch")
@click.option("--pattern", default="*.testql.toon.yaml", help="File pattern to watch")
@click.option("--command", "-c", default="run", type=click.Choice(["run", "suite"]), help="Command to run on change")
@click.option("--debounce", default=1.0, help="Debounce time in seconds")
def watch(path: str, pattern: str, command: str, debounce: float) -> None:
    """Watch for file changes and re-run tests automatically."""
    from pathlib import Path
    import time

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        click.echo("❌ watchdog not installed. Install with: pip install watchdog")
        sys.exit(1)

    target_path = Path(path).resolve()
    click.echo(f"👁️  Watching {target_path}/{pattern}")
    click.echo(f"   Debounce: {debounce}s")
    click.echo("   Press Ctrl+C to stop\n")

    last_run = 0

    class TestHandler(FileSystemEventHandler):
        def on_modified(self, event):
            nonlocal last_run
            if event.is_directory:
                return
            if not event.src_path.endswith(pattern.replace("*", "")):
                return

            now = time.time()
            if now - last_run < debounce:
                return
            last_run = now

            click.echo(f"📝 Changed: {Path(event.src_path).name}")
            click.echo("   Re-running...")

            # Run command
            import subprocess
            try:
                if command == "run":
                    result = subprocess.run(
                        ["testql", "run", event.src_path],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                else:
                    result = subprocess.run(
                        ["testql", "suite", "--pattern", pattern],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                if result.returncode == 0:
                    click.echo("   ✅ Tests passed")
                else:
                    click.echo("   ❌ Tests failed")
                    if result.stdout:
                        click.echo(result.stdout[-500:])  # Last 500 chars
            except Exception as e:
                click.echo(f"   ❌ Error: {e}")

    observer = Observer()
    observer.schedule(TestHandler(), str(target_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        click.echo("\n👋 Stopped watching")

    observer.join()


def main():
    """Entry point for console script."""
    cli()


if __name__ == "__main__":
    main()

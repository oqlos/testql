"""CLI commands: init, create, watch, from_sumd, report, echo — miscellaneous testql commands."""

from __future__ import annotations

import sys
from pathlib import Path

import click

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

_API_TEMPLATE = '''\
meta:
  name: "API Health Check"
  type: api
  tags: [smoke, api, health]

SET api_url = "${api_url:-http://localhost:8101}"

# Health check
GET "${api_url}/api/health"
ASSERT_STATUS 200
ASSERT_JSON path="status" equals="ok"

LOG "API health check passed"
'''

_GUI_TEMPLATE = '''\
meta:
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
'''

_ENCODER_TEMPLATE = '''\
meta:
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
'''


def _build_test_content(test_type: str, name: str, meta_module: str, tags: list) -> str:
    if test_type == "gui":
        route = f"/{meta_module.replace('-', '/')}" if meta_module != "general" else "/"
        return f'''\
meta:
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

# Cleanup
LOG "GUI test {name} completed"
'''

    if test_type == "api":
        return f'''\
meta:
  name: "API Test: {name}"
  type: api
  module: {meta_module}
  tags: {tags}
  generated: true

SET api_url = "${{api_url:-http://localhost:8101}}"

# API calls
# GET "${{api_url}}/api/{meta_module}/list"
# ASSERT_STATUS 200

# Cleanup
LOG "API test {name} completed"
'''

    if test_type == "mixed":
        return f'''\
meta:
  name: "Mixed Test: {name}"
  type: mixed
  module: {meta_module}
  tags: {tags}
  generated: true

SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# === GUI Verification ===
NAVIGATE "${{base_url}}/{meta_module}/detail/${{entity_id}}"
WAIT 300
ASSERT_SELECTOR "[data-testid='detail-view']" "exists"

LOG "Mixed test {name} completed"
'''

    if test_type == "performance":
        return f'''\
meta:
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

ASSERT ${{load_time}} < 2000 "Page load should be under 2s"

LOG "Performance test {name} completed"
'''

    if test_type == "workflow":
        return f'''\
meta:
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

    - name: "Step 2: Action"
      action: EXECUTE

    - name: "Step 3: Verify"
      action: ASSERT

    - name: "Step 4: Cleanup"
      action: TEARDOWN

LOG "Workflow test {name} completed"
'''

    # encoder (default)
    return f'''\
meta:
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

# Cleanup
ENCODER_OFF
LOG "Encoder test {name} completed"
'''


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@click.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="Project path to initialize")
@click.option("--name", "-n", help="Project name (default: directory name)")
@click.option("--type", "-t", "project_type", type=click.Choice(["gui", "api", "mixed", "encoder", "all"]), default="all")
def init(path: str, name: str | None, project_type: str) -> None:
    """Initialize TestQL project with templates and config."""
    target_path = Path(path).resolve()
    project_name = name or target_path.name

    for d in ["testql", "testql/fixtures", "testql/reports"]:
        (target_path / d).mkdir(parents=True, exist_ok=True)

    config_file = target_path / "testql.yaml"
    if not config_file.exists():
        config_file.write_text(f'''\
# TestQL Configuration
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
''')
        click.echo(f"✅ Created {config_file}")

    templates_dir = target_path / "testql"

    if project_type in ("api", "all", "mixed"):
        tpl = templates_dir / "test-api-health.testql.toon.yaml"
        if not tpl.exists():
            tpl.write_text(_API_TEMPLATE)
            click.echo(f"✅ Created {tpl.name}")

    if project_type in ("gui", "all", "mixed"):
        tpl = templates_dir / "test-gui-navigation.testql.toon.yaml"
        if not tpl.exists():
            tpl.write_text(_GUI_TEMPLATE)
            click.echo(f"✅ Created {tpl.name}")

    if project_type in ("encoder", "all", "mixed"):
        tpl = templates_dir / "test-encoder-basic.testql.toon.yaml"
        if not tpl.exists():
            tpl.write_text(_ENCODER_TEMPLATE)
            click.echo(f"✅ Created {tpl.name}")

    click.echo(f"\n🎯 TestQL initialized in {target_path}")
    click.echo(f"   Project: {project_name}")
    click.echo(f"   Types: {project_type}")
    click.echo("\nNext steps:")
    click.echo("  testql create <name> --type <type>  # Create new test")
    click.echo("  testql suite smoke                    # Run smoke tests")
    click.echo("  testql list                           # List all tests")


@click.command()
@click.argument("name")
@click.option("--type", "-t", "test_type", type=click.Choice(["gui", "api", "mixed", "encoder", "performance", "workflow"]), default="gui")
@click.option("--module", "-m", help="Target module")
@click.option("--output", "-o", type=click.Path(), help="Output directory (default: testql/)")
@click.option("--force", is_flag=True, help="Overwrite existing file")
def create(name: str, test_type: str, module: str | None, output: str | None, force: bool) -> None:
    """Create new test file from template."""
    out_dir = Path(output) if output else Path("testql")
    out_dir.mkdir(parents=True, exist_ok=True)

    filepath = out_dir / f"{name}.testql.toon.yaml"
    if filepath.exists() and not force:
        click.echo(f"❌ File exists: {filepath}")
        click.echo("   Use --force to overwrite")
        sys.exit(1)

    meta_module = module or "general"
    tags = [test_type, meta_module, "auto-generated"]
    content = _build_test_content(test_type, name, meta_module, tags)

    filepath.write_text(content)
    click.echo(f"✅ Created {filepath}")
    click.echo(f"   Type: {test_type}")
    if module:
        click.echo(f"   Module: {module}")
    click.echo("\nEdit the file to add your test steps.")


@click.command()
@click.option("--path", "-p", type=click.Path(), default=".", help="Path to watch")
@click.option("--pattern", default="*.testql.toon.yaml", help="File pattern to watch")
@click.option("--command", "-c", default="run", type=click.Choice(["run", "suite"]))
@click.option("--debounce", default=1.0, help="Debounce time in seconds")
def watch(path: str, pattern: str, command: str, debounce: float) -> None:
    """Watch for file changes and re-run tests automatically."""
    import time

    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
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

            import subprocess
            try:
                if command == "run":
                    result = subprocess.run(
                        ["testql", "run", event.src_path],
                        capture_output=True, text=True, timeout=60,
                    )
                else:
                    result = subprocess.run(
                        ["testql", "suite", "--pattern", pattern],
                        capture_output=True, text=True, timeout=120,
                    )
                if result.returncode == 0:
                    click.echo("   ✅ Tests passed")
                else:
                    click.echo("   ❌ Tests failed")
                    if result.stdout:
                        click.echo(result.stdout[-500:])
            except Exception as exc:
                click.echo(f"   ❌ Error: {exc}")

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


@click.command()
@click.argument("sumd_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output testql file")
@click.option("--dry-run", is_flag=True, help="Print scenario without saving")
def from_sumd(sumd_file: str, output: str | None, dry_run: bool) -> None:
    """Generate TestQL scenarios from SUMD.md documentation."""
    from testql.sumd_parser import SumdParser

    sumd_path = Path(sumd_file)
    parser = SumdParser()

    click.echo(f"📄 Parsing SUMD: {sumd_path}")
    doc = parser.parse_file(sumd_path)

    click.echo(f"   Project: {doc.metadata.name} ({doc.metadata.version})")
    click.echo(f"   Interfaces: {len(doc.interfaces)}")
    click.echo(f"   Workflows: {len(doc.workflows)}")
    click.echo(f"   Scenarios: {len(doc.testql_scenarios)}")

    scenario_content = parser.generate_testql_scenarios(doc)

    if dry_run:
        click.echo("\n📋 Generated TestQL scenario:\n")
        click.echo(scenario_content)
        return

    out_path = Path(output) if output else sumd_path.parent / f"{doc.metadata.name}-from-sumd.testql.toon.yaml"
    out_path.write_text(scenario_content, encoding="utf-8")
    click.echo(f"✅ Saved TestQL scenario: {out_path}")


@click.command()
@click.argument("data_json", type=click.Path(exists=True), required=False)
@click.option("--output", "-o", type=click.Path(), help="Output HTML file (default: report.html)")
@click.option("--example", is_flag=True, help="Generate example report with dummy data")
def report(data_json: str | None, output: str | None, example: bool) -> None:
    """Generate HTML report from test data.json."""
    import json

    from testql.report_generator import generate_report

    out_path = Path(output) if output else Path("report.html")

    if example:
        example_data = {
            "suite_name": "Example Test Suite",
            "total": 5,
            "passed": 3,
            "failed": 1,
            "skipped": 1,
            "duration_ms": 2450,
            "tests": [
                {"name": "test_health_check", "status": "passed", "duration_ms": 120, "assertions": 2, "failures": []},
                {"name": "test_user_list", "status": "passed", "duration_ms": 340, "assertions": 4, "failures": []},
                {"name": "test_user_create", "status": "passed", "duration_ms": 560, "assertions": 5, "failures": []},
                {"name": "test_auth_fail", "status": "failed", "duration_ms": 890, "assertions": 3, "failures": ["Expected 401, got 200"]},
                {"name": "test_delete_user", "status": "skipped", "duration_ms": 0, "assertions": 0, "failures": []},
            ],
        }
        data_file = Path("/tmp/example_data.json")
        data_file.write_text(json.dumps(example_data))
        result = generate_report(data_file, out_path)
        click.echo(f"✅ Example report generated: {result}")
        click.echo(f"   Open in browser: file://{result.absolute()}")
        return

    if not data_json:
        click.echo("❌ Error: Provide data.json file or use --example")
        sys.exit(1)

    result = generate_report(Path(data_json), out_path)
    click.echo(f"✅ Report generated: {result}")
    click.echo(f"   Open in browser: file://{result.absolute()}")


@click.command()
@click.option("--toon-path", type=click.Path(), help="Path to toon test files")
@click.option("--doql-path", type=click.Path(), help="Path to doql LESS file (app.doql.less)")
@click.option("--format", "fmt", type=click.Choice(["json", "text", "sumd"]), default="text")
@click.option("--output", "-o", type=click.Path(), help="Save output to file")
@click.option("--project-path", type=click.Path(), default=".", help="Project path for sumd generation")
def echo(
    toon_path: str | None,
    doql_path: str | None,
    fmt: str,
    output: str | None,
    project_path: str,
) -> None:
    """Generate AI-friendly project metadata echo from toon tests and doql model."""
    import json
    import os

    from testql.doql_parser import parse_doql_file
    from testql.echo_schemas import ProjectEcho
    from testql.toon_parser import parse_toon_file

    project_echo = ProjectEcho()
    project_path_obj = Path(project_path)

    if toon_path:
        toon_file_path = Path(toon_path)
        if toon_file_path.is_dir():
            toon_files = [
                Path(root) / f
                for root, _dirs, files in os.walk(toon_file_path)
                for f in files
                if f.endswith(".testql.toon.yaml") or f.endswith(".testtoon")
            ]
            for tf in toon_files:
                contract = parse_toon_file(tf)
                project_echo.api_contract.endpoints.extend(contract.endpoints)
                project_echo.api_contract.asserts.extend(contract.asserts)
                if contract.base_url and not project_echo.api_contract.base_url:
                    project_echo.api_contract.base_url = contract.base_url
            click.echo(f"📄 Parsed {len(toon_files)} toon file(s)")
        elif toon_file_path.exists():
            project_echo.api_contract = parse_toon_file(toon_file_path)
            click.echo(f"📄 Parsed toon file: {toon_file_path}")
        else:
            click.echo(f"⚠️  Toon path not found: {toon_path}")

    if doql_path:
        doql_file_path = Path(doql_path)
        if doql_file_path.exists():
            project_echo.system_model = parse_doql_file(doql_file_path)
            click.echo(f"📄 Parsed doql file: {doql_file_path}")
        else:
            click.echo(f"⚠️  Doql path not found: {doql_path}")

    if fmt == "json":
        output_str = json.dumps(project_echo.to_dict(), indent=2)
    elif fmt == "sumd":
        from testql.sumd_generator import generate_sumd
        output_str = generate_sumd(project_echo, project_path_obj)
    else:
        output_str = project_echo.to_text()

    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        click.echo(f"✅ Saved echo to {output}")
    else:
        click.echo("\n" + output_str)

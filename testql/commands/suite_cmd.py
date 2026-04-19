"""CLI commands: testql suite, testql list — test suite execution and listing."""

from __future__ import annotations

import fnmatch
import os
import sys
from pathlib import Path

import click


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_files(base_dir: Path, file_pattern: str) -> list[Path]:
    """Find files matching *file_pattern* under *base_dir*."""
    matched: list[Path] = []
    if not base_dir.exists():
        return matched

    if "/" in file_pattern or "\\" in file_pattern:
        parts = file_pattern.replace("\\", "/").split("/")
        search_dir = base_dir
        for part in parts[:-1]:
            search_dir = search_dir / part
        file_only = parts[-1]
    else:
        search_dir = base_dir
        file_only = file_pattern

    if not search_dir.exists():
        return matched

    for root, _dirs, files in os.walk(search_dir):
        for filename in files:
            if fnmatch.fnmatch(filename, file_only):
                matched.append(Path(root) / filename)
    return matched


def _collect_test_files(
    target_path: Path,
    suite_name: str | None,
    pattern: str | None,
    config: dict,
) -> list[Path]:
    test_files: list[Path] = []

    if suite_name and config.get("suites", {}).get(suite_name):
        suite_patterns = config["suites"][suite_name]
        if isinstance(suite_patterns, str):
            suite_patterns = [suite_patterns]
        base = target_path if target_path.is_dir() else target_path.parent
        for p in suite_patterns:
            test_files.extend(_find_files(base, str(p)))

    elif pattern:
        base = target_path if target_path.is_dir() else target_path.parent
        test_files = _find_files(base, str(pattern))

    elif target_path.is_file():
        test_files = [target_path]

    else:
        test_dirs = [
            target_path / "testql",
            target_path / "testql/scenarios/tests",
            target_path / "tests",
            target_path,
        ]
        for td in test_dirs:
            if td.exists():
                test_files.extend(_find_files(td, "*.testql.toon.yaml"))
                test_files.extend(_find_files(td, "*.testtoon"))
                test_files.extend(_find_files(td, "*.iql"))

    seen: set[str] = set()
    unique: list[Path] = []
    for f in test_files:
        key = str(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return [f for f in unique if f.exists()]


def _run_single_file(test_file: Path, interp) -> dict:
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
        return {"file": str(test_file), "name": test_file.name, "ok": False, "error": str(exc)}


def _build_report_data(suite_name, results, total_passed, total_failed, total_duration) -> dict:
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


def _save_report(report_data: dict, report_file: str, output: str) -> None:
    import json

    if output == "json":
        Path(report_file).write_text(json.dumps(report_data, indent=2))
    elif output == "junit":
        results = report_data["results"]
        total_duration = report_data["summary"]["duration_ms"]
        junit_xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<testsuites name="TestQL" tests="{len(results)}"'
            f' failures="{len([r for r in results if not r.get("ok")])}"'
            f' time="{total_duration/1000:.3f}">\n'
        )
        for r in results:
            junit_xml += (
                f'  <testsuite name="{r["name"]}"'
                f' tests="{r.get("passed", 0) + r.get("failed", 0)}"'
                f' failures="{r.get("failed", 0)}"'
                f' time="{r.get("duration_ms", 0)/1000:.3f}">\n'
            )
            for e in r.get("errors", []):
                junit_xml += f'    <failure message="{e}"/>\n'
            junit_xml += "  </testsuite>\n"
        junit_xml += "</testsuites>"
        Path(report_file).write_text(junit_xml)

    click.echo(f"📄 Report saved: {report_file}")


def _print_summary(results: list[dict], total_passed: int, total_failed: int, total_duration: float) -> None:
    click.echo(f"\n{'='*50}")
    click.echo(f"Results: {len([r for r in results if r.get('ok')])}/{len(results)} files passed")
    click.echo(f"Tests: {total_passed} passed, {total_failed} failed")
    click.echo(f"Duration: {total_duration:.0f}ms")


def _run_suite_files(
    test_files: list[Path],
    url: str,
    output: str,
    fail_fast: bool,
    config: dict,
) -> tuple[list[dict], bool]:
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
        result = _run_single_file(test_file, interp)
        results.append(result)
        if not result.get("ok"):
            all_passed = False
            if fail_fast:
                click.echo("\n⚡ Fail-fast enabled, stopping suite")
                break
    return results, all_passed


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

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
    import yaml

    target_path = Path(base_path)
    config_file = (
        target_path / "testql.yaml"
        if target_path.is_dir()
        else target_path.parent / "testql.yaml"
    )
    config: dict = {}
    if config_file.exists():
        config = yaml.safe_load(config_file.read_text()) or {}

    test_files = _collect_test_files(target_path, suite_name, pattern, config)
    if not test_files:
        click.echo("❌ No test files found")
        sys.exit(1)

    click.echo(f"🧪 Running {len(test_files)} test(s)\n")

    results, all_passed = _run_suite_files(
        test_files, url or "", output, fail_fast, config
    )

    total_passed = sum(r.get("passed", 0) for r in results)
    total_failed = sum(r.get("failed", 0) for r in results)
    total_duration = sum(r.get("duration_ms", 0) for r in results)

    _print_summary(results, total_passed, total_failed, total_duration)

    if report or output in ("json", "junit", "html"):
        report_data = _build_report_data(suite_name, results, total_passed, total_failed, total_duration)
        report_file = report or f"testql-report.{output}"
        _save_report(report_data, report_file, output)

    sys.exit(0 if all_passed else 1)


@click.command(name="list")
@click.option("--path", "-p", type=click.Path(), default=".", help="Path to search for tests")
@click.option("--type", "test_type", type=click.Choice(["gui", "api", "mixed", "encoder", "performance", "all"]), default="all", help="Filter by type")
@click.option("--tag", help="Filter by tag")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "simple"]), default="table")
def list_tests(path: str, test_type: str, tag: str | None, fmt: str) -> None:
    """List all available tests with metadata."""
    import json

    import yaml

    target_path = Path(path)
    raw_files: list[Path] = []

    search_dirs = [
        target_path / "testql",
        target_path / "testql/scenarios/tests",
        target_path / "tests",
        target_path,
    ]
    for sd in search_dirs:
        if sd.exists():
            raw_files.extend(sd.glob("*.testql.toon.yaml"))
            raw_files.extend(sd.glob("*.testtoon"))

    tests = []
    for tf in sorted(set(raw_files)):
        meta = _parse_meta(tf, yaml)
        if test_type != "all" and meta.get("type") != test_type:
            continue
        if tag and tag not in meta.get("tags", []):
            continue
        tests.append({
            "file": str(tf.relative_to(target_path)),
            "name": meta.get("name", tf.stem),
            "type": meta.get("type", "unknown"),
            "tags": meta.get("tags", []),
        })

    if not tests:
        click.echo("No test files found.")
        return

    if fmt == "json":
        print(json.dumps(tests, indent=2))
    elif fmt == "simple":
        for t in tests:
            click.echo(t["file"])
    else:  # table
        click.echo(f"{'File':<55} {'Type':<14} {'Tags'}")
        click.echo("-" * 80)
        for t in tests:
            tags_str = ", ".join(t["tags"]) if t["tags"] else "-"
            click.echo(f"{t['file']:<55} {t['type']:<14} {tags_str}")
        click.echo(f"\n{len(tests)} test file(s) found.")


def _parse_meta(tf: Path, yaml) -> dict:
    meta: dict = {"name": tf.stem, "type": "unknown", "tags": []}
    try:
        content = tf.read_text()

        # Handle TestTOON header format: # SCENARIO: ..., # TYPE: ...
        if content.startswith("# SCENARIO:") or "# TYPE:" in content[:200]:
            for line in content.splitlines()[:10]:
                if line.startswith("# SCENARIO:"):
                    meta["name"] = line[len("# SCENARIO:"):].strip()
                elif line.startswith("# TYPE:"):
                    meta["type"] = line[len("# TYPE:"):].strip()
            return meta

        if "meta:" not in content:
            return meta

        lines = content.split("\n")
        in_meta = False
        meta_lines: list[str] = []
        for line in lines:
            if line.strip() == "meta:":
                in_meta = True
                continue
            if in_meta:
                if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                    break
                meta_lines.append(line)

        if meta_lines:
            parsed = yaml.safe_load("meta:\n" + "\n".join(meta_lines))
            if parsed and "meta" in parsed:
                meta.update(parsed["meta"])
    except Exception:
        pass
    return meta

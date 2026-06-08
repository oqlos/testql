"""CLI command: testql run — execute file(s) in .testql.toon.yaml format."""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import click


def _resolve_input_paths(spec: str) -> list[Path]:
    p = Path(spec)
    if p.exists() and p.is_file():
        return [p]

    if p.exists() and p.is_dir():
        files = sorted(p.rglob("*.testql.toon.yaml"))
        if files:
            return files
        raise click.ClickException(f"No '.testql.toon.yaml' files found in directory: {spec}")

    matches = sorted(Path(m) for m in glob.glob(spec, recursive=True))
    files = [m for m in matches if m.is_file()]
    if files:
        return files

    raise click.ClickException(
        "Invalid input for FILE: expected an existing file, directory, or glob pattern "
        f"matching '.testql.toon.yaml' files. Got: {spec!r}"
    )


def _run_nlp2env(path: Path, dry_run: bool) -> object:
    import os

    from testql.nlp2env.runner import Nlp2EnvRunner

    return Nlp2EnvRunner(
        example_dir=path.parent,
        dry_run=dry_run,
        skip_llm=os.getenv("NLP2ENV_SKIP_LLM", "").lower() in {"1", "true", "yes"},
        only_llm=os.getenv("NLP2ENV_LLM_ONLY", "").lower() in {"1", "true", "yes"},
    ).run_file(path)


def _is_nlp2env_scenario(path: Path) -> bool:
    from testql.adapters.nlp2env import Nlp2EnvAdapter

    adapter = Nlp2EnvAdapter()
    return adapter.detect(path).matches or adapter.detect(path.read_text(encoding="utf-8")).matches


def _run_single(path: Path, url: str, dry_run: bool, quiet: bool, timeout: int | None):
    if _is_nlp2env_scenario(path):
        return _run_nlp2env(path, dry_run)

    from testql.interpreter import OqlInterpreter

    source = path.read_text(encoding="utf-8")
    interp = OqlInterpreter(
        api_url=url,
        dry_run=dry_run,
        quiet=quiet,
        include_paths=[str(path.parent), "."],
        timeout_ms=timeout,
    )
    return interp.run(source, path.name)


def _emit_single_json(result) -> None:
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


def _emit_multi_json(results: list[tuple[Path, object]]) -> None:
    runs = []
    passed_files = 0
    failed_files = 0
    for path, result in results:
        ok = bool(result.ok)
        if ok:
            passed_files += 1
        else:
            failed_files += 1
        runs.append(
            {
                "file": str(path),
                "source": result.source,
                "ok": ok,
                "passed": result.passed,
                "failed": result.failed,
                "steps": len(result.steps),
                "duration_ms": round(result.duration_ms, 1),
                "errors": result.errors,
                "warnings": result.warnings,
            }
        )

    print(
        json.dumps(
            {
                "ok": failed_files == 0,
                "files": len(results),
                "passed_files": passed_files,
                "failed_files": failed_files,
                "runs": runs,
            },
            indent=2,
        )
    )


def _maybe_planfile(result, filename: str, planfile: bool) -> None:
    if result.ok or not planfile:
        return

    from testql.base import StepStatus
    from testql.integrations.planfile_hook import create_test_failure_ticket

    error_msgs = []
    for step in result.steps:
        if step.status in (StepStatus.FAILED, StepStatus.ERROR):
            msg = f"`{step.name}`"
            if step.message:
                msg += f": {step.message}"
            error_msgs.append(msg)

    for err in result.errors:
        err_str = str(err)
        if not any(err_str in m for m in error_msgs):
            error_msgs.append(err_str)

    create_test_failure_ticket(error_msgs, filename)


@click.command()
@click.argument("files", nargs=-1, required=True, type=str)
@click.option("--url", default="http://localhost:8101", help="Base API URL")
@click.option("--dry-run", is_flag=True, help="Parse and validate without executing")
@click.option(
    "--output",
    type=click.Choice(["console", "json"]),
    default="console",
    help="Output format",
)
@click.option("--quiet", is_flag=True, help="Suppress step-by-step output")
@click.option("--planfile", is_flag=True, help="Auto-create tickets for failures via planfile")
@click.option("--timeout", type=int, default=None, help="Global timeout in milliseconds for operations")
def run(files: tuple[str, ...], url: str, dry_run: bool, output: str, quiet: bool, planfile: bool, timeout: int | None) -> None:
    """Run TestQL scenario(s): file(s), directory(ies), or glob pattern(s)."""
    paths_by_key: dict[str, Path] = {}
    for spec in files:
        for path in _resolve_input_paths(spec):
            paths_by_key[str(path.resolve())] = path
    paths = [paths_by_key[k] for k in sorted(paths_by_key.keys())]
    results = [(path, _run_single(path, url, dry_run, quiet, timeout)) for path in paths]

    for path, result in results:
        _maybe_planfile(result, path.name, planfile)

    if output == "json":
        if len(results) == 1:
            _emit_single_json(results[0][1])
        else:
            _emit_multi_json(results)

    all_ok = all(result.ok for _, result in results)
    sys.exit(0 if all_ok else 1)

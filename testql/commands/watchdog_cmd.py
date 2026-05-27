"""CLI command: testql watchdog — continuous multi-scenario runner with Prometheus metrics.

Runs N scenarios in round-robin, exposes /metrics on a configurable port,
and POSTs failures to a webhook (e.g. healing-webhook for LLM-ready ticket creation).

Usage examples:

    # Single scenario, 60s loop
    testql watchdog scenarios/realtime-health.testql.toon.yaml

    # Multiple scenarios, 30s interval, custom webhook
    testql watchdog scenarios/*.testql.toon.yaml --interval 30 \
        --webhook http://healing-webhook:8810/probe-failure

    # Directory mode (discovers all .testql.toon.yaml files)
    testql watchdog ./scenarios/ --port 9101

Environment variables (override CLI flags):

    WATCHDOG_INTERVAL        default 60 (seconds between cycles)
    WATCHDOG_WEBHOOK_URL     default http://healing-webhook:8810/probe-failure
    WATCHDOG_METRICS_PORT    default 9101
    WATCHDOG_TIMEOUT         default (interval - 5) seconds per scenario
    WATCHDOG_BASE_URL        default http://localhost:8101
"""

from __future__ import annotations

import glob
import json
import logging
import os
import subprocess
import sys
import time
from itertools import cycle
from pathlib import Path
from typing import Iterator

import click

log = logging.getLogger("testql.watchdog")


def _discover_scenarios(specs: tuple[str, ...]) -> list[Path]:
    """Resolve scenario specs (files, dirs, globs) into a deduplicated list of paths."""
    paths: dict[str, Path] = {}
    for spec in specs:
        p = Path(spec)
        if p.is_file():
            paths[str(p.resolve())] = p
        elif p.is_dir():
            for f in sorted(p.rglob("*.testql.toon.yaml")):
                paths[str(f.resolve())] = f
        else:
            for m in sorted(glob.glob(spec, recursive=True)):
                mp = Path(m)
                if mp.is_file():
                    paths[str(mp.resolve())] = mp
    return [paths[k] for k in sorted(paths)]


def _run_scenario(scenario: Path, url: str, timeout: int) -> tuple[int, dict]:
    """Invoke `testql run <scenario> --output json --quiet` and return (exit_code, json)."""
    cmd = ["testql", "run", str(scenario), "--output", "json", "--quiet", "--url", url]
    log.debug("→ %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {"raw_stdout": proc.stdout[:500], "raw_stderr": proc.stderr[:500]}
    return proc.returncode, payload


def _post_failures(webhook_url: str, scenario: Path, failures: list[dict]) -> None:
    """POST failure details to webhook."""
    if not failures or not webhook_url:
        return
    try:
        import httpx
        body = {
            "source": "testql-watchdog",
            "scenario": scenario.name,
            "timestamp": time.time(),
            "failures": failures[:20],
        }
        resp = httpx.post(webhook_url, json=body, timeout=5.0)
        log.info("webhook <- %d failures (HTTP %s)", len(failures), resp.status_code)
    except Exception as exc:  # noqa: BLE001
        log.warning("webhook unreachable: %s", exc)


def _extract_failures(payload: dict) -> list[dict]:
    """Extract failed steps from testql JSON output."""
    failures: list[dict] = []
    steps = payload.get("steps") or payload.get("results") or []
    if isinstance(steps, list):
        for step in steps:
            if isinstance(step, dict) and not step.get("passed", step.get("ok", True)):
                failures.append({
                    "endpoint": step.get("endpoint") or step.get("url") or step.get("name", "?"),
                    "method": step.get("method", "GET"),
                    "status": step.get("status"),
                    "expected": step.get("expected_status"),
                    "error": step.get("error") or step.get("message"),
                })
    return failures


def _start_metrics_server(port: int, scenarios: list[Path]):
    """Start Prometheus metrics HTTP server and return metric objects."""
    try:
        from prometheus_client import Counter, Gauge, start_http_server
    except ImportError:
        log.warning("prometheus_client not installed; metrics disabled (pip install prometheus-client)")
        return None

    metrics = {
        "run_total": Counter("testql_scenario_run_total", "Scenario run count", ["scenario"]),
        "pass_total": Counter("testql_scenario_pass_total", "Assertions passed", ["scenario"]),
        "fail_total": Counter("testql_scenario_fail_total", "Assertions failed", ["scenario"]),
        "duration": Gauge("testql_scenario_duration_seconds", "Last-run wall-clock", ["scenario"]),
        "exit_code": Gauge("testql_scenario_last_exit_code", "Last exit code", ["scenario"]),
        "endpoint_up": Gauge("testql_endpoint_up", "1=pass, 0=fail", ["endpoint", "method"]),
        "scenarios_total": Gauge("testql_watchdog_scenarios_total", "Number of monitored scenarios"),
    }
    metrics["scenarios_total"].set(len(scenarios))
    start_http_server(port)
    log.info("Prometheus /metrics on :%d", port)
    return metrics


def _update_metrics(metrics, scenario: Path, exit_code: int, payload: dict, elapsed: float):
    """Update Prometheus counters/gauges for a single scenario run."""
    if metrics is None:
        return
    name = scenario.name
    metrics["run_total"].labels(scenario=name).inc()
    metrics["duration"].labels(scenario=name).set(elapsed)
    metrics["exit_code"].labels(scenario=name).set(exit_code)

    steps = payload.get("steps") or payload.get("results") or []
    if isinstance(steps, list):
        for step in steps:
            if not isinstance(step, dict):
                continue
            endpoint = step.get("endpoint") or step.get("url") or step.get("name", "?")
            method = step.get("method", "GET")
            passed = bool(step.get("passed", step.get("ok", False)))
            metrics["endpoint_up"].labels(endpoint=endpoint, method=method).set(1 if passed else 0)
            if passed:
                metrics["pass_total"].labels(scenario=name).inc()
            else:
                metrics["fail_total"].labels(scenario=name).inc()


def _resolve_watchdog_config(
    interval: int | None,
    webhook: str | None,
    port: int | None,
    url: str | None,
    timeout: int | None,
) -> tuple[int, str, int, str, int]:
    """Resolve watchdog config from CLI > env > defaults."""
    interval_s = interval or int(os.getenv("WATCHDOG_INTERVAL", "60"))
    webhook_url = webhook or os.getenv("WATCHDOG_WEBHOOK_URL", "http://healing-webhook:8810/probe-failure")
    metrics_port = port or int(os.getenv("WATCHDOG_METRICS_PORT", "9101"))
    base_url = url or os.getenv("WATCHDOG_BASE_URL", "http://localhost:8101")
    timeout_s = timeout or int(os.getenv("WATCHDOG_TIMEOUT", str(max(interval_s - 5, 10))))
    return interval_s, webhook_url, metrics_port, base_url, timeout_s


def _process_one_scenario(
    scenario: Path,
    base_url: str,
    timeout_s: int,
    webhook_url: str,
    metrics,
) -> None:
    """Run a single scenario, update metrics, and POST failures."""
    start = time.time()
    exit_code, payload = _run_scenario(scenario, base_url, timeout_s)
    elapsed = time.time() - start

    failures = _extract_failures(payload)
    _update_metrics(metrics, scenario, exit_code, payload, elapsed)

    status_icon = "✅" if exit_code == 0 else "❌"
    log.info(
        "%s %s exit=%d elapsed=%.1fs failures=%d",
        status_icon, scenario.name, exit_code, elapsed, len(failures),
    )

    if failures:
        _post_failures(webhook_url, scenario, failures)


@click.command()
@click.argument("scenarios", nargs=-1, required=True, type=str)
@click.option("--interval", type=int, default=None, help="Seconds between cycles (env: WATCHDOG_INTERVAL, default 60)")
@click.option("--webhook", type=str, default=None, help="URL to POST failures (env: WATCHDOG_WEBHOOK_URL)")
@click.option("--port", type=int, default=None, help="Prometheus metrics port (env: WATCHDOG_METRICS_PORT, default 9101)")
@click.option("--url", type=str, default=None, help="Base API URL for scenarios (env: WATCHDOG_BASE_URL, default http://localhost:8101)")
@click.option("--timeout", type=int, default=None, help="Per-scenario timeout in seconds (default: interval - 5)")
@click.option("--once", is_flag=True, help="Run all scenarios once and exit (useful for CI)")
@click.option("--verbose", is_flag=True, help="Verbose logging")
def watchdog(
    scenarios: tuple[str, ...],
    interval: int | None,
    webhook: str | None,
    port: int | None,
    url: str | None,
    timeout: int | None,
    once: bool,
    verbose: bool,
) -> None:
    """Run TestQL scenarios in a continuous loop with Prometheus metrics.

    Accepts files, directories, or glob patterns. Scenarios execute in
    round-robin order. Failures are POSTed to a webhook for self-healing.

    \b
    Examples:
      testql watchdog scenarios/realtime-health.testql.toon.yaml
      testql watchdog ./scenarios/ --interval 30
      testql watchdog a.yaml b.yaml c.yaml --once
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )

    interval_s, webhook_url, metrics_port, base_url, timeout_s = _resolve_watchdog_config(
        interval, webhook, port, url, timeout
    )

    # Discover scenarios
    paths = _discover_scenarios(scenarios)
    if not paths:
        raise click.ClickException("No .testql.toon.yaml scenarios found in the given paths.")

    log.info("testql watchdog starting")
    log.info("  scenarios = %d files", len(paths))
    for p in paths:
        log.info("    • %s", p)
    log.info("  interval  = %ds", interval_s)
    log.info("  url       = %s", base_url)
    log.info("  webhook   = %s", webhook_url)
    log.info("  metrics   = :%d/metrics", metrics_port)
    log.info("  timeout   = %ds per scenario", timeout_s)
    log.info("  mode      = %s", "once" if once else "loop")

    # Start Prometheus
    metrics = None if once else _start_metrics_server(metrics_port, paths)

    # Round-robin iterator
    scenario_iter: Iterator[Path] = iter(paths) if once else cycle(paths)
    cycle_count = 0
    scenarios_in_cycle = len(paths)

    try:
        for scenario in scenario_iter:
            cycle_count += 1
            try:
                _process_one_scenario(scenario, base_url, timeout_s, webhook_url, metrics)
            except subprocess.TimeoutExpired:
                log.error("⏰ %s timed out after %ds", scenario.name, timeout_s)
                _update_metrics(metrics, scenario, -1, {}, float(timeout_s))
            except Exception as exc:  # noqa: BLE001
                log.exception("unexpected error running %s: %s", scenario.name, exc)

            # Sleep between scenarios (not between cycles)
            if not once:
                time.sleep(interval_s / scenarios_in_cycle)

    except KeyboardInterrupt:
        log.info("watchdog stopped (Ctrl+C)")

    if once:
        # Exit with non-zero if any scenario failed
        sys.exit(0 if cycle_count == len(paths) else 1)

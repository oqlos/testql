"""Browser navigation performance measurement commands."""

from __future__ import annotations

import json
import shlex
import time
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


def parse_measure_navigation_args(args: str) -> tuple[str, str, int, str]:
    """Parse URL, ready selector, timeout and destination variable."""
    parts = shlex.split(args)
    option_parts = [part for part in parts if part.startswith(("timeout=", "as="))]
    positional = [part for part in parts if part not in option_parts]
    options = dict(part.split("=", 1) for part in option_parts)
    if len(positional) < 2:
        raise ValueError(
            'GUI_MEASURE_NAVIGATION requires "url" "ready_selector" '
            "[timeout=15000] [as=_performance]"
        )
    timeout = int(options.get("timeout", "15000"))
    if timeout <= 0:
        raise ValueError("timeout must be greater than zero")
    variable = options.get("as", "_performance")
    if not variable:
        raise ValueError("performance variable name cannot be empty")
    return positional[0], positional[1], timeout, variable


def performance_init_script(selector: str) -> str:
    """Return an init script installed before navigation in every frame."""
    encoded_selector = json.dumps(selector)
    return f"""
(() => {{
  const selector = {encoded_selector};
  const metric = {{ ready_ms: null, long_tasks: [] }};
  window.__testqlPerformance = metric;

  const markReady = () => {{
    if (metric.ready_ms !== null) return;
    try {{
      if (document.querySelector(selector)) metric.ready_ms = performance.now();
    }} catch (_) {{}}
  }};

  try {{
    const observer = new PerformanceObserver((list) => {{
      for (const entry of list.getEntries()) {{
        metric.long_tasks.push({{ start: entry.startTime, duration: entry.duration }});
      }}
    }});
    observer.observe({{ type: "longtask", buffered: true }});
  }} catch (_) {{}}

  document.addEventListener("DOMContentLoaded", markReady, {{ once: true }});
  const timer = setInterval(() => {{
    markReady();
    if (metric.ready_ms !== null) clearInterval(timer);
  }}, 25);
  markReady();
}})();
"""


PERFORMANCE_FRAME_SCRIPT = """
() => {
  const state = window.__testqlPerformance || {};
  const resources = performance.getEntriesByType("resource");
  const scripts = resources.filter((entry) => entry.initiatorType === "script");
  const nav = performance.getEntriesByType("navigation")[0];
  return {
    time_origin: performance.timeOrigin,
    ready_ms: state.ready_ms === null || state.ready_ms === undefined ? null : state.ready_ms,
    response_ms: nav ? nav.responseStart - nav.requestStart : null,
    dom_content_loaded_ms: nav ? nav.domContentLoadedEventEnd : null,
    load_event_ms: nav ? nav.loadEventEnd : null,
    resource_count: resources.length,
    transfer_bytes: resources.reduce((sum, entry) => sum + (entry.transferSize || 0), 0),
    script_bytes: scripts.reduce((sum, entry) => sum + (entry.transferSize || 0), 0),
    long_task_count: (state.long_tasks || []).length,
    long_task_ms: (state.long_tasks || []).reduce((sum, entry) => sum + (entry.duration || 0), 0),
  };
}
"""


def aggregate_frame_metrics(frames: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate top navigation and same-/cross-origin frame resource metrics."""
    usable = [frame for frame in frames if isinstance(frame, dict)]
    if not usable:
        return {}
    top = usable[0]
    top_origin = float(top.get("time_origin") or 0)
    ready_values = []
    for frame in usable:
        if frame.get("ready_ms") is not None:
            ready_values.append(
                float(frame.get("time_origin") or top_origin) - top_origin
                + float(frame["ready_ms"])
            )
    return {
        "ready_ms": min(ready_values) if ready_values else None,
        "response_ms": top.get("response_ms"),
        "dom_content_loaded_ms": top.get("dom_content_loaded_ms"),
        "load_event_ms": top.get("load_event_ms"),
        "resource_count": sum(int(frame.get("resource_count") or 0) for frame in usable),
        "transfer_bytes": sum(int(frame.get("transfer_bytes") or 0) for frame in usable),
        "script_bytes": sum(int(frame.get("script_bytes") or 0) for frame in usable),
        "long_task_count": sum(int(frame.get("long_task_count") or 0) for frame in usable),
        "long_task_ms": sum(float(frame.get("long_task_ms") or 0) for frame in usable),
        "frame_count": len(usable),
    }


def collect_page_metrics(page: Any) -> dict[str, Any]:
    """Collect every Playwright frame, including cross-origin iframe documents."""
    if hasattr(page, "performance_metrics"):
        return aggregate_frame_metrics(page.performance_metrics(PERFORMANCE_FRAME_SCRIPT))
    frames = []
    for frame in page.frames:
        try:
            frames.append(frame.evaluate(PERFORMANCE_FRAME_SCRIPT))
        except Exception:
            continue
    return aggregate_frame_metrics(frames)


class BrowserPerformanceMixin:
    """Provide measured browser navigation as structured TestQL data."""

    def _cmd_gui_measure_navigation(self, args: str, line: OqlLine) -> None:
        """Navigate and capture browser performance metrics into a variable."""
        name = "GUI_MEASURE_NAVIGATION"
        try:
            url, selector, timeout, variable = parse_measure_navigation_args(args)
        except (ValueError, TypeError) as error:
            self.out.fail(f"L{line.number}: {error}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(error)))
            return

        if self.dry_run:
            self.out.step("⏱️", f'{name} "{url}" → {variable} (dry-run)')
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return
        if not self._gui_page:
            message = "No active GUI session. Call GUI_START first"
            self.out.fail(f"{name}: {message}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=message))
            return

        target = url
        if not url.startswith(("http://", "https://")):
            base_url = self.vars.get("base_url", "http://localhost:8100")
            target = f"{str(base_url).rstrip('/')}/{url.lstrip('/')}"

        started = time.monotonic()
        try:
            self._gui_page.add_init_script(performance_init_script(selector))
            self._gui_page.goto(target, timeout=timeout)
            deadline = time.monotonic() + timeout / 1000
            metrics: dict[str, Any] = {}
            while time.monotonic() < deadline:
                metrics = collect_page_metrics(self._gui_page)
                if metrics.get("ready_ms") is not None:
                    break
                time.sleep(0.025)
            if metrics.get("ready_ms") is None:
                raise TimeoutError(f'ready selector "{selector}" not found within {timeout}ms')

            metrics["navigation_ms"] = round((time.monotonic() - started) * 1000, 2)
            for key, value in list(metrics.items()):
                if isinstance(value, float):
                    metrics[key] = round(value, 2)
            self.vars.set(variable, metrics)
            self.last_response = metrics
            summary = json.dumps(metrics, ensure_ascii=False, separators=(",", ":"))
            self.out.step("⏱️", f"{name} → {summary}")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.PASSED,
                value=metrics,
                message=summary,
                duration_ms=metrics["navigation_ms"],
                details=metrics,
            ))
        except Exception as error:
            duration = (time.monotonic() - started) * 1000
            self.out.fail(f"{name} error: {error}")
            self.errors.append(f"L{line.number}: {name} failed: {error}")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.ERROR,
                message=str(error),
                duration_ms=duration,
            ))

    def _cmd_measure_navigation(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_MEASURE_NAVIGATION."""
        self._cmd_gui_measure_navigation(args, line)

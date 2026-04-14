"""TestQL console reporter — colorful terminal output."""

from __future__ import annotations

from testql.base import ScriptResult, StepStatus


def report_console(result: ScriptResult) -> str:
    """Format a ScriptResult for console display."""
    lines: list[str] = []
    lines.append(f"\n{'=' * 60}")
    lines.append(f"  TestQL Report: {result.source}")
    lines.append(f"{'=' * 60}")

    for step in result.steps:
        icon = {
            StepStatus.PASSED: "✅",
            StepStatus.FAILED: "❌",
            StepStatus.ERROR: "💥",
            StepStatus.SKIPPED: "⏭️",
            StepStatus.WARNING: "⚠️",
        }.get(step.status, "  ")
        lines.append(f"  {icon} {step.name}")
        if step.message:
            lines.append(f"       {step.message}")

    lines.append(f"{'─' * 60}")
    icon = "✅" if result.ok else "❌"
    lines.append(
        f"  {icon} {result.passed}/{len(result.steps)} passed, "
        f"{result.failed} failed ({result.duration_ms:.0f}ms)"
    )
    if result.errors:
        lines.append(f"  Errors:")
        for err in result.errors:
            lines.append(f"    • {err}")
    lines.append("")
    return "\n".join(lines)

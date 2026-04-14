"""TestQL JSON reporter."""

from __future__ import annotations

import json

from testql.base import ScriptResult


def report_json(result: ScriptResult) -> str:
    """Format a ScriptResult as JSON."""
    return json.dumps(
        {
            "source": result.source,
            "ok": result.ok,
            "passed": result.passed,
            "failed": result.failed,
            "total": len(result.steps),
            "duration_ms": round(result.duration_ms, 1),
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "message": s.message,
                    "duration_ms": round(s.duration_ms, 1),
                }
                for s in result.steps
            ],
            "errors": result.errors,
            "warnings": result.warnings,
        },
        indent=2,
    )

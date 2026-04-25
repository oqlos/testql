"""Executor for `ProtoStep` — local message validation against a `.proto` schema.

The proto source is read from `step.schema_file` (path relative to cwd) — or,
if absent, from the `_proto_source` variable / `proto.schemas` fixture. The
step's `fields["_raw"]` is parsed via `parse_instance_fields` into the
`(name, type, raw_value)` tuples the validator expects.

Two checks are supported via `step.check`:

  * `round_trip_equal` — every scalar value coerces stably (no precision loss)
  * `all_required_present` — every required field is supplied

The payload exposed to assertions is:

    {"valid": bool, "issues": [...], "missing": [...], "message": "User",
     "check": "round_trip_equal"}
"""

from __future__ import annotations

from pathlib import Path

from testql.adapters.proto.descriptor_loader import parse_proto
from testql.adapters.proto.message_validator import (
    lookup_message,
    parse_instance_fields,
    round_trip_equal,
    validate_message_instance,
)
from testql.base import StepResult, StepStatus
from testql.ir import ProtoStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


def _resolve_source(step: ProtoStep, ctx: ExecutionContext) -> str:
    """Pick the best available proto source (schema_file path → variable → fixture)."""
    schema_path = interp_value(step.schema_file, ctx.vars)
    if schema_path:
        path = Path(schema_path)
        if path.is_file():
            return path.read_text(encoding="utf-8")
        return schema_path  # treat as inline source string
    return interp_value(ctx.vars.get("_proto_source", ""), ctx.vars)


def _instance_tuples(step: ProtoStep) -> list[tuple[str, str, str]]:
    raw = (step.fields or {}).get("_raw", "")
    return parse_instance_fields(str(raw))


def _run_check(check: str, message, instance) -> tuple[bool, list, list]:
    """Run the requested check; return (valid, issue_messages, missing_field_names)."""
    if check == "round_trip_equal":
        return round_trip_equal(message, instance), [], []
    result = validate_message_instance(message, instance)
    issues = [iss.message for iss in result.issues if iss.severity == "error"]
    missing = [iss.field for iss in result.issues if "missing required" in iss.message]
    return len(issues) == 0, issues, missing


def execute(step: ProtoStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "PROTO")
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "message": step.message})
    try:
        source = _resolve_source(step, ctx)
        if not source:
            return error_result(label, ValueError("no proto source available"))
        proto_file = parse_proto(source)
        message = lookup_message(proto_file, step.message)
        if message is None:
            return error_result(label, ValueError(f"unknown message: {step.message!r}"))
        instance = _instance_tuples(step)
        valid, issues, missing = _run_check(step.check, message, instance)
    except Exception as e:
        return error_result(label, e)
    payload = {"valid": valid, "issues": issues, "missing": missing,
               "message": step.message, "check": step.check}
    ctx.last_response = payload
    return assemble_result(label, payload, step.asserts, ctx.dry_run)


__all__ = ["execute"]

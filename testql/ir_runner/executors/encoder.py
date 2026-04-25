"""Executor for `EncoderStep` — POST hardware-encoder commands.

Mirrors the legacy `EncoderMixin` endpoint mapping but as a pure function,
without the mixin chain.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from testql.base import StepResult, StepStatus
from testql.ir import EncoderStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


_ENDPOINTS: dict[str, str] = {
    "on": "/encoder/activate",
    "off": "/encoder/deactivate",
    "click": "/encoder/click",
    "dblclick": "/encoder/cancel",
    "scroll": "/encoder/scroll",
    "focus": "/encoder/focus",
    "status": "/encoder/status",
    "page_next": "/encoder/page-next",
    "page_prev": "/encoder/page-prev",
}


def _request_body(action: str, value, target) -> dict | None:
    if action == "scroll":
        return {"delta": int(value) if value is not None else 1}
    if action == "focus":
        return {"zone": str(target or "col3")}
    return None


def _do_call(method: str, url: str, body: dict | None) -> tuple[int, dict]:
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        return e.code, {"error": e.reason}


def execute(step: EncoderStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "ENCODER")
    endpoint = _ENDPOINTS.get(step.action)
    if endpoint is None:
        return error_result(label, ValueError(f"unknown encoder action: {step.action!r}"))
    url = ctx.encoder_url + endpoint
    method = "GET" if step.action == "status" else "POST"
    body = _request_body(step.action, interp_value(step.value, ctx.vars),
                         interp_value(step.target, ctx.vars))
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "url": url})
    try:
        status, data = _do_call(method, url, body)
    except Exception as e:
        return error_result(label, e)
    payload = {"status": status, "data": data, "action": step.action}
    ctx.last_response, ctx.last_status = payload, status
    return assemble_result(label, payload, step.asserts, ctx.dry_run)


__all__ = ["execute"]

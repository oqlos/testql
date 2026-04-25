"""Executor for `ApiStep` — HTTP request + assertion evaluation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from testql.base import StepResult, StepStatus
from testql.ir import ApiStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, step_label


def _resolve_url(path: str, ctx: ExecutionContext) -> str:
    if path.startswith(("http://", "https://")):
        return path
    return f"{ctx.api_url}{path}"


def _parse_response(text: str) -> dict:
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text[:500]}


def _do_request(method: str, url: str, body: dict | None, headers: dict) -> tuple[int, dict]:
    req_body = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url, data=req_body, method=method,
        headers={"Content-Type": "application/json", **headers},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, _parse_response(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return e.code, _parse_response(body_text)


def _payload(status: int, data: object, headers: dict) -> dict:
    return {"status": status, "data": data, "headers": headers}


def execute(step: ApiStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "API")
    url = _resolve_url(interp_value(step.path, ctx.vars), ctx)
    body = interp_value(step.body, ctx.vars)
    headers = interp_value(step.headers, ctx.vars) or {}
    if ctx.dry_run:
        ctx.last_status, ctx.last_response = 200, {}
        return StepResult(name=label, status=StepStatus.PASSED,
                          details={"dry_run": True, "url": url})
    try:
        status, data = _do_request(step.method, url, body, headers)
    except Exception as e:
        return error_result(label, e)
    ctx.last_status, ctx.last_response = status, data
    return assemble_result(label, _payload(status, data, headers), step.asserts, ctx.dry_run)


__all__ = ["execute"]

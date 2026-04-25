"""Executor for `GraphqlStep` — POST query/mutation against a GraphQL endpoint.

`subscription` is best-effort: in this minimal runner it is not executed and
returns a SKIPPED result with a message pointing the user at the legacy
WebSocket path.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from testql.base import StepResult, StepStatus
from testql.ir import GraphqlStep

from ..context import ExecutionContext
from ..interpolation import interp_value
from .base import assemble_result, error_result, skipped_result, step_label


def _post_graphql(url: str, query: str, variables: dict) -> tuple[int, dict]:
    body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        return e.code, {"errors": [{"message": e.reason}]}


def _resolve_endpoint(step: GraphqlStep, ctx: ExecutionContext) -> str:
    return interp_value(step.endpoint or ctx.graphql_url, ctx.vars)


def execute(step: GraphqlStep, ctx: ExecutionContext) -> StepResult:
    label = step_label(step, "GRAPHQL")
    if step.operation == "subscription":
        return skipped_result(label, "subscriptions not supported by run-ir; use legacy `testql run`")
    if ctx.dry_run:
        return StepResult(name=label, status=StepStatus.PASSED, details={"dry_run": True})
    url = _resolve_endpoint(step, ctx)
    query = interp_value(step.body, ctx.vars)
    variables = interp_value(step.variables, ctx.vars) or {}
    try:
        status, response = _post_graphql(url, query, variables)
    except Exception as e:
        return error_result(label, e)
    payload = {"status": status, "data": response.get("data"),
               "errors": response.get("errors", []), "raw": response}
    ctx.last_response, ctx.last_status = payload, status
    return assemble_result(label, payload, step.asserts, ctx.dry_run)


__all__ = ["execute"]

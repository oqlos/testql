"""OpenAPI 3.x → TestPlan IR.

Walks `paths.<path>.<method>` and emits one `ApiStep` per declared operation,
with a default `Assertion(field='status', op='==', expected=200)` when no
explicit success response is declared.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from testql.ir import ApiStep, Assertion, ScenarioMetadata, TestPlan

from .base import BaseSource, SourceLike


_HTTP_METHODS = ("get", "post", "put", "delete", "patch", "head", "options")


def _load_spec(source: SourceLike) -> dict[str, Any]:
    if isinstance(source, dict):
        return source
    if isinstance(source, Path):
        text = source.read_text(encoding="utf-8")
    elif "\n" not in source and Path(source).is_file():
        text = Path(source).read_text(encoding="utf-8")
    else:
        text = source
    return yaml.safe_load(text) or {}


def _pick_success_status(responses: dict | None) -> int:
    """Return the lowest 2xx status declared, or 200 by default."""
    if not responses:
        return 200
    twos = [int(k) for k in responses.keys()
            if isinstance(k, (str, int)) and str(k).isdigit() and 200 <= int(k) < 300]
    return min(twos) if twos else 200


def _operation_to_step(method: str, path: str, op_spec: dict | None) -> ApiStep:
    op_spec = op_spec or {}
    status = _pick_success_status(op_spec.get("responses"))
    name = op_spec.get("operationId") or f"{method.upper()} {path}"
    return ApiStep(
        method=method.upper(),
        path=path,
        expect_status=status,
        asserts=[Assertion(field="status", op="==", expected=status)],
        name=name,
    )


def _iter_operations(paths: dict):
    for path, item in (paths or {}).items():
        if not isinstance(item, dict):
            continue
        for method, op_spec in item.items():
            if method.lower() in _HTTP_METHODS:
                yield method.lower(), path, op_spec


@dataclass
class OpenAPISource(BaseSource):
    """`openapi.yaml` / `openapi.json` → TestPlan."""

    name: str = "openapi"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".openapi.yaml", ".openapi.yml", ".openapi.json",
    ))

    def load(self, source: SourceLike) -> TestPlan:
        spec = _load_spec(source)
        info = spec.get("info") or {}
        plan = TestPlan(metadata=ScenarioMetadata(
            name=info.get("title", "OpenAPI smoke"),
            type="api",
            version=info.get("version"),
            extra={"source": "openapi"},
        ))
        servers = spec.get("servers") or []
        if servers and isinstance(servers, list):
            plan.config["base_url"] = servers[0].get("url", "")
        for method, path, op_spec in _iter_operations(spec.get("paths") or {}):
            plan.steps.append(_operation_to_step(method, path, op_spec))
        return plan


__all__ = ["OpenAPISource"]

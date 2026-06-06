"""Thin HTTP/SDK client for nlp2dsl conversation endpoints."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any
from urllib import error, request


@dataclass
class Nlp2DslResponse:
    status_code: int
    body: dict[str, Any] = field(default_factory=dict)
    raw: str = ""

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300


class Nlp2DslClient:
    """Call nlp2dsl REST endpoints used in conversation test scenarios."""

    def __init__(self, base_url: str | None = None, timeout_s: float = 30.0) -> None:
        self.base_url = (base_url or os.environ.get("NLP2DSL_URL") or "http://localhost:8080").rstrip("/")
        self.timeout_s = timeout_s

    def _post(self, path: str, payload: dict[str, Any]) -> Nlp2DslResponse:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                body = json.loads(raw) if raw.strip() else {}
                return Nlp2DslResponse(status_code=resp.status, body=body, raw=raw)
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw) if raw.strip() else {}
            except json.JSONDecodeError:
                body = {"error": raw}
            return Nlp2DslResponse(status_code=exc.code, body=body, raw=raw)

    def chatstart(self, payload: dict[str, Any] | None = None) -> Nlp2DslResponse:
        return self._post("/chatstart", payload or {})

    def chatmessage(self, payload: dict[str, Any]) -> Nlp2DslResponse:
        return self._post("/chatmessage", payload)

    def runworkflow(self, payload: dict[str, Any]) -> Nlp2DslResponse:
        return self._post("/runworkflow", payload)

    def workflow_from_text(self, text: str, *, execute: bool = False) -> Nlp2DslResponse:
        return self._post("/workflowfrom-text", {"text": text, "execute": execute})

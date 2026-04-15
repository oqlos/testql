"""Encoder hardware commands mixin for IqlInterpreter."""

from __future__ import annotations

import json
import urllib.request

from testql.base import StepResult, StepStatus

from ._parser import IqlLine


class EncoderMixin:
    """Mixin providing all ENCODER_* hardware control commands."""

    def _encoder_url(self) -> str:
        return self.vars.get("encoder_url", "http://localhost:8105")

    def _encoder_call(
        self, method: str, endpoint: str, body: dict | None, line: IqlLine, label: str
    ) -> None:
        url = f"{self._encoder_url()}{endpoint}"
        if self.dry_run:
            self.out.step("🎛️", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return
        try:
            req_body = json.dumps(body).encode("utf-8") if body else None
            req = urllib.request.Request(
                url, data=req_body, method=method,
                headers={"Content-Type": "application/json"} if req_body else {},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                text = resp.read().decode("utf-8")
                try:
                    data = json.loads(text)
                except Exception:
                    data = {"text": text[:200]}
                self.vars.set("_encoder_status", data)
                self.out.step("🎛️", f"{label} => {json.dumps(data)[:120]}")
                self.results.append(StepResult(name=label, status=StepStatus.PASSED, details=data))
        except Exception as e:
            self.out.fail(f"{label} => {e}")
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(e)))

    def _cmd_encoder_on(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/activate", None, line, "ENCODER_ON")

    def _cmd_encoder_off(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/deactivate", None, line, "ENCODER_OFF")

    def _cmd_encoder_scroll(self, args: str, line: IqlLine) -> None:
        delta = int(args.strip()) if args.strip() else 1
        self._encoder_call("POST", "/encoder/scroll", {"delta": delta}, line, f"ENCODER_SCROLL {delta}")

    def _cmd_encoder_click(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/click", None, line, "ENCODER_CLICK")

    def _cmd_encoder_dblclick(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/cancel", None, line, "ENCODER_DBLCLICK")

    def _cmd_encoder_focus(self, args: str, line: IqlLine) -> None:
        zone = args.strip().strip("\"'") or "col3"
        self._encoder_call("POST", "/encoder/focus", {"zone": zone}, line, f"ENCODER_FOCUS {zone}")

    def _cmd_encoder_status(self, args: str, line: IqlLine) -> None:
        self._encoder_call("GET", "/encoder/status", None, line, "ENCODER_STATUS")

    def _cmd_encoder_page_next(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/page-next", None, line, "ENCODER_PAGE_NEXT")

    def _cmd_encoder_page_prev(self, args: str, line: IqlLine) -> None:
        self._encoder_call("POST", "/encoder/page-prev", None, line, "ENCODER_PAGE_PREV")

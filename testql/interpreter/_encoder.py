"""Encoder hardware commands mixin for OqlInterpreter."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class EncoderMixin:
    """Mixin providing all ENCODER_* hardware control commands."""

    def _encoder_url(self) -> str:
        return self.vars.get("encoder_url", "http://localhost:8105")

    def _encoder_prefix(self) -> str:
        return self.vars.get("encoder_endpoint_prefix", "/encoder")

    def _encoder_do_http(
        self, method: str, url: str, body: dict | None, label: str
    ) -> None:
        """Execute the encoder HTTP call and record the result step."""
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

    def _encoder_call(
        self, method: str, endpoint: str, body: dict | None, line: OqlLine, label: str
    ) -> None:
        url = f"{self._encoder_url()}{endpoint}"
        if self.dry_run:
            self.out.step("🎛️", f"{label} (dry-run)")
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return
        try:
            self._encoder_do_http(method, url, body, label)
        except urllib.error.HTTPError as e:
            if e.code == 405 and method.upper() == "POST":
                fallback_url = url
                if body:
                    query = urllib.parse.urlencode(body)
                    fallback_url = f"{url}?{query}" if query else url
                self.out.warn(f"{label} POST not allowed; retrying GET")
                try:
                    self._encoder_do_http("GET", fallback_url, None, label)
                    return
                except Exception as fallback_error:
                    self.out.fail(f"{label} => {fallback_error}")
                    self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(fallback_error)))
                    return
            self.out.fail(f"{label} => {e}")
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(e)))
        except Exception as e:
            self.out.fail(f"{label} => {e}")
            self.results.append(StepResult(name=label, status=StepStatus.FAILED, message=str(e)))

    def _cmd_encoder_on(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/activate", None, line, "ENCODER_ON")

    def _cmd_encoder_off(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/deactivate", None, line, "ENCODER_OFF")

    def _cmd_encoder_scroll(self, args: str, line: OqlLine) -> None:
        delta = int(args.strip()) if args.strip() else 1
        self._encoder_call("POST", f"{self._encoder_prefix()}/scroll", {"delta": delta}, line, f"ENCODER_SCROLL {delta}")

    def _cmd_encoder_click(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/click", None, line, "ENCODER_CLICK")

    def _cmd_encoder_dblclick(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/cancel", None, line, "ENCODER_DBLCLICK")

    def _cmd_encoder_focus(self, args: str, line: OqlLine) -> None:
        zone = args.strip().strip("\"'") or "col3"
        self._encoder_call("POST", f"{self._encoder_prefix()}/focus", {"zone": zone}, line, f"ENCODER_FOCUS {zone}")

    def _cmd_encoder_status(self, args: str, line: OqlLine) -> None:
        self._encoder_call("GET", f"{self._encoder_prefix()}/status", None, line, "ENCODER_STATUS")

    def _cmd_encoder_page_next(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/page-next", None, line, "ENCODER_PAGE_NEXT")

    def _cmd_encoder_page_prev(self, args: str, line: OqlLine) -> None:
        self._encoder_call("POST", f"{self._encoder_prefix()}/page-prev", None, line, "ENCODER_PAGE_PREV")

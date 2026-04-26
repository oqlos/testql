"""API runner mixin — HTTP calls and response capture for IqlInterpreter."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import IqlLine


class ApiRunnerMixin:
    """Mixin providing HTTP API execution commands: API, CAPTURE."""

    # These attributes are provided by the host IqlInterpreter
    api_url: str
    dry_run: bool
    last_response: dict[str, Any] | None
    last_status: int

    # Retry configuration
    retry_max_attempts: int = 3
    retry_backoff_ms: int = 1000
    retry_status_codes: set[int] = {429, 500, 502, 503, 504}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _do_http_request(self, method: str, url: str, body_data: dict | None) -> tuple[int, dict, dict]:
        """Execute an HTTP request, returning (status, parsed_response, headers)."""
        req_body = json.dumps(body_data).encode("utf-8") if body_data else None
        req = urllib.request.Request(
            url, data=req_body, method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            headers = dict(resp.headers)
            text = resp.read().decode("utf-8")
            try:
                data = json.loads(text)
            except Exception:
                data = {"text": text[:500]}
            return status, data, headers

    def _do_http_request_with_retry(self, method: str, url: str, body_data: dict | None) -> tuple[int, dict, dict]:
        """Execute HTTP request with retry logic for transient failures."""
        last_exception = None

        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                status, data, headers = self._do_http_request(method, url, body_data)

                # Check if status code warrants retry
                if status in self.retry_status_codes and attempt < self.retry_max_attempts:
                    backoff = self.retry_backoff_ms * attempt
                    self.out.warn(f"Retry {attempt}/{self.retry_max_attempts} for {status} (wait {backoff}ms)")
                    time.sleep(backoff / 1000)
                    continue

                return status, data, headers

            except (urllib.error.URLError, urllib.error.HTTPError) as e:
                last_exception = e
                if hasattr(e, 'code') and e.code in self.retry_status_codes and attempt < self.retry_max_attempts:
                    backoff = self.retry_backoff_ms * attempt
                    self.out.warn(f"Retry {attempt}/{self.retry_max_attempts} for {e.code} (wait {backoff}ms)")
                    time.sleep(backoff / 1000)
                    continue
                # Re-raise non-retryable errors
                raise
            except Exception as e:
                # Non-retryable errors
                raise

        # All retries exhausted, raise last exception
        if last_exception:
            raise last_exception
        raise RuntimeError("Max retries exceeded")

    def _store_api_response(self, status: int, response: dict, headers: dict | None = None) -> None:
        """Persist last API response into interpreter state and variables."""
        self.last_status = status
        self.last_response = response
        self.vars.set("_status", status)
        self.vars.set("_response", response)
        self.vars.set("_headers", headers or {})
        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, list):
                self.vars.set("_count", len(data))

    # ── Commands ─────────────────────────────────────────────────────────────

    def _record_api_success(self, label: str, status: int, response: dict, headers: dict | None = None) -> None:
        """Store successful API response and append a PASSED step."""
        self._store_api_response(status, response, headers)
        icon = "✅" if status < 400 else "❌"
        self.out.step(icon, f"{label} → {status}")
        self.results.append(StepResult(
            name=label, status=StepStatus.PASSED, details={"status": status},
        ))

    def _record_api_http_error(self, label: str, e: urllib.error.HTTPError) -> None:
        self.last_status = e.code
        self.last_response = {}
        self.out.fail(f"{label} → {e.code}")
        self.results.append(StepResult(
            name=label, status=StepStatus.FAILED, message=f"HTTP {e.code}",
        ))

    def _record_api_error(self, label: str, e: Exception) -> None:
        self.last_status = 0
        self.last_response = {}
        self.out.fail(f"{label} → {e}")
        self.results.append(StepResult(
            name=label, status=StepStatus.ERROR, message=str(e),
        ))

    def _cmd_api(self, args: str, line: IqlLine) -> None:
        """API METHOD /path [json-body]"""
        parts = args.strip().split(None, 2)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: API requires METHOD URL [body]")
            return

        method = parts[0].upper()
        url = parts[1].strip("\"'")
        body_str = parts[2] if len(parts) > 2 else ""

        if url.startswith("/"):
            url = f"{self.api_url}{url}"

        body_data = None
        if body_str:
            body_str = self.vars.interpolate(body_str)
            try:
                body_data = json.loads(body_str)
            except json.JSONDecodeError:
                body_data = {"raw": body_str}

        label = f"API {method} {url}"

        if self.dry_run:
            self.out.step("🌐", f"{label} (dry-run)")
            self.last_status = 200
            self.last_response = {"data": [], "_dry_run": True}
            self.results.append(StepResult(name=label, status=StepStatus.PASSED))
            return

        try:
            status, response, headers = self._do_http_request_with_retry(method, url, body_data)
            self._record_api_success(label, status, response, headers)
        except urllib.error.HTTPError as e:
            self._record_api_http_error(label, e)
        except Exception as e:
            self._record_api_error(label, e)

    def _cmd_capture(self, args: str, line: IqlLine) -> None:
        """CAPTURE var_name FROM "json.path"

        Extracts a value from the last API response via dotted JSON path
        and stores it as a variable for use in subsequent commands.

        Example:
            API POST /api/devices {"name": "Test"}
            ASSERT_STATUS 201
            CAPTURE device_id FROM "data.id"
            API GET /api/devices/${device_id}
        """
        import re
        m = re.match(r'(\w+)\s+FROM\s+"([^"]+)"', args.strip(), re.IGNORECASE)
        if not m:
            self.out.warn(f'L{line.number}: CAPTURE syntax: CAPTURE var FROM "json.path"')
            return

        var_name, json_path = m.group(1), m.group(2)
        value = _navigate_json_path(self.last_response, json_path)

        if value is None:
            self.out.warn(f"L{line.number}: CAPTURE {var_name}: path '{json_path}' not found in last response")
            self.results.append(StepResult(
                name=f"CAPTURE {var_name}", status=StepStatus.WARNING,
                message=f"Path '{json_path}' returned None",
            ))
            return

        self.vars.set(var_name, value)
        self.out.step("🔗", f"CAPTURE {var_name} = {value!r}")
        self.results.append(StepResult(
            name=f"CAPTURE {var_name}",
            status=StepStatus.PASSED,
            details={var_name: value},
        ))


def _resolve_length(root: Any, path: str) -> int | None:
    """Return len() of the list at *path* (without the trailing .length)."""
    parent: Any = root
    for key in path.rsplit(".", 1)[0].split("."):
        parent = parent.get(key) if isinstance(parent, dict) else None
    return len(parent) if isinstance(parent, list) else None


def _navigate_step(obj: Any, key: str) -> Any:
    """Descend one level into a JSON object by key (or integer index)."""
    if isinstance(obj, dict):
        return obj.get(key)
    if isinstance(obj, list):
        try:
            return obj[int(key)]
        except (ValueError, IndexError):
            return None
    return None


def _navigate_json_path(root: Any, path: str) -> Any:
    """Navigate a dotted JSON path, supporting list index key[0] and .length."""
    obj = root
    # Split by dots, but then also handle [index] inside keys
    for part in path.split("."):
        if '[' in part and part.endswith(']'):
            key, index_part = part.split('[', 1)
            index = int(index_part[:-1])
            if key:
                obj = _navigate_step(obj, key)
            obj = _navigate_step(obj, str(index))
        else:
            obj = _navigate_step(obj, part)
            
    if path.endswith(".length") and isinstance(root, dict):
        length = _resolve_length(root, path)
        if length is not None:
            obj = length
    return obj

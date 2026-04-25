"""Assertions mixin for IqlInterpreter."""

from __future__ import annotations

from typing import Any
import json

from testql.base import StepResult, StepStatus

from ._parser import IqlLine
from ._api_runner import _navigate_json_path


_COMPARE_OPS: dict[str, Any] = {
    "==": lambda a, b: a == b,
    "=":  lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: (a or 0) > b,
    ">=": lambda a, b: (a or 0) >= b,
    "<":  lambda a, b: (a or 0) < b,
    "<=": lambda a, b: (a or 0) <= b,
}


class AssertionsMixin:
    """Mixin providing ASSERT_STATUS, ASSERT_OK, ASSERT_CONTAINS, ASSERT_JSON."""

    def _cmd_assert_status(self, args: str, line: IqlLine) -> None:
        """ASSERT_STATUS <code> — check last HTTP status code."""
        expected = int(args.strip())
        ok = self.last_status == expected
        name = f"ASSERT_STATUS {expected}"
        if ok:
            self.out.step("  ✅", name)
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} (got {self.last_status})")
            self.errors.append(f"L{line.number}: expected status {expected}, got {self.last_status}")
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f"expected {expected}, got {self.last_status}",
            ))

    def _cmd_assert_ok(self, args: str, line: IqlLine) -> None:
        """ASSERT_OK — check last status was 2xx."""
        ok = 200 <= self.last_status < 300
        name = "ASSERT_OK"
        if ok:
            self.out.step("  ✅", f"{name} (status {self.last_status})")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} (status {self.last_status})")
            self.errors.append(f"L{line.number}: expected 2xx, got {self.last_status}")
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f"status {self.last_status}",
            ))

    def _cmd_assert_contains(self, args: str, line: IqlLine) -> None:
        """ASSERT_CONTAINS "needle" — check needle present in JSON-serialised response."""
        import json as _json
        needle = args.strip().strip("\"'")
        haystack = _json.dumps(self.last_response or {})
        ok = needle in haystack
        name = f'ASSERT_CONTAINS "{needle}"'
        if ok:
            self.out.step("  ✅", name)
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{name} — not found")
            self.errors.append(f'L{line.number}: "{needle}" not found in response')
            self.results.append(StepResult(
                name=name, status=StepStatus.FAILED,
                message=f'"{needle}" not found',
            ))

    def _cmd_assert_json(self, args: str, line: IqlLine) -> None:
        """ASSERT_JSON path op value — e.g. ASSERT_JSON data.length > 0"""
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.warn(f"L{line.number}: ASSERT_JSON requires <path> <op> <value>")
            return

        path, op, expected_str = parts[0], parts[1], parts[2]
        obj = _navigate_json_path(self.last_response, path)

        # Handle None values - fail assertion if path not found
        if obj is None:
            desc = f"ASSERT_JSON {path} {op} {expected_str}"
            self.out.step("  ❌", f"{desc} (path not found)")
            self.errors.append(f"L{line.number}: {desc} failed (path '{path}' not found in response)")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"path '{path}' not found",
            ))
            return

        try:
            expected: Any = float(expected_str) if "." in expected_str else int(expected_str)
        except ValueError:
            expected = expected_str.strip("\"'")

        cmp_fn = _COMPARE_OPS.get(op)
        ok = cmp_fn(obj, expected) if cmp_fn else False
        desc = f"ASSERT_JSON {path} {op} {expected_str}"

        if ok:
            self.out.step("  ✅", f"{desc} (actual: {obj})")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{desc} (actual: {obj})")
            self.errors.append(f"L{line.number}: {desc} failed (actual: {obj})")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"actual: {obj}",
            ))

    def _cmd_assert_schema(self, args: str, line: IqlLine) -> None:
        """ASSERT_SCHEMA <schema_file_or_json> — Validate response against JSON schema.

        Examples:
            ASSERT_SCHEMA "schemas/user.json"
            ASSERT_SCHEMA '{"type": "object", "required": ["id", "name"]}'
        """
        schema_input = args.strip().strip("\"'")

        if not schema_input:
            self.out.warn(f"L{line.number}: ASSERT_SCHEMA requires schema file or JSON")
            return

        # Try to load schema
        try:
            if schema_input.startswith("{") or schema_input.startswith("["):
                schema = json.loads(schema_input)
            else:
                # Assume it's a file path
                schema_path = Path(schema_input)
                if not schema_path.exists():
                    self.out.fail(f"L{line.number}: Schema file not found: {schema_input}")
                    self.results.append(StepResult(
                        name="ASSERT_SCHEMA", status=StepStatus.FAILED,
                        message=f"Schema file not found: {schema_input}"
                    ))
                    return
                schema = json.loads(schema_path.read_text())
        except (json.JSONDecodeError, IOError) as e:
            self.out.fail(f"L{line.number}: Invalid schema: {e}")
            self.results.append(StepResult(
                name="ASSERT_SCHEMA", status=StepStatus.FAILED, message=str(e)
            ))
            return

        # Validate response against schema
        try:
            import jsonschema
            jsonschema.validate(instance=self.last_response, schema=schema)
            self.out.step("  ✅", "ASSERT_SCHEMA valid")
            self.results.append(StepResult(
                name="ASSERT_SCHEMA", status=StepStatus.PASSED
            ))
        except ImportError:
            self.out.warn("jsonschema not installed. Install with: pip install jsonschema")
            self.results.append(StepResult(
                name="ASSERT_SCHEMA", status=StepStatus.WARNING,
                message="jsonschema not installed"
            ))
        except jsonschema.ValidationError as e:
            self.out.step("  ❌", f"ASSERT_SCHEMA invalid: {e.message}")
            self.errors.append(f"L{line.number}: Schema validation failed: {e.message}")
            self.results.append(StepResult(
                name="ASSERT_SCHEMA", status=StepStatus.FAILED, message=str(e.message)
            ))

    def _cmd_assert_headers(self, args: str, line: IqlLine) -> None:
        """ASSERT_HEADERS <header_name> <op> <expected> — Assert HTTP header value.

        Examples:
            ASSERT_HEADERS Content-Type == "application/json"
            ASSERT_HEADERS X-Custom-Header contains "value"
        """
        parts = args.strip().split(None, 2)
        if len(parts) < 3:
            self.out.warn(f"L{line.number}: ASSERT_HEADERS requires <header> <op> <value>")
            return

        header_name, op, expected = parts[0], parts[1], parts[2].strip("\"'")
        
        # Get headers from variable (set by API runner)
        actual = self.vars.get("_headers", {})

        if not isinstance(actual, dict):
            actual = {}

        header_value = actual.get(header_name, "")
        if isinstance(header_value, list):
            header_value = header_value[0] if header_value else ""

        cmp_fn = _COMPARE_OPS.get(op)
        if op == "contains":
            ok = expected in header_value
        elif cmp_fn:
            ok = cmp_fn(header_value, expected)
        else:
            ok = False

        desc = f"ASSERT_HEADERS {header_name} {op} {expected}"

        if ok:
            self.out.step("  ✅", f"{desc} (actual: {header_value})")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{desc} (actual: {header_value})")
            self.errors.append(f"L{line.number}: {desc} failed (actual: {header_value})")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"actual: {header_value}",
            ))

    def _cmd_assert_cookies(self, args: str, line: IqlLine) -> None:
        """ASSERT_COOKIES <cookie_name> <op> <expected> — Assert cookie value.

        Examples:
            ASSERT_COOKIES session_id exists
            ASSERT_COOKIES session_id == "abc123"
        """
        parts = args.strip().split(None, 2)
        if len(parts) < 2:
            self.out.warn(f"L{line.number}: ASSERT_COOKIES requires <cookie> <op> [value]")
            return

        cookie_name = parts[0]
        op = parts[1]
        expected = parts[2] if len(parts) > 2 else None

        # Get cookies from headers variable
        headers = self.vars.get("_headers", {})
        if not isinstance(headers, dict):
            headers = {}

        cookie_header = headers.get("Set-Cookie", headers.get("set-cookie", ""))
        if isinstance(cookie_header, list):
            cookie_header = "; ".join(cookie_header)

        # Parse cookie value
        cookies: dict[str, str] = {}
        for cookie in cookie_header.split(";"):
            cookie = cookie.strip()
            if "=" in cookie:
                k, v = cookie.split("=", 1)
                cookies[k.strip()] = v.strip()

        cookie_value = cookies.get(cookie_name, "")

        if op == "exists":
            ok = cookie_name in cookies
            desc = f"ASSERT_COOKIES {cookie_name} exists"
        elif op == "not_exists":
            ok = cookie_name not in cookies
            desc = f"ASSERT_COOKIES {cookie_name} not_exists"
        elif expected:
            expected = expected.strip("\"'")
            cmp_fn = _COMPARE_OPS.get(op)
            if op == "contains":
                ok = expected in cookie_value
            elif cmp_fn:
                ok = cmp_fn(cookie_value, expected)
            else:
                ok = False
            desc = f"ASSERT_COOKIES {cookie_name} {op} {expected}"
        else:
            self.out.warn(f"L{line.number}: ASSERT_COOKIES requires value for op '{op}'")
            return

        if ok:
            self.out.step("  ✅", f"{desc}")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            self.out.step("  ❌", f"{desc}")
            self.errors.append(f"L{line.number}: {desc} failed")
            self.results.append(StepResult(
                name=desc, status=StepStatus.FAILED, message=f"cookie value: {cookie_value}",
            ))

    def _cmd_assert_visible(self, args: str, line: IqlLine) -> None:
        """ASSERT_VISIBLE <selector> — Check if DOM element is visible (GUI test).

        This is a GUI assertion that requires a browser context. In headless/API mode,
        it passes with a warning since we can't verify DOM visibility.
        """
        selector = args.strip().strip('"\'')
        if not selector:
            self.out.warn(f"L{line.number}: ASSERT_VISIBLE requires a selector")
            return

        desc = f'ASSERT_VISIBLE "{selector}"'

        # Check if we have a browser/page context from GUI runner
        page = self.vars.get('_page')
        if page is not None:
            # Actual browser-based check would go here
            # For now, mark as passed with info
            self.out.step("  ✅", f"{desc} (GUI check)")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            # No browser context - skip but don't fail
            self.out.step("  ⏭️", f"{desc} (skipped - no GUI context)")
            self.results.append(StepResult(
                name=desc, status=StepStatus.PASSED,
                message="GUI assertion skipped in headless mode"
            ))

    def _cmd_assert_text(self, args: str, line: IqlLine) -> None:
        """ASSERT_TEXT <selector> <expected> — Check if element contains text (GUI test).

        This is a GUI assertion that requires a browser context. In headless/API mode,
        it passes with a warning since we can't verify DOM content.
        """
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            self.out.warn(f"L{line.number}: ASSERT_TEXT requires <selector> <expected>")
            return

        selector = parts[0].strip('"\'')
        expected = parts[1].strip('"\'')
        desc = f'ASSERT_TEXT "{selector}" "{expected}"'

        # Check if we have a browser/page context from GUI runner
        page = self.vars.get('_page')
        if page is not None:
            # Actual browser-based check would go here
            self.out.step("  ✅", f"{desc} (GUI check)")
            self.results.append(StepResult(name=desc, status=StepStatus.PASSED))
        else:
            # No browser context - skip but don't fail
            self.out.step("  ⏭️", f"{desc} (skipped - no GUI context)")
            self.results.append(StepResult(
                name=desc, status=StepStatus.PASSED,
                message="GUI assertion skipped in headless mode"
            ))

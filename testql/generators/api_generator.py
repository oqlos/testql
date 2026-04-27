"""API test generation mixin.

This module provides specialized generator for API-focused test scenarios.
"""

from __future__ import annotations

import urllib.request
import urllib.error
from pathlib import Path


class APIGeneratorMixin:
    """Mixin for generating API-focused test scenarios."""

    def _generate_api_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate comprehensive API tests from discovered routes."""
        routes = self.profile.config.get('discovered_routes', [])
        frameworks = self.profile.config.get('endpoint_frameworks', [])

        if not routes:
            return None

        # Determine the base_url to use for validation and testing
        # Priority: validate_url > base_url from config > default localhost
        base_url = self.profile.config.get('validate_url') or self.profile.config.get('base_url', 'http://localhost:8101')

        # Always validate endpoints to avoid generating 404 errors
        routes = self._validate_endpoints(routes, base_url)
        if not routes:
            return None

        # Filter to only GET endpoints for smoke tests (POST/PATCH need request bodies)
        get_routes = [r for r in routes if r.get('method', 'GET').upper() == 'GET']
        if not get_routes:
            return None

        sections = self._build_api_test_header(frameworks)
        sections.extend(self._build_api_test_config(frameworks, base_url))
        sections.extend(self._build_api_test_preamble(base_url))
        sections.extend(self._build_api_test_endpoints(get_routes))
        sections.extend(self._build_api_test_captures())
        sections.extend(self._build_api_test_assertions())
        sections.extend(self._build_api_test_flow())
        sections.extend(self._build_api_test_summary(get_routes))

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-api-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _validate_endpoints(self, routes: list[dict], base_url: str) -> list[dict]:
        """Validate endpoints by pinging them with retry and exponential backoff."""
        import sys
        
        valid_routes = []
        rejected = []
        
        sys.stderr.write(f"🔍 Validating {len(routes)} endpoints against {base_url}...\n")
        
        for route in routes:
            result = self._validate_single_endpoint(route, base_url)
            if result.is_valid:
                valid_routes.append(route)
                if result.retry_count > 0:
                    sys.stderr.write(f"  ⚠️  {result.method} {result.path} succeeded after {result.retry_count + 1} attempts\n")
            else:
                rejected.append(result.reason)
        
        self._log_validation_summary(valid_routes, rejected, routes)
        return valid_routes

    def _validate_single_endpoint(self, route: dict, base_url: str) -> "_ValidationResult":
        """Validate a single endpoint with retry logic."""
        path = route.get('path', '')
        method = route.get('method', 'GET')
        
        if '{' in path or '<' in path:
            return _ValidationResult(is_valid=False, reason=f"{method} {path} (parameterized path)", method=method, path=path)
        
        url = f"{base_url.rstrip('/')}{path}"
        max_retries = 3
        base_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                is_valid, reason = self._try_endpoint_request(url, method)
                if is_valid:
                    return _ValidationResult(is_valid=True, reason="", method=method, path=path, retry_count=attempt)
                elif reason:
                    return _ValidationResult(is_valid=False, reason=reason, method=method, path=path)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if attempt < max_retries - 1:
                    self._sleep_with_backoff(base_delay, attempt)
                    continue
                return _ValidationResult(is_valid=False, reason=f"{method} {path} ({type(e).__name__}: {e})", method=method, path=path)
            except Exception as e:
                return _ValidationResult(is_valid=False, reason=f"{method} {path} (unexpected: {e})", method=method, path=path)
        
        return _ValidationResult(is_valid=False, reason=f"{method} {path} (exceeded retries)", method=method, path=path)

    def _try_endpoint_request(self, url: str, method: str) -> tuple[bool, str | None]:
        """Try a single endpoint request and return (is_valid, reason_if_invalid)."""
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                status = resp.status
                if status < 400 or status in (401, 403):
                    return True, None
                else:
                    return False, f"{method} {url} (HTTP {status})"
        except urllib.error.HTTPError as e:
            if e.code in (404, 405):
                return False, f"{method} {url} (HTTP {e.code})"
            elif e.code < 500:
                return True, None
            return False, None

    def _sleep_with_backoff(self, base_delay: float, attempt: int) -> None:
        """Sleep with exponential backoff."""
        import time
        delay = base_delay * (2 ** attempt)
        time.sleep(delay)

    def _log_validation_summary(self, valid_routes: list[dict], rejected: list[str], routes: list[dict]) -> None:
        """Log validation summary to stderr."""
        import sys
        if rejected:
            sys.stderr.write(f"\n⚠️  Rejected {len(rejected)} endpoints:\n")
            for r in rejected[:10]:
                sys.stderr.write(f"   - {r}\n")
            if len(rejected) > 10:
                sys.stderr.write(f"   ... and {len(rejected) - 10} more\n")
        sys.stderr.write(f"✅ Validation complete: {len(valid_routes)}/{len(routes)} valid endpoints found.\n")

    def _build_api_test_header(self, frameworks: list[str]) -> list[str]:
        """Build header section for API test scenario."""
        return [
            "# SCENARIO: Auto-generated API Smoke Tests",
            "# TYPE: api",
            "# GENERATED: true",
            f"# DETECTORS: {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_config(self, frameworks: list[str], base_url: str = None) -> list[str]:
        """Build CONFIG section for API test scenario."""
        # Use provided base_url or fallback to localhost
        if base_url is None:
            base_url = 'http://localhost:8101'
            if hasattr(self, 'profile') and self.profile and hasattr(self.profile, 'config'):
                base_url = self.profile.config.get('base_url', base_url)
        return [
            "CONFIG[5]{key, value}:",
            f"  base_url, {base_url}",
            "  timeout_ms, 10000",
            "  retry_count, 3",
            "  retry_backoff_ms, 1000",
            f"  detected_frameworks, {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_preamble(self, base_url: str) -> list[str]:
        """Build preamble with WAIT and health check."""
        return [
            "# Wait for service to be ready",
            "WAIT 1000",
            "",
            "# Health check",
            "API GET /api/health 200",
            "ASSERT_STATUS 200",
            "",
        ]

    def _build_api_test_captures(self) -> list[str]:
        """Build CAPTURE section for dynamic values from responses."""
        return [
            "# Capture useful values from responses for subsequent tests",
            "# CAPTURE request_id FROM 'headers.x-request-id'",
            "# CAPTURE session_token FROM 'body.token'",
            "",
        ]

    def _build_rest_section(self, routes: list[dict]) -> list[str]:
        """Build REST API section lines."""
        unique_routes = self._deduplicate_rest_routes(routes)
        if not unique_routes:
            return []
        lines = [
            f"# REST API Endpoints ({len(unique_routes)} unique)",
            f"API[{len(unique_routes[:25])}]{{method, endpoint, expected_status}}:",
        ]
        for route in unique_routes[:25]:
            expected = 200 if route['method'] == 'GET' else 201
            lines.append(f"  {route['method']}, {route['path']}, {expected}")
        lines.append("")
        return lines

    def _build_graphql_section(self, routes: list[dict]) -> list[str]:
        """Build GraphQL section lines."""
        lines = [
            f"# GraphQL Endpoints ({len(routes)} detected)",
            f"GRAPHQL[{len(routes[:10])}]{{query, variables}}:",
        ]
        for route in routes[:10]:
            lines.append(f"  {route.get('handler', 'query')}, {{}}")
        lines.append("")
        return lines

    def _build_websocket_section(self, routes: list[dict]) -> list[str]:
        """Build WebSocket section lines."""
        lines = [
            f"# WebSocket Endpoints ({len(routes)} detected)",
            f"WEBSOCKET[{len(routes[:5])}]{{url, action}}:",
        ]
        for route in routes[:5]:
            lines.append(f"  ws://localhost:8101{route['path']}, connect")
        lines.append("")
        return lines

    def _build_api_test_endpoints(self, routes: list[dict]) -> list[str]:
        """Build endpoint sections for API test scenario."""
        sections: list[str] = []
        rest_routes = [r for r in routes if r.get('endpoint_type') == 'rest']
        graphql_routes = [r for r in routes if r.get('endpoint_type') == 'graphql']
        ws_routes = [r for r in routes if r.get('endpoint_type') == 'websocket']
        if rest_routes:
            sections.extend(self._build_rest_section(rest_routes))
        if graphql_routes:
            sections.extend(self._build_graphql_section(graphql_routes))
        if ws_routes:
            sections.extend(self._build_websocket_section(ws_routes))
        return sections

    def _deduplicate_rest_routes(self, routes: list[dict]) -> list[dict]:
        """Remove duplicate REST routes, excluding parameterized paths."""
        unique_routes = []
        seen = set()

        for r in routes:
            key = (r['method'], r['path'])
            if key not in seen and '{' not in r['path']:
                seen.add(key)
                unique_routes.append(r)

        return unique_routes

    def _build_api_test_assertions(self) -> list[str]:
        """Build assertions section for API test scenario."""
        return [
            "ASSERT[2]{field, operator, expected}:",
            "  _status, <, 500",
            "  _status, >=, 200",
        ]

    def _build_api_test_flow(self) -> list[str]:
        """Build FLOW section for conditional execution and error handling."""
        return [
            "",
            "# Conditional flow for error handling",
            "FLOW[2]{condition, action}:",
            "  _status >= 500, LOG 'Server error detected'",
            "  _status == 429, WAIT 2000  # Rate limit - wait and retry",
            "",
        ]

    def _build_api_test_summary(self, routes: list[dict]) -> list[str]:
        """Build summary section for API test scenario."""
        # Group routes by framework for summary
        routes_by_framework: dict[str, list] = {}
        for r in routes:
            fw = r.get('framework', 'unknown')
            if fw not in routes_by_framework:
                routes_by_framework[fw] = []
            routes_by_framework[fw].append(r)

        sections = []
        if routes_by_framework:
            sections.append("")
            sections.append("# Summary by Framework:")
            for fw, fw_routes in routes_by_framework.items():
                sections.append(f"#   {fw}: {len(fw_routes)} endpoints")

        return sections


class _ValidationResult:
    """Result of endpoint validation."""
    def __init__(self, is_valid: bool, reason: str, method: str, path: str, retry_count: int = 0):
        self.is_valid = is_valid
        self.reason = reason
        self.method = method
        self.path = path
        self.retry_count = retry_count

    def _build_api_test_header(self, frameworks: list[str]) -> list[str]:
        """Build header section for API test scenario."""
        return [
            "# SCENARIO: Auto-generated API Smoke Tests",
            "# TYPE: api",
            "# GENERATED: true",
            f"# DETECTORS: {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_config(self, frameworks: list[str], base_url: str = None) -> list[str]:
        """Build CONFIG section for API test scenario."""
        # Use provided base_url or fallback to localhost
        if base_url is None:
            base_url = 'http://localhost:8101'
            if hasattr(self, 'profile') and self.profile and hasattr(self.profile, 'config'):
                base_url = self.profile.config.get('base_url', base_url)
        return [
            "CONFIG[5]{key, value}:",
            f"  base_url, {base_url}",
            "  timeout_ms, 10000",
            "  retry_count, 3",
            "  retry_backoff_ms, 1000",
            f"  detected_frameworks, {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_preamble(self, base_url: str) -> list[str]:
        """Build preamble with WAIT and health check."""
        return [
            "# Wait for service to be ready",
            "WAIT 1000",
            "",
            "# Health check",
            "API GET /api/health 200",
            "ASSERT_STATUS 200",
            "",
        ]

    def _build_api_test_captures(self) -> list[str]:
        """Build CAPTURE section for dynamic values from responses."""
        return [
            "# Capture useful values from responses for subsequent tests",
            "# CAPTURE request_id FROM 'headers.x-request-id'",
            "# CAPTURE session_token FROM 'body.token'",
            "",
        ]

    def _build_rest_section(self, routes: list[dict]) -> list[str]:
        """Build REST API section lines."""
        unique_routes = self._deduplicate_rest_routes(routes)
        if not unique_routes:
            return []
        lines = [
            f"# REST API Endpoints ({len(unique_routes)} unique)",
            f"API[{len(unique_routes[:25])}]{{method, endpoint, expected_status}}:",
        ]
        for route in unique_routes[:25]:
            expected = 200 if route['method'] == 'GET' else 201
            lines.append(f"  {route['method']}, {route['path']}, {expected}")
        lines.append("")
        return lines

    def _build_graphql_section(self, routes: list[dict]) -> list[str]:
        """Build GraphQL section lines."""
        lines = [
            f"# GraphQL Endpoints ({len(routes)} detected)",
            f"GRAPHQL[{len(routes[:10])}]{{query, variables}}:",
        ]
        for route in routes[:10]:
            lines.append(f"  {route.get('handler', 'query')}, {{}}")
        lines.append("")
        return lines

    def _build_websocket_section(self, routes: list[dict]) -> list[str]:
        """Build WebSocket section lines."""
        lines = [
            f"# WebSocket Endpoints ({len(routes)} detected)",
            f"WEBSOCKET[{len(routes[:5])}]{{url, action}}:",
        ]
        for route in routes[:5]:
            lines.append(f"  ws://localhost:8101{route['path']}, connect")
        lines.append("")
        return lines

    def _build_api_test_endpoints(self, routes: list[dict]) -> list[str]:
        """Build endpoint sections for API test scenario."""
        sections: list[str] = []
        rest_routes = [r for r in routes if r.get('endpoint_type') == 'rest']
        graphql_routes = [r for r in routes if r.get('endpoint_type') == 'graphql']
        ws_routes = [r for r in routes if r.get('endpoint_type') == 'websocket']
        if rest_routes:
            sections.extend(self._build_rest_section(rest_routes))
        if graphql_routes:
            sections.extend(self._build_graphql_section(graphql_routes))
        if ws_routes:
            sections.extend(self._build_websocket_section(ws_routes))
        return sections

    def _deduplicate_rest_routes(self, routes: list[dict]) -> list[dict]:
        """Remove duplicate REST routes, excluding parameterized paths."""
        unique_routes = []
        seen = set()

        for r in routes:
            key = (r['method'], r['path'])
            if key not in seen and '{' not in r['path']:
                seen.add(key)
                unique_routes.append(r)

        return unique_routes

    def _build_api_test_assertions(self) -> list[str]:
        """Build assertions section for API test scenario."""
        return [
            "ASSERT[2]{field, operator, expected}:",
            "  _status, <, 500",
            "  _status, >=, 200",
        ]

    def _build_api_test_flow(self) -> list[str]:
        """Build FLOW section for conditional execution and error handling."""
        return [
            "",
            "# Conditional flow for error handling",
            "FLOW[2]{condition, action}:",
            "  _status >= 500, LOG 'Server error detected'",
            "  _status == 429, WAIT 2000  # Rate limit - wait and retry",
            "",
        ]

    def _build_api_test_summary(self, routes: list[dict]) -> list[str]:
        """Build summary section for API test scenario."""
        # Group routes by framework for summary
        routes_by_framework: dict[str, list] = {}
        for r in routes:
            fw = r.get('framework', 'unknown')
            if fw not in routes_by_framework:
                routes_by_framework[fw] = []
            routes_by_framework[fw].append(r)

        sections = []
        if routes_by_framework:
            sections.append("")
            sections.append("# Summary by Framework:")
            for fw, fw_routes in routes_by_framework.items():
                sections.append(f"#   {fw}: {len(fw_routes)} endpoints")

        return sections

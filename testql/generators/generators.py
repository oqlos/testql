"""Test generation mixins for different test types.

This module provides specialized generators for:
- API tests (smoke tests, integration tests)
- Tests derived from existing Python tests
- Tests derived from OQL/CQL scenarios
- CLI, library, frontend, and hardware tests
"""

from __future__ import annotations

import urllib.request
import urllib.error
from pathlib import Path

from .sources.pytest_source import PytestParser
from .sources.oql_source import OqlParser


class APIGeneratorMixin:
    """Mixin for generating API-focused test scenarios."""

    def _generate_api_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate comprehensive API tests from discovered routes."""
        routes = self.profile.config.get('discovered_routes', [])
        frameworks = self.profile.config.get('endpoint_frameworks', [])

        if not routes:
            return None

        validate_url = self.profile.config.get('validate_url')
        if validate_url:
            routes = self._validate_endpoints(routes, validate_url)
            if not routes:
                return None

        sections = self._build_api_test_header(frameworks)
        sections.extend(self._build_api_test_config(frameworks))
        sections.extend(self._build_api_test_endpoints(routes))
        sections.extend(self._build_api_test_assertions())
        sections.extend(self._build_api_test_summary(routes))

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-api-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _validate_endpoints(self, routes: list[dict], base_url: str) -> list[dict]:
        """Validate endpoints by pinging them and returning only the valid ones."""
        import sys
        
        valid_routes = []
        # Print directly to stderr to avoid mixing with stdout payload
        sys.stderr.write(f"🔍 Validating {len(routes)} endpoints against {base_url}...\n")
        
        for route in routes:
            path = route.get('path', '')
            method = route.get('method', 'GET')
            # Skip parameterized routes for simple validation
            if '{' in path or '<' in path:
                continue
                
            url = f"{base_url.rstrip('/')}{path}"
            try:
                # Use a fast timeout (2s)
                req = urllib.request.Request(url, method=method)
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status < 400 or resp.status in (401, 403, 405): 
                        # 401/403 means it exists but requires auth, 405 means method not allowed but endpoint exists
                        valid_routes.append(route)
            except urllib.error.HTTPError as e:
                # If it's a 404, it means it's not implemented or wrong path
                if e.code != 404:
                    valid_routes.append(route)
            except Exception:
                # Connection error, timeout, etc. We'll be strict and exclude it
                pass
                
        sys.stderr.write(f"✅ Validation complete: {len(valid_routes)} valid endpoints found.\n")
        return valid_routes

    def _build_api_test_header(self, frameworks: list[str]) -> list[str]:
        """Build header section for API test scenario."""
        return [
            "# SCENARIO: Auto-generated API Smoke Tests",
            "# TYPE: api",
            "# GENERATED: true",
            f"# DETECTORS: {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_config(self, frameworks: list[str]) -> list[str]:
        """Build CONFIG section for API test scenario."""
        return [
            "CONFIG[5]{key, value}:",
            "  base_url, ${api_url:-http://localhost:8100}",
            "  timeout_ms, 10000",
            "  retry_count, 3",
            "  retry_backoff_ms, 1000",
            f"  detected_frameworks, {', '.join(frameworks)}",
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
            "  status, <, 500",
            "  response_time, <, 2000",
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


class PythonTestGeneratorMixin:
    """Mixin for generating tests from existing Python tests."""

    def _generate_from_python_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate tests from existing Python test patterns."""
        patterns = [p for p in self.profile.test_patterns if p.pattern_type in ('api', 'e2e')]
        if not patterns:
            return None

        sections = [
            "# SCENARIO: Auto-generated from Python Tests",
            "# TYPE: integration",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            "  base_url, ${api_url:-http://localhost:8101}",
            "  timeout_ms, 10000",
            "",
        ]

        api_commands = []
        for p in patterns:
            for cmd in p.commands:
                if cmd.get('type') == 'api':
                    api_commands.append(cmd)

        if api_commands:
            sections.append(f"# Converted {len(api_commands)} API calls from pytest")
            sections.append(f"API[{len(api_commands)}]{{method, endpoint, expected_status}}:")
            for cmd in api_commands:
                sections.append(f"  {cmd['method']}, {cmd['path']}, 200")
            sections.append("")

        all_assertions = []
        for p in patterns:
            for ast_assert in p.assertions:
                expr = ast_assert.get('expression', '')
                if '==' in expr:
                    parts = expr.split('==')
                    left = parts[0].replace('assert ', '').strip()
                    right = parts[1].strip()
                    all_assertions.append((left, '==', right))
                elif '!=' in expr:
                    parts = expr.split('!=')
                    left = parts[0].replace('assert ', '').strip()
                    right = parts[1].strip()
                    all_assertions.append((left, '!=', right))

        if all_assertions:
            sections.append(f"# Converted {len(all_assertions)} assertions from pytest")
            sections.append(f"ASSERT[{len(all_assertions)}]{{field, operator, expected}}:")
            for left, op, right in all_assertions:
                # Clean up response.json() or response.status_code to TestQL friendly fields
                field = left
                if 'status_code' in left:
                    field = 'status'
                elif 'json()' in left:
                    field = 'body'
                sections.append(f"  {field}, {op}, {right}")
            sections.append("")

        if not api_commands and not all_assertions:
            sections.append("# NOTE: Python pytest files were detected but no convertible HTTP calls or assertions were found.")
            sections.append("# To run pytest tests directly, use: pytest <test_file>")
            sections.append("")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-pytests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file


class ScenarioGeneratorMixin:
    """Mixin for generating tests from OQL/CQL scenarios."""

    def _generate_from_scenarios(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate tests from existing OQL/CQL scenarios."""
        scenario_files = self.profile.discovered_files.get('scenarios_oql', [])
        if not scenario_files:
            return None

        parser = OqlParser()
        all_scenarios = []
        for sf in scenario_files[:10]:
            try:
                scenario = parser.parse_file(sf)
                if scenario:
                    all_scenarios.append(scenario)
            except Exception:
                continue

        if not all_scenarios:
            return None

        sections = [
            "# SCENARIO: Auto-generated from OQL/CQL Scenarios",
            "# TYPE: hardware",
            "# GENERATED: true",
            "",
        ]

        # Generate CONFIG
        all_config = {'generated_from': 'oql_scenarios', 'timeout_ms': '10000'}
        for scenario in all_scenarios:
            all_config.update(scenario.config)

        sections.append(f"CONFIG[{len(all_config)}]{{key, value}}:")
        for k, v in all_config.items():
            sections.append(f"  {k}, {v}")
        sections.append("")

        # Convert commands
        all_steps = []
        for scenario in all_scenarios:
            for cmd in scenario.test_commands:
                iql = self._convert_oql_command(cmd)
                if iql:
                    all_steps.append(iql)

        if all_steps:
            sections.append(f"# Converted {len(all_steps)} commands")
            for step in all_steps[:25]:
                sections.append(step)
            sections.append("")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-scenarios.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _convert_oql_command(self, cmd) -> str | None:
        """Convert OQL command to IQL."""
        cmd_type = cmd.command.upper()
        if cmd_type == 'WAIT':
            return f"WAIT {cmd.target}"
        elif cmd_type == 'ENCODER_ON':
            return "ENCODER_ON"
        elif cmd_type == 'ENCODER_OFF':
            return "ENCODER_OFF"
        elif cmd_type == 'ENCODER_STATUS':
            return "ENCODER_STATUS"
        elif cmd_type == 'LOG':
            return f'LOG "{cmd.target}"'
        elif cmd_type == 'EXEC':
            return f'SHELL "{cmd.target}"'
        return None


class SpecializedGeneratorMixin:
    """Mixin for generating specialized test types."""

    def _generate_api_integration_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate API integration tests."""
        sections = [
            "# SCENARIO: API Integration Tests",
            "# TYPE: api",
            "# GENERATED: true",
            "",
            "CONFIG[3]{key, value}:",
            "  base_url, http://localhost:8101",
            "  timeout_ms, 30000",
            "  retry_count, 3",
            "",
            "API[4]{method, endpoint, expected_status}:",
            "  GET, /health, 200",
            "  GET, /api/v1/status, 200",
            "  POST, /api/v1/test, 201",
            "  GET, /api/v1/docs, 200",
            "",
            "ASSERT[2]{field, operator, expected}:",
            "  status, ==, ok",
            "  response_time, <, 1000",
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-api-integration.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_cli_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate CLI tests with real shell commands."""
        sections = [
            "# SCENARIO: CLI Command Tests",
            "# TYPE: cli",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            f"  cli_command, python -m {self.profile.name}",
            "  timeout_ms, 10000",
            "",
            "# Test 1: CLI help command",
            f'SHELL "python -m {self.profile.name} --help" 5000',
            'ASSERT_EXIT_CODE 0',
            'ASSERT_STDOUT_CONTAINS "usage"',
            "",
            "# Test 2: CLI version command",
            f'SHELL "python -m {self.profile.name} --version" 5000',
            'ASSERT_EXIT_CODE 0',
            "",
            "# Test 3: CLI main workflow (dry-run)",
            f'SHELL "python -m {self.profile.name} --help" 10000',
            'ASSERT_EXIT_CODE 0',
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-cli-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_lib_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate library unit tests with real pytest commands."""
        sections = [
            "# SCENARIO: Library Unit Tests",
            "# TYPE: unit",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            f"  module_name, {self.profile.name}",
            "  timeout_ms, 60000",
            "",
            "# Test 1: Verify module can be imported",
            f'UNIT_IMPORT "{self.profile.name}"',
            "",
            "# Test 2: Run existing pytest tests if tests/ directory exists",
            'UNIT_PYTEST_DISCOVER "tests/" 60000',
            "",
            "# Test 3: Assert core function behavior (example)",
            'UNIT_ASSERT "len" "[[1,2,3,4]]" "4"',
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-unit-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_frontend_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate frontend/GUI tests with real GUI commands."""
        sections = [
            "# SCENARIO: Frontend E2E Tests",
            "# TYPE: gui",
            "# GENERATED: true",
            "",
            "CONFIG[3]{key, value}:",
            "  base_url, http://localhost:5173",
            "  gui_driver, playwright",
            "  timeout_ms, 30000",
            "",
            "# Test 1: Start application and navigate",
            'GUI_START "${base_url}"',
            "",
            "# Test 2: Interact with UI elements",
            'GUI_CLICK "[data-testid=main-button]"',
            'GUI_INPUT "[data-testid=search]" "test query"',
            'GUI_CLICK "[data-testid=submit]"',
            "",
            "# Test 3: Verify elements",
            'GUI_ASSERT_VISIBLE "[data-testid=results]"',
            'GUI_ASSERT_TEXT "[data-testid=results]" "test"',
            "",
            "# Test 4: Screenshot",
            'GUI_CAPTURE "" "e2e-screenshot.png"',
            "",
            "# Test 5: Cleanup",
            'GUI_STOP',
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-frontend-e2e.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_hardware_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate hardware/firmware tests."""
        sections = [
            "# SCENARIO: Hardware Smoke Tests",
            "# TYPE: hardware",
            "# GENERATED: true",
            "",
            "CONFIG[4]{key, value}:",
            "  hardware_url, http://localhost:8202",
            "  timeout_ms, 10000",
            "  auto_start_firmware, true",
            "  retry_count, 3",
            "",
            "API[2]{method, endpoint, expected_status}:",
            "  GET, /api/v1/hardware/health, 200",
            "  GET, /api/v1/hardware/identify, 200",
            "",
            "HARDWARE[3]{command, peripheral}:",
            "  check, piadc",
            "  check, motor-dri0050",
            "  check, modbus-io",
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-hardware-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

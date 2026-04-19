"""Test generation mixins for different test types.

This module provides specialized generators for:
- API tests (smoke tests, integration tests)
- Tests derived from existing Python tests
- Tests derived from OQL/CQL scenarios
- CLI, library, frontend, and hardware tests
"""

from __future__ import annotations

from pathlib import Path


class APIGeneratorMixin:
    """Mixin for generating API-focused test scenarios."""

    def _generate_api_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate comprehensive API tests from discovered routes."""
        routes = self.profile.config.get('discovered_routes', [])
        frameworks = self.profile.config.get('endpoint_frameworks', [])

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
            "CONFIG[4]{key, value}:",
            "  base_url, http://localhost:8101",
            "  timeout_ms, 10000",
            "  retry_count, 3",
            f"  detected_frameworks, {', '.join(frameworks)}",
            "",
        ]

    def _build_api_test_endpoints(self, routes: list[dict]) -> list[str]:
        """Build endpoint sections for API test scenario."""
        sections = []

        # Group by endpoint type
        rest_routes = [r for r in routes if r.get('endpoint_type') == 'rest']
        graphql_routes = [r for r in routes if r.get('endpoint_type') == 'graphql']
        ws_routes = [r for r in routes if r.get('endpoint_type') == 'websocket']

        # REST API endpoints
        if rest_routes:
            unique_routes = self._deduplicate_rest_routes(rest_routes)
            if unique_routes:
                sections.append(f"# REST API Endpoints ({len(unique_routes)} unique)")
                sections.append(f"API[{len(unique_routes[:25])}]{{method, endpoint, expected_status}}:")
                for route in unique_routes[:25]:
                    expected = 200 if route['method'] == 'GET' else 201
                    sections.append(f"  {route['method']}, {route['path']}, {expected}")
                sections.append("")

        # GraphQL endpoints
        if graphql_routes:
            sections.append(f"# GraphQL Endpoints ({len(graphql_routes)} detected)")
            sections.append(f"GRAPHQL[{len(graphql_routes[:10])}]{{query, variables}}:")
            for route in graphql_routes[:10]:
                handler = route.get('handler', 'query')
                sections.append(f'  {handler}, {{}}')
            sections.append("")

        # WebSocket endpoints
        if ws_routes:
            sections.append(f"# WebSocket Endpoints ({len(ws_routes)} detected)")
            sections.append(f"WEBSOCKET[{len(ws_routes[:5])}]{{url, action}}:")
            for route in ws_routes[:5]:
                sections.append(f'  ws://localhost:8101{route["path"]}, connect')
            sections.append("")

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
        ]

        # Group by type
        api_patterns = [p for p in patterns if p.pattern_type == 'api']
        other_patterns = [p for p in patterns if p.pattern_type != 'api']

        if api_patterns:
            sections.append(f"LOG[{len(api_patterns)}]{{message}}:")
            for p in api_patterns[:10]:
                sections.append(f'  "Test: {p.name}"')
            sections.append("")

        if other_patterns:
            sections.append(f"INCLUDE[{len(other_patterns)}]{{file}}:")
            for p in other_patterns[:5]:
                sections.append(f'  "{p.metadata.get("source_file", "unknown")}"')

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-pytests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file


class ScenarioGeneratorMixin:
    """Mixin for generating tests from OQL/CQL scenarios."""

    def _generate_from_scenarios(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate tests from existing OQL/CQL scenarios."""
        scenarios = self.profile.config.get('scenario_patterns', [])
        if not scenarios:
            return None

        sections = [
            "# SCENARIO: Auto-generated from OQL/CQL Scenarios",
            "# TYPE: hardware",
            "# GENERATED: true",
            "",
            "CONFIG[1]{key, value}:",
            "  generated_from, oql_scenarios",
            "",
            f"LOG[{len(scenarios)}]{{message}}:",
        ]

        for s in scenarios[:10]:
            sections.append(f'  "Scenario: {s["name"]}"')

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-scenarios.testql.toon.yaml'
        output_file.write_text(content)

        return output_file


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
        """Generate CLI tests."""
        sections = [
            "# SCENARIO: CLI Command Tests",
            "# TYPE: cli",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            f"  cli_command, python -m {self.profile.name}",
            "  timeout_ms, 10000",
            "",
            "LOG[3]{message}:",
            '  "Test CLI help command"',
            '  "Test CLI version command"',
            '  "Test CLI main workflow"',
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-cli-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_lib_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate library unit tests."""
        sections = [
            "# SCENARIO: Library Unit Tests",
            "# TYPE: unit",
            "# GENERATED: true",
            "",
            "LOG[2]{message}:",
            '  "Test core functions"',
            '  "Test public API surface"',
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-unit-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_frontend_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate frontend/GUI tests."""
        sections = [
            "# SCENARIO: Frontend E2E Tests",
            "# TYPE: gui",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            "  base_url, http://localhost:5173",
            "  browser, chromium",
            "",
            "NAVIGATE[1]{url}:",
            "  /",
            "",
            "GUI[3]{action, selector}:",
            "  click, [data-testid=main-button]",
            "  input, [data-testid=search] test",
            "  click, [data-testid=submit]",
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
            "CONFIG[3]{key, value}:",
            "  firmware_url, http://localhost:8202",
            "  timeout_ms, 10000",
            "  auto_start_firmware, true",
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

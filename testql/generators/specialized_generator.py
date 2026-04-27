"""Specialized test generation mixin.

This module provides specialized generators for CLI, library, frontend, and hardware tests.
"""

from __future__ import annotations

from pathlib import Path


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
            "# NOTE: Requires hardware service running at hardware_url",
            "#       Hardware endpoints should respond at /api/v1/hardware/{peripheral}",
            "",
            "CONFIG[4]{key, value}:",
            "  hardware_url, http://localhost:8202",
            "  timeout_ms, 10000",
            "  auto_start_firmware, true",
            "  retry_count, 3",
            "",
            "# Health check - verifies hardware service is running",
            "API[2]{method, endpoint, expected_status}:",
            "  GET, /health, 200",
            "  GET, /api/v1/hardware/health, 200",
            "",
            "# Hardware peripheral checks - requires hardware service",
            "# Available commands: check, status, reset, configure",
            "# HARDWARE[3]{command, peripheral}:",
            "#   check, piadc",
            "#   check, motor-dri0050",
            "#   check, modbus-io",
        ]

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-hardware-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

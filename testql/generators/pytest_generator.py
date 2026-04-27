"""Python test generation mixin.

This module provides specialized generator for tests derived from existing Python tests.
"""

from __future__ import annotations

import re
from pathlib import Path


class PythonTestGeneratorMixin:
    """Mixin for generating tests from existing Python tests."""

    def _generate_from_python_tests(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate tests from existing Python test patterns."""
        patterns = [p for p in self.profile.test_patterns if p.pattern_type in ('api', 'e2e')]
        if not patterns:
            return None

        sections = self._build_test_header()
        
        api_commands = self._extract_api_commands(patterns)
        sections.extend(self._build_api_section(api_commands))
        
        all_assertions = self._extract_assertions(patterns)
        sections.extend(self._build_assertions_section(all_assertions))
        
        if not api_commands and not all_assertions:
            sections.extend(self._build_no_conversions_note())

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-pytests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _build_test_header(self) -> list[str]:
        """Build the header section for generated test file."""
        return [
            "# SCENARIO: Auto-generated from Python Tests",
            "# TYPE: integration",
            "# GENERATED: true",
            "",
            "CONFIG[2]{key, value}:",
            "  base_url, ${api_url:-http://localhost:8101}",
            "  timeout_ms, 10000",
            "",
        ]

    def _extract_api_commands(self, patterns: list) -> list[dict]:
        """Extract API commands from test patterns."""
        api_commands = []
        for p in patterns:
            for cmd in p.commands:
                if cmd.get('type') == 'api':
                    api_commands.append(cmd)
        return api_commands

    def _build_api_section(self, api_commands: list[dict]) -> list[str]:
        """Build the API section of the test file."""
        if not api_commands:
            return []
        
        sections = [
            f"# Converted {len(api_commands)} API calls from pytest",
            f"API[{len(api_commands)}]{{method, endpoint, expected_status}}:",
        ]
        for cmd in api_commands:
            sections.append(f"  {cmd['method']}, {cmd['path']}, 200")
        sections.append("")
        return sections

    def _extract_assertions(self, patterns: list) -> list[tuple[str, str, str]]:
        """Extract assertions from test patterns."""
        all_assertions = []
        for p in patterns:
            for ast_assert in p.assertions:
                expr = ast_assert.get('expression', '')
                assertion = self._parse_assertion_expression(expr)
                if assertion:
                    all_assertions.append(assertion)
        return all_assertions

    def _parse_assertion_expression(self, expr: str) -> tuple[str, str, str] | None:
        """Parse a single assertion expression."""
        if '==' in expr:
            parts = expr.split('==')
            left = parts[0].replace('assert ', '').strip()
            right = parts[1].split(',')[0].strip()
            return (left, '==', right)
        elif '!=' in expr:
            parts = expr.split('!=')
            left = parts[0].replace('assert ', '').strip()
            right = parts[1].strip()
            return (left, '!=', right)
        return None

    def _build_assertions_section(self, assertions: list[tuple[str, str, str]]) -> list[str]:
        """Build the assertions section of the test file."""
        if not assertions:
            return []
        
        sections = [
            f"# Converted {len(assertions)} assertions from pytest",
            f"ASSERT[{len(assertions)}]{{field, operator, expected}}:",
        ]
        for left, op, right in assertions:
            field = self._normalize_assertion_field(left)
            sections.append(f"  {field}, {op}, {right}")
        sections.append("")
        return sections

    def _build_no_conversions_note(self) -> list[str]:
        """Build a note when no conversions were possible."""
        return [
            "# NOTE: Python pytest files were detected but no convertible HTTP calls or assertions were found.",
            "# To run pytest tests directly, use: pytest <test_file>",
            "",
        ]

    def _normalize_assertion_field(self, field: str) -> str:
        """Normalize assertion field to TestQL-friendly format."""
        # Clean up response.json() or response.status_code to TestQL friendly fields
        if 'status_code' in field:
            field = '_status'
        elif 'json()' in field:
            field = field.split('json()')[-1].strip('[]"\' .') or 'body'
        
        # Cleanup common dictionary access patterns (e.g. data["key"] -> data.key)
        field = field.replace('["', '.').replace('"]', '').replace("['", '.').replace("']", '')
        
        # Cleanup .get("key") patterns
        field = re.sub(r'\.get\([\'"]([^\'"]+)[\'"]\)', r'.\1', field)
        
        # Remove prefixes like 'data.', 'body.', 'response.' if they are common roots
        for root in ('data.', 'body.', 'response.', 'resp.', 'c.', 'obj.'):
            if field.startswith(root):
                field = field[len(root):]
        
        # Final cleanup of leading/trailing dots and quotes
        field = field.strip('."\' ')
        
        if not field:
            field = 'body'

        return field

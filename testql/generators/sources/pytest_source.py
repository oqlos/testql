"""Convert Python/pytest test files into Unified IR for TestQL.

Parses Python test files using AST and converts them to OQL commands.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testql.ir import TestPlan, ScenarioMetadata

from .base import BaseSource, SourceLike


@dataclass
class ParsedTest:
    """Represents a single parsed test function."""
    name: str
    class_name: str | None
    source_file: Path
    docstring: str | None
    setup_steps: list[dict] = field(default_factory=list)
    test_steps: list[dict] = field(default_factory=list)
    assertions: list[dict] = field(default_factory=list)
    teardown_steps: list[dict] = field(default_factory=list)
    fixtures: list[str] = field(default_factory=list)


class PytestParser:
    """Parse pytest test files into structured test definitions."""

    # HTTP-related function patterns
    HTTP_PATTERNS = [
        r'requests\.(get|post|put|delete|patch)\s*\(',
        r'client\.(get|post|put|delete|patch)\s*\(',
        r'session\.(get|post|put|delete|patch)\s*\(',
        r'\.get\s*\([\'"]\/',
        r'\.post\s*\([\'"]\/',
    ]

    # Assertion patterns
    ASSERT_PATTERNS = {
        'status': r'assert.*status\s*(==|!=|<=|>=|<|>)\s*(\d+)',
        'contains': r'assert.*in\s+.*response',
        'equals': r'assert\s+.+\s*==\s*.+',
        'true': r'assert\s+\w+\s*$',
        'false': r'assert\s+not\s+\w+',
    }

    def parse_file(self, file_path: Path | str) -> list[ParsedTest]:
        """Parse a single Python test file."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        try:
            content = path.read_text(encoding='utf-8')
            tree = ast.parse(content)
        except (SyntaxError, UnicodeDecodeError) as e:
            return []

        tests = []
        source_lines = content.split('\n')

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                tests.append(self._parse_test_function(node, source_lines, path))
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        tests.append(self._parse_test_function(
                            item, source_lines, path, class_name=node.name
                        ))

        return tests

    def _parse_test_function(
        self,
        node: ast.FunctionDef,
        source_lines: list[str],
        file_path: Path,
        class_name: str | None = None
    ) -> ParsedTest:
        """Parse a single test function AST node."""
        test_source = '\n'.join(source_lines[node.lineno-1:node.end_lineno])

        test = ParsedTest(
            name=node.name,
            class_name=class_name,
            source_file=file_path,
            docstring=ast.get_docstring(node),
            fixtures=self._extract_fixtures(node),
        )

        # Parse body for steps and assertions
        test.setup_steps, test.test_steps, test.assertions = self._parse_body(
            node, source_lines
        )

        return test

    def _extract_fixtures(self, node: ast.FunctionDef) -> list[str]:
        """Extract pytest fixture names from function arguments."""
        fixtures = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name) and decorator.func.id == 'pytest.fixture':
                    continue
        # Extract from arguments (pytest fixtures are typically arguments)
        for arg in node.args.args:
            fixture_name = arg.arg
            # Skip common non-fixture parameters
            if fixture_name not in ('self', 'cls', 'request'):
                fixtures.append(fixture_name)
        return fixtures

    def _parse_body(
        self,
        node: ast.FunctionDef,
        source_lines: list[str]
    ) -> tuple[list[dict], list[dict], list[dict]]:
        """Parse function body into setup steps, test steps, and assertions."""
        setup_steps: list[dict] = []
        test_steps: list[dict] = []
        assertions: list[dict] = []

        in_setup = True  # Assume setup until we hit first assertion

        for stmt in node.body:
            stmt_source = self._get_source_segment(stmt, source_lines)
            if not stmt_source:
                continue

            # Check for assertions
            if isinstance(stmt, ast.Assert):
                in_setup = False
                assertions.append(self._parse_assertion(stmt, stmt_source))
            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                call_info = self._parse_call(stmt.value, stmt_source)
                if in_setup and call_info.get('type') == 'api':
                    setup_steps.append(call_info)
                elif call_info.get('type') == 'api':
                    test_steps.append(call_info)
                elif call_info.get('type') == 'fixture':
                    setup_steps.append(call_info)
            elif isinstance(stmt, ast.Assign):
                # Variable assignment - could be setup
                assign_info = self._parse_assignment(stmt, stmt_source)
                if in_setup:
                    setup_steps.append(assign_info)

        return setup_steps, test_steps, assertions

    def _get_source_segment(self, node: ast.AST, source_lines: list[str]) -> str | None:
        """Extract source code for an AST node."""
        try:
            if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                return '\n'.join(source_lines[node.lineno-1:node.end_lineno])
        except Exception:
            pass
        return None

    def _parse_assertion(self, node: ast.Assert, source: str) -> dict:
        """Parse an assertion into structured format."""
        result = {'type': 'assert', 'source': source.strip()}

        # Check for status code assertions
        status_match = re.search(self.ASSERT_PATTERNS['status'], source, re.IGNORECASE)
        if status_match:
            result['assert_type'] = 'status'
            result['operator'] = status_match.group(1)
            result['expected'] = int(status_match.group(2))
            return result

        # Check for contains assertions
        if re.search(self.ASSERT_PATTERNS['contains'], source, re.IGNORECASE):
            result['assert_type'] = 'contains'
            return result

        # Default to equals
        result['assert_type'] = 'equals'
        return result

    def _parse_call(self, node: ast.Call, source: str) -> dict:
        """Parse a function call into structured format."""
        result = {'type': 'call', 'source': source.strip()}

        # Check for HTTP calls
        for pattern in self.HTTP_PATTERNS:
            match = re.search(pattern, source, re.IGNORECASE)
            if match:
                result['type'] = 'api'
                result['method'] = match.group(1).upper() if match.groups() else 'GET'
                # Try to extract URL
                url_match = re.search(r'[\'\"]([^\'\"]+)[\'\"]', source)
                if url_match:
                    result['url'] = url_match.group(1)
                return result

        # Check for fixture usage
        if isinstance(node.func, ast.Name):
            result['function'] = node.func.id
            if result['function'] in ('setup_function', 'setup_module', 'teardown'):
                result['type'] = 'fixture'

        return result

    def _parse_assignment(self, node: ast.Assign, source: str) -> dict:
        """Parse an assignment statement."""
        return {'type': 'assign', 'source': source.strip()}


@dataclass
class PytestSource(BaseSource):
    """Source adapter for pytest files - converts to Unified IR."""

    name: str = "pytest"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".py",))

    def load(self, source: SourceLike) -> TestPlan:
        """Load pytest file and convert to TestPlan IR."""
        scenarios = self.ingest(source)

        # Convert first scenario to TestPlan
        if scenarios:
            scenario = scenarios[0]
            metadata = ScenarioMetadata(
                name=scenario.get('metadata', {}).get('name', 'pytest-scenario'),
                type=scenario.get('metadata', {}).get('type', 'integration'),
            )
            return TestPlan(
                metadata=metadata,
                config=scenario.get('config', {}),
                steps=[],  # Would need proper Step conversion
            )

        return TestPlan(metadata=ScenarioMetadata(name="empty", type="integration"))

    def ingest(self, path: SourceLike) -> list[dict]:
        """Ingest pytest files and convert to Unified IR.

        Returns list of test scenarios in IR format.
        """
        file_path = Path(path) if isinstance(path, str) else path
        if not file_path.exists():
            return []

        parser = PytestParser()

        if file_path.is_file():
            tests = parser.parse_file(file_path)
        else:
            # Scan directory for test files
            tests = []
            for pattern in ['**/test_*.py', '**/tests/**/*.py']:
                for test_file in file_path.rglob(pattern):
                    tests.extend(parser.parse_file(test_file))

        # Convert to Unified IR
        scenarios = []
        for test in tests:
            scenario = self._to_unified_ir(test)
            if scenario:
                scenarios.append(scenario)

        return scenarios

    def _to_unified_ir(self, test: ParsedTest) -> dict | None:
        """Convert ParsedTest to Unified IR format."""
        if not test.test_steps and not test.assertions:
            return None

        ir = {
            'metadata': {
                'name': f"{test.class_name}_{test.name}" if test.class_name else test.name,
                'type': self._detect_test_type(test),
                'source': str(test.source_file),
                'docstring': test.docstring,
            },
            'config': {},
            'setup': [],
            'steps': [],
            'assertions': [],
            'teardown': [],
        }

        # Convert setup steps
        for step in test.setup_steps:
            if step.get('type') == 'api':
                ir['setup'].append({
                    'command': 'API',
                    'method': step.get('method', 'GET'),
                    'url': step.get('url', '/'),
                })

        # Convert test steps
        for step in test.test_steps:
            if step.get('type') == 'api':
                ir['steps'].append({
                    'command': 'API',
                    'method': step.get('method', 'GET'),
                    'url': step.get('url', '/'),
                })

        # Convert assertions
        for assertion in test.assertions:
            if assertion.get('assert_type') == 'status':
                ir['assertions'].append({
                    'command': 'ASSERT_STATUS',
                    'expected': assertion.get('expected', 200),
                })
            elif assertion.get('assert_type') == 'contains':
                ir['assertions'].append({
                    'command': 'ASSERT_CONTAINS',
                    'expected': '',  # Would need to extract from source
                })
            else:
                ir['assertions'].append({
                    'command': 'ASSERT_OK',
                })

        return ir

    def _detect_test_type(self, test: ParsedTest) -> str:
        """Detect test type from patterns."""
        source = str(test.source_file) + ' ' + (test.docstring or '')
        source_lower = source.lower()

        if 'api' in source_lower or 'http' in source_lower:
            return 'api'
        if 'gui' in source_lower or 'browser' in source_lower:
            return 'gui'
        if 'e2e' in source_lower or 'integration' in source_lower:
            return 'integration'
        if 'unit' in source_lower:
            return 'unit'
        return 'integration'  # Default

    def to_oql(self, ir: dict) -> list[str]:
        """Convert Unified IR to OQL commands."""
        lines = []

        # Header
        meta = ir.get('metadata', {})
        lines.append(f"# SCENARIO: {meta.get('name', 'Unnamed')}")
        lines.append(f"# TYPE: {meta.get('type', 'integration')}")
        lines.append("# GENERATED: true (from pytest)")
        if meta.get('docstring'):
            lines.append(f"# {meta.get('docstring')}")
        lines.append("")

        # Config
        config = ir.get('config', {})
        if config:
            lines.append(f"CONFIG[{len(config)}]{{key, value}}:")
            for k, v in config.items():
                lines.append(f"  {k}, {v}")
            lines.append("")

        # Setup
        setup = ir.get('setup', [])
        if setup:
            lines.append("# Setup steps")
            for step in setup:
                if step.get('command') == 'API':
                    lines.append(f"API {step.get('method', 'GET')} \"{step.get('url', '/')}\"")
            lines.append("")

        # Test steps
        steps = ir.get('steps', [])
        for step in steps:
            if step.get('command') == 'API':
                lines.append(f"API {step.get('method', 'GET')} \"{step.get('url', '/')}\"")

        # Assertions
        assertions = ir.get('assertions', [])
        if assertions:
            lines.append("")
            for assertion in assertions:
                cmd = assertion.get('command', 'ASSERT_OK')
                if cmd == 'ASSERT_STATUS':
                    lines.append(f"ASSERT_STATUS {assertion.get('expected', 200)}")
                elif cmd == 'ASSERT_CONTAINS':
                    lines.append(f'ASSERT_CONTAINS "{assertion.get("expected", "")}"')
                else:
                    lines.append("ASSERT_OK")

        return lines

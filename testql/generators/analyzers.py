"""Project analysis logic for TestQL generators.

This module handles project type detection, directory scanning,
test file analysis, configuration parsing, and route detection.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .base import BaseAnalyzer, TestPattern


class ProjectAnalyzer(BaseAnalyzer):
    """Analyzes project structure to discover testable patterns."""

    def detect_project_type(self) -> str:
        """Detect project type from files and structure."""
        files = list(self.project_path.iterdir())
        names = {f.name for f in files}

        # Check for web frontend
        if any(n in names for n in ['package.json', 'vite.config.js', 'index.html']):
            if 'playwright.config.js' in names or 'e2e' in names:
                return 'web-frontend'

        # Check for Python API/service
        if 'pyproject.toml' in names:
            content = (self.project_path / 'pyproject.toml').read_text(errors='ignore')
            if 'fastapi' in content.lower() or 'flask' in content.lower():
                return 'python-api'
            if 'click' in content.lower():
                return 'python-cli'
            return 'python-lib'

        # Check for hardware/firmware
        if any((self.project_path / d).exists() for d in ['scenarios', 'hardware', 'firmware']):
            return 'hardware'

        return 'mixed'

    def run_full_analysis(self) -> None:
        """Run complete project analysis."""
        self.profile.project_type = self.detect_project_type()
        self._scan_directory_structure()
        self._analyze_python_tests()
        self._analyze_config_files()
        self._analyze_api_routes()
        self._analyze_scenarios()

    def _scan_directory_structure(self) -> None:
        """Scan and categorize project files."""
        max_files_per_category = 100

        patterns = {
            'python_tests': ['**/test_*.py', '**/tests/**/*.py', '**/tests.py'],
            'python_source': ['**/*.py'],
            'config_yaml': ['**/*.yaml', '**/*.yml'],
            'config_json': ['**/*.json'],
            'config_toml': ['**/*.toml'],
            'scenarios_oql': ['**/*.oql', '**/*.cql', '**/*.tql'],
            'scenarios_testql': ['**/*.testql.toon.yaml'],
            'web_routes': ['**/routes/**/*', '**/pages/**/*'],
            'api_specs': ['**/openapi*.yaml', '**/swagger*.yaml', '**/api-spec*'],
        }

        for category, globs in patterns.items():
            count = 0
            for glob in globs:
                if count >= max_files_per_category:
                    break
                try:
                    for path in self.project_path.rglob(glob):
                        if self._should_exclude_path(path):
                            continue
                        self.profile.discovered_files[category].append(path)
                        count += 1
                        if count >= max_files_per_category:
                            break
                except Exception:
                    continue

    def _analyze_python_tests(self) -> None:
        """Analyze existing Python test files for patterns."""
        test_files = self.profile.discovered_files.get('python_tests', [])

        for test_file in test_files:
            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            pattern = self._extract_test_pattern(
                                node, content, source_file=test_file
                            )
                            if pattern:
                                self.profile.test_patterns.append(pattern)

                    elif isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                                pattern = self._extract_test_pattern(
                                    item, content, class_name=node.name, source_file=test_file
                                )
                                if pattern:
                                    self.profile.test_patterns.append(pattern)
            except SyntaxError:
                continue

    def _extract_test_pattern(
        self,
        node: ast.FunctionDef,
        content: str,
        class_name: str | None = None,
        source_file: Path | None = None
    ) -> TestPattern | None:
        """Extract test pattern from AST node."""
        name = f"{class_name}_{node.name}" if class_name else node.name

        source_lines = content.split('\n')[node.lineno-1:node.end_lineno]
        source = '\n'.join(source_lines)

        pattern_type = self._detect_pattern_type(name, source)
        commands, assertions = self._extract_commands_and_assertions(source_lines)

        source_file_name = source_file.stem if source_file else "unknown"
        return TestPattern(
            name=name,
            target=source_file_name,
            pattern_type=pattern_type,
            commands=commands,
            assertions=assertions,
            metadata={'source_file': str(source_file) if source_file else "unknown", 'line': node.lineno}
        )

    def _detect_pattern_type(self, name: str, source: str) -> str:
        """Detect the type of test pattern from name and source."""
        name_lower = name.lower()
        source_lower = source.lower()

        if 'api' in name_lower or 'http' in source_lower or 'requests' in source_lower:
            return 'api'
        if 'gui' in name_lower or 'browser' in source_lower or 'playwright' in source_lower:
            return 'gui'
        if 'e2e' in name_lower or 'integration' in name_lower:
            return 'e2e'
        return 'unit'

    def _extract_commands_and_assertions(
        self,
        source_lines: list[str]
    ) -> tuple[list[dict], list[dict]]:
        """Extract commands and assertions from source lines."""
        commands = []
        assertions = []

        for line in source_lines:
            line_stripped = line.strip()
            if line_stripped.startswith('assert'):
                assertions.append({'type': 'assert', 'expression': line_stripped})

        return commands, assertions

    def _analyze_config_files(self) -> None:
        """Analyze configuration files for testable settings."""
        config_data = {}

        for yaml_file in self.profile.discovered_files.get('config_yaml', []):
            try:
                import yaml
                content = yaml_file.read_text()
                data = yaml.safe_load(content)
                if data:
                    config_data[yaml_file.name] = data
            except Exception:
                continue

        for json_file in self.profile.discovered_files.get('config_json', []):
            try:
                content = json_file.read_text()
                data = json.loads(content)
                config_data[json_file.name] = data
            except json.JSONDecodeError:
                continue

        self.profile.config = config_data

    def _analyze_api_routes(self) -> None:
        """Analyze API routes using advanced endpoint detection."""
        try:
            from ..endpoint_detector import UnifiedEndpointDetector

            detector = UnifiedEndpointDetector(self.project_path)
            endpoints = detector.detect_all()

            route_patterns = []
            for ep in endpoints:
                route_patterns.append({
                    'method': ep.method.upper(),
                    'path': ep.path,
                    'source': str(ep.source_file),
                    'framework': ep.framework,
                    'endpoint_type': ep.endpoint_type,
                    'handler': ep.handler_name,
                    'summary': ep.summary,
                })

            self.profile.config['discovered_routes'] = route_patterns
            self.profile.config['endpoint_frameworks'] = detector.detectors_used
            self.profile.config['endpoint_objects'] = endpoints

        except Exception:
            self._analyze_api_routes_fallback()

    def _analyze_api_routes_fallback(self) -> None:
        """Fallback simple regex-based route detection."""
        route_patterns = []

        for py_file in self.profile.discovered_files.get('python_source', [])[:50]:
            try:
                content = py_file.read_text()

                # FastAPI route patterns
                fastapi_routes = re.findall(
                    r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
                    content, re.IGNORECASE
                )
                for method, path in fastapi_routes:
                    route_patterns.append({
                        'method': method.upper(),
                        'path': path,
                        'source': str(py_file)
                    })

            except Exception:
                continue

        self.profile.config['discovered_routes'] = route_patterns

    def _analyze_scenarios(self) -> None:
        """Analyze existing scenario files for patterns."""
        scenario_patterns = []

        for scenario_file in self.profile.discovered_files.get('scenarios_oql', []):
            try:
                content = scenario_file.read_text()

                # Extract SET commands
                set_matches = re.findall(r"SET\s+'([^']+)'\s+'([^']*)'", content)

                # Extract READ/CHECK commands
                read_matches = re.findall(r"(READ|CHECK)\s+'([^']+)'", content)

                scenario_patterns.append({
                    'file': str(scenario_file),
                    'name': scenario_file.stem,
                    'config_keys': [m[0] for m in set_matches],
                    'commands': [m[0] for m in read_matches],
                })

            except Exception:
                continue

        self.profile.config['scenario_patterns'] = scenario_patterns

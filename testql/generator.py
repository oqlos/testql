"""TestQL Generator — Automated test generation from project structures.

This module provides intelligent test generation capabilities that analyze:
- Existing test files (pytest, unittest)
- Project structure and source code
- Configuration files (YAML, JSON, TOML)
- API endpoints and routes
- Database schemas
- Hardware scenarios

The generators produce TestQL scenarios (*.testql.toon.yaml) that can be
executed by the TestQL interpreter.
"""

from __future__ import annotations

import ast
import json
import re
import os
import inspect
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable
from collections import defaultdict


@dataclass
class TestPattern:
    """Discovered test pattern from source code."""
    name: str
    target: str
    pattern_type: str  # 'api', 'gui', 'unit', 'integration', 'e2e'
    commands: list[dict]
    assertions: list[dict]
    metadata: dict = field(default_factory=dict)


@dataclass
class ProjectProfile:
    """Analyzed project profile."""
    name: str
    root_path: Path
    project_type: str  # 'python-api', 'python-lib', 'web-frontend', 'hardware', 'mixed'
    test_patterns: list[TestPattern] = field(default_factory=list)
    discovered_files: dict[str, list[Path]] = field(default_factory=lambda: defaultdict(list))
    config: dict = field(default_factory=dict)


class TestGenerator:
    """Base class for test generators."""

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.profile = ProjectProfile(
            name=self.project_path.name,
            root_path=self.project_path,
            project_type=self._detect_project_type()
        )

    def _detect_project_type(self) -> str:
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

    def analyze(self) -> ProjectProfile:
        """Run full project analysis."""
        self._scan_directory_structure()
        self._analyze_python_tests()
        self._analyze_config_files()
        self._analyze_api_routes()
        self._analyze_scenarios()
        return self.profile

    def _scan_directory_structure(self):
        """Scan and categorize project files."""
        exclude_dirs = {'.venv', 'venv', 'node_modules', '__pycache__', '.git', '.pytest_cache', '.ruff_cache', '.idea', 'dist', 'build'}
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

        def should_exclude(path: Path) -> bool:
            """Check if path should be excluded."""
            parts = set(path.parts)
            return bool(parts & exclude_dirs)

        for category, globs in patterns.items():
            count = 0
            for glob in globs:
                if count >= max_files_per_category:
                    break
                try:
                    for path in self.project_path.rglob(glob):
                        if should_exclude(path):
                            continue
                        self.profile.discovered_files[category].append(path)
                        count += 1
                        if count >= max_files_per_category:
                            break
                except Exception:
                    continue

    def _analyze_python_tests(self):
        """Analyze existing Python test files for patterns."""
        for test_file in self.profile.discovered_files.get('python_tests', []):
            try:
                content = test_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name.startswith('test_'):
                            pattern = self._extract_test_pattern(node, content, source_file=test_file)
                            if pattern:
                                self.profile.test_patterns.append(pattern)

                    elif isinstance(node, ast.ClassDef):
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                                pattern = self._extract_test_pattern(item, content, class_name=node.name, source_file=test_file)
                                if pattern:
                                    self.profile.test_patterns.append(pattern)
            except SyntaxError:
                continue

    def _extract_test_pattern(self, node: ast.FunctionDef, content: str, class_name: str = None, source_file: Path = None) -> TestPattern | None:
        """Extract test pattern from AST node."""
        name = f"{class_name}_{node.name}" if class_name else node.name

        # Look for API call patterns
        source_lines = content.split('\n')[node.lineno-1:node.end_lineno]
        source = '\n'.join(source_lines)

        # Detect pattern type
        pattern_type = 'unit'
        if 'api' in name.lower() or 'http' in source.lower() or 'requests' in source.lower():
            pattern_type = 'api'
        elif 'gui' in name.lower() or 'browser' in source.lower() or 'playwright' in source.lower():
            pattern_type = 'gui'
        elif 'e2e' in name.lower() or 'integration' in name.lower():
            pattern_type = 'e2e'

        # Extract commands from source
        commands = []
        assertions = []

        # Look for assert statements
        for line in source_lines:
            line_stripped = line.strip()
            if line_stripped.startswith('assert'):
                assertions.append({'type': 'assert', 'expression': line_stripped})

        source_file_name = source_file.stem if source_file else "unknown"
        return TestPattern(
            name=name,
            target=source_file_name,
            pattern_type=pattern_type,
            commands=commands,
            assertions=assertions,
            metadata={'source_file': str(source_file) if source_file else "unknown", 'line': node.lineno}
        )

    def _analyze_config_files(self):
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

    def _analyze_api_routes(self):
        """Analyze API routes from Python source files."""
        route_patterns = []

        for py_file in self.profile.discovered_files.get('python_source', [])[:50]:  # Limit for performance
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

                # Flask route patterns
                flask_routes = re.findall(
                    r'@app\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[([^\]]+)\]',
                    content, re.IGNORECASE
                )
                for path, methods in flask_routes:
                    for method in methods.replace("'", '"').replace(' ', '').split(','):
                        route_patterns.append({
                            'method': method.strip('"').upper(),
                            'path': path,
                            'source': str(py_file)
                        })

            except Exception:
                continue

        self.profile.config['discovered_routes'] = route_patterns

    def _analyze_scenarios(self):
        """Analyze existing scenario files for patterns."""
        scenario_patterns = []

        for scenario_file in self.profile.discovered_files.get('scenarios_oql', []):
            try:
                content = scenario_file.read_text()

                # Extract CONFIG blocks
                config_matches = re.findall(r"CONFIG:\s*(.*?)(?=\n\w|$)", content, re.DOTALL)

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

    def generate_tests(self, output_dir: str | Path | None = None) -> list[Path]:
        """Generate TestQL scenarios based on analysis."""
        if not self.profile.test_patterns and not self.profile.config:
            self.analyze()

        output_dir = Path(output_dir) if output_dir else self.project_path / 'testql-scenarios'
        output_dir.mkdir(exist_ok=True)

        generated_files = []

        # Generate from discovered routes
        if self.profile.config.get('discovered_routes'):
            file_path = self._generate_api_tests(output_dir)
            if file_path:
                generated_files.append(file_path)

        # Generate from existing Python tests
        if self.profile.test_patterns:
            file_path = self._generate_from_python_tests(output_dir)
            if file_path:
                generated_files.append(file_path)

        # Generate from scenarios
        if self.profile.config.get('scenario_patterns'):
            file_path = self._generate_from_scenarios(output_dir)
            if file_path:
                generated_files.append(file_path)

        # Generate project-specific tests
        generator_map = {
            'python-api': self._generate_api_integration_tests,
            'python-cli': self._generate_cli_tests,
            'python-lib': self._generate_lib_tests,
            'web-frontend': self._generate_frontend_tests,
            'hardware': self._generate_hardware_tests,
        }

        generator = generator_map.get(self.profile.project_type)
        if generator:
            file_path = generator(output_dir)
            if file_path:
                generated_files.append(file_path)

        return generated_files

    def _generate_api_tests(self, output_dir: Path) -> Path | None:
        """Generate API smoke tests from discovered routes."""
        routes = self.profile.config.get('discovered_routes', [])
        if not routes:
            return None

        sections = ["# SCENARIO: Auto-generated API Smoke Tests"]
        sections.append("# TYPE: api")
        sections.append("# GENERATED: true")
        sections.append("")

        # CONFIG section
        sections.append("CONFIG[2]{key, value}:")
        sections.append("  base_url, http://localhost:8101")
        sections.append("  timeout_ms, 5000")
        sections.append("")

        # API section
        unique_routes = []
        seen = set()
        for r in routes:
            key = (r['method'], r['path'])
            if key not in seen and '{' not in r['path']:  # Skip parameterized routes
                seen.add(key)
                unique_routes.append(r)

        sections.append(f"API[{len(unique_routes)}]{{method, endpoint, expected_status}}:")
        for route in unique_routes[:20]:  # Limit to 20 routes
            expected = 200 if route['method'] == 'GET' else 201
            sections.append(f"  {route['method']}, {route['path']}, {expected}")

        sections.append("")
        sections.append("ASSERT[1]{field, operator, expected}:")
        sections.append("  status, <, 400")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-api-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_from_python_tests(self, output_dir: Path) -> Path | None:
        """Generate tests from existing Python test patterns."""
        patterns = [p for p in self.profile.test_patterns if p.pattern_type in ('api', 'e2e')]
        if not patterns:
            return None

        sections = ["# SCENARIO: Auto-generated from Python Tests"]
        sections.append("# TYPE: integration")
        sections.append("# GENERATED: true")
        sections.append("")

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

    def _generate_from_scenarios(self, output_dir: Path) -> Path | None:
        """Generate tests from existing OQL/CQL scenarios."""
        scenarios = self.profile.config.get('scenario_patterns', [])
        if not scenarios:
            return None

        sections = ["# SCENARIO: Auto-generated from OQL/CQL Scenarios"]
        sections.append("# TYPE: hardware")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("CONFIG[1]{key, value}:")
        sections.append("  generated_from, oql_scenarios")
        sections.append("")

        sections.append(f"LOG[{len(scenarios)}]{{message}}:")
        for s in scenarios[:10]:
            sections.append(f'  "Scenario: {s["name"]}"')

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-scenarios.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_api_integration_tests(self, output_dir: Path) -> Path | None:
        """Generate API integration tests."""
        sections = ["# SCENARIO: API Integration Tests"]
        sections.append("# TYPE: api")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("CONFIG[3]{key, value}:")
        sections.append("  base_url, http://localhost:8101")
        sections.append("  timeout_ms, 30000")
        sections.append("  retry_count, 3")
        sections.append("")

        sections.append("API[4]{method, endpoint, expected_status}:")
        sections.append("  GET, /health, 200")
        sections.append("  GET, /api/v1/status, 200")
        sections.append("  POST, /api/v1/test, 201")
        sections.append("  GET, /api/v1/docs, 200")
        sections.append("")

        sections.append("ASSERT[2]{field, operator, expected}:")
        sections.append("  status, ==, ok")
        sections.append("  response_time, <, 1000")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-api-integration.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_cli_tests(self, output_dir: Path) -> Path | None:
        """Generate CLI tests."""
        sections = ["# SCENARIO: CLI Command Tests"]
        sections.append("# TYPE: cli")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("CONFIG[2]{key, value}:")
        sections.append("  cli_command, python -m" + self.profile.name)
        sections.append("  timeout_ms, 10000")
        sections.append("")

        sections.append("LOG[3]{message}:")
        sections.append('  "Test CLI help command"')
        sections.append('  "Test CLI version command"')
        sections.append('  "Test CLI main workflow"')

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-cli-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_lib_tests(self, output_dir: Path) -> Path | None:
        """Generate library unit tests."""
        sections = ["# SCENARIO: Library Unit Tests"]
        sections.append("# TYPE: unit")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("LOG[2]{message}:")
        sections.append('  "Test core functions"')
        sections.append('  "Test public API surface"')

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-unit-tests.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_frontend_tests(self, output_dir: Path) -> Path | None:
        """Generate frontend/GUI tests."""
        sections = ["# SCENARIO: Frontend E2E Tests"]
        sections.append("# TYPE: gui")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("CONFIG[2]{key, value}:")
        sections.append("  base_url, http://localhost:5173")
        sections.append("  browser, chromium")
        sections.append("")

        sections.append("NAVIGATE[1]{url}:")
        sections.append("  /")
        sections.append("")

        sections.append("GUI[3]{action, selector}:")
        sections.append("  click, [data-testid=main-button]")
        sections.append("  input, [data-testid=search] test")
        sections.append("  click, [data-testid=submit]")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-frontend-e2e.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _generate_hardware_tests(self, output_dir: Path) -> Path | None:
        """Generate hardware/firmware tests."""
        sections = ["# SCENARIO: Hardware Smoke Tests"]
        sections.append("# TYPE: hardware")
        sections.append("# GENERATED: true")
        sections.append("")

        sections.append("CONFIG[3]{key, value}:")
        sections.append("  firmware_url, http://localhost:8202")
        sections.append("  timeout_ms, 10000")
        sections.append("  auto_start_firmware, true")
        sections.append("")

        sections.append("API[2]{method, endpoint, expected_status}:")
        sections.append("  GET, /api/v1/hardware/health, 200")
        sections.append("  GET, /api/v1/hardware/identify, 200")
        sections.append("")

        sections.append("HARDWARE[3]{command, peripheral}:")
        sections.append("  check, piadc")
        sections.append("  check, motor-dri0050")
        sections.append("  check, modbus-io")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-hardware-smoke.testql.toon.yaml'
        output_file.write_text(content)

        return output_file


class MultiProjectTestGenerator:
    """Generator that operates across multiple projects."""

    def __init__(self, workspace_path: str | Path):
        self.workspace_path = Path(workspace_path)
        self.generators: dict[str, TestGenerator] = {}
        self.profiles: dict[str, ProjectProfile] = {}

    def discover_projects(self) -> list[Path]:
        """Discover all projects in workspace."""
        projects = []
        for item in self.workspace_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if it's a project (has pyproject.toml, package.json, etc.)
                if any((item / f).exists() for f in ['pyproject.toml', 'package.json', 'setup.py', 'README.md']):
                    projects.append(item)
        return projects

    def analyze_all(self) -> dict[str, ProjectProfile]:
        """Analyze all discovered projects."""
        projects = self.discover_projects()

        for project_path in projects:
            generator = TestGenerator(project_path)
            profile = generator.analyze()
            self.generators[project_path.name] = generator
            self.profiles[project_path.name] = profile

        return self.profiles

    def generate_all(self) -> dict[str, list[Path]]:
        """Generate tests for all projects."""
        results = {}

        for name, generator in self.generators.items():
            output_dir = generator.project_path / 'testql-scenarios'
            generated = generator.generate_tests(output_dir)
            results[name] = generated

        return results

    def generate_cross_project_tests(self, output_dir: str | Path) -> Path:
        """Generate integration tests that span multiple projects."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        sections = ["# SCENARIO: Cross-Project Integration Tests"]
        sections.append("# TYPE: integration")
        sections.append("# GENERATED: true")
        sections.append(f"# PROJECTS: {', '.join(self.profiles.keys())}")
        sections.append("")

        sections.append("CONFIG[1]{key, value}:")
        sections.append("  mode, cross-project")
        sections.append("")

        # Add checks for each project
        project_names = list(self.profiles.keys())
        if project_names:
            sections.append(f"LOG[{len(project_names)}]{{message}}:")
            for name in project_names:
                sections.append(f'  "Project: {name}"')

        content = '\n'.join(sections)
        output_file = output_dir / 'cross-project-integration.testql.toon.yaml'
        output_file.write_text(content)

        return output_file


def generate_for_project(project_path: str | Path) -> list[Path]:
    """Convenience function to generate tests for a single project."""
    generator = TestGenerator(project_path)
    return generator.generate_tests()


def generate_for_workspace(workspace_path: str | Path) -> dict[str, list[Path]]:
    """Convenience function to generate tests for entire workspace."""
    multi_gen = MultiProjectTestGenerator(workspace_path)
    multi_gen.analyze_all()
    return multi_gen.generate_all()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "."

    print(f"Generating tests for: {path}")
    generated = generate_for_project(path)
    print(f"Generated {len(generated)} test files:")
    for f in generated:
        print(f"  - {f}")

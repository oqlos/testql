"""Main TestGenerator class combining all analysis and generation capabilities."""

from __future__ import annotations

from pathlib import Path

from .analyzers import ProjectAnalyzer
from .generators import (
    APIGeneratorMixin,
    PythonTestGeneratorMixin,
    ScenarioGeneratorMixin,
    SpecializedGeneratorMixin,
)


class TestGenerator(
    ProjectAnalyzer,
    APIGeneratorMixin,
    PythonTestGeneratorMixin,
    ScenarioGeneratorMixin,
    SpecializedGeneratorMixin,
):
    """Main test generator combining analysis and generation capabilities.

    This class orchestrates project analysis and TestQL scenario generation
    by combining multiple mixins that handle specific aspects:
    - ProjectAnalyzer: Project structure and content analysis (includes BaseAnalyzer)
    - APIGeneratorMixin: API test scenario generation
    - PythonTestGeneratorMixin: Tests from existing Python tests
    - ScenarioGeneratorMixin: Tests from OQL/CQL scenarios
    - SpecializedGeneratorMixin: CLI, lib, frontend, hardware tests

    Example:
        generator = TestGenerator("/path/to/project")
        generator.analyze()
        files = generator.generate_tests("./output")

        # Or as a one-liner:
        files = generator.generate_tests("./output")  # auto-runs analyze()
    """

    __test__ = False  # Not a pytest test class

    def analyze(self):
        """Run full project analysis.

        Populates self.profile with discovered test patterns,
        file structure, configuration, and API routes.

        Returns self.profile for convenient chaining.
        """
        self.run_full_analysis()
        return self.profile

    def generate_tests(self, output_dir: str | Path | None = None) -> list[Path]:
        """Generate TestQL scenarios based on analysis.

        Args:
            output_dir: Directory for generated files. Defaults to
                       project_path / 'testql-scenarios'

        Returns:
            List of paths to generated scenario files
        """
        if not self.profile.test_patterns and not self.profile.config:
            self.analyze()

        output_dir = Path(output_dir) if output_dir else self.project_path / 'testql-scenarios'
        output_dir.mkdir(exist_ok=True)

        generated_files: list[Path] = []

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

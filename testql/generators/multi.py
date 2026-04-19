"""Multi-project workspace test generation support."""

from __future__ import annotations

from pathlib import Path

from .test_generator import TestGenerator
from .base import ProjectProfile


class MultiProjectTestGenerator:
    """Generator that operates across multiple projects in a workspace."""

    def __init__(self, workspace_path: str | Path):
        self.workspace_path = Path(workspace_path)
        self.generators: dict[str, TestGenerator] = {}
        self.profiles: dict[str, ProjectProfile] = {}

    def discover_projects(self) -> list[Path]:
        """Discover all projects in the workspace.

        A directory is considered a project if it contains any of:
        - pyproject.toml
        - package.json
        - setup.py
        - README.md
        """
        projects = []
        marker_files = ['pyproject.toml', 'package.json', 'setup.py', 'README.md']

        for item in self.workspace_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                if any((item / f).exists() for f in marker_files):
                    projects.append(item)

        return projects

    def analyze_all(self) -> dict[str, ProjectProfile]:
        """Analyze all discovered projects in the workspace.

        Returns:
            Dictionary mapping project names to their profiles
        """
        projects = self.discover_projects()

        for project_path in projects:
            generator = TestGenerator(project_path)
            profile = generator.analyze()
            self.generators[project_path.name] = generator
            self.profiles[project_path.name] = profile

        return self.profiles

    def generate_all(self) -> dict[str, list[Path]]:
        """Generate tests for all discovered projects.

        Returns:
            Dictionary mapping project names to lists of generated file paths
        """
        results: dict[str, list[Path]] = {}

        for name, generator in self.generators.items():
            output_dir = generator.project_path / 'testql-scenarios'
            generated = generator.generate_tests(output_dir)
            results[name] = generated

        return results

    def generate_cross_project_tests(self, output_dir: str | Path) -> Path:
        """Generate integration tests that span multiple projects.

        Creates a scenario file that references all discovered projects.

        Args:
            output_dir: Directory for the generated cross-project test file

        Returns:
            Path to the generated scenario file
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        sections = [
            "# SCENARIO: Cross-Project Integration Tests",
            "# TYPE: integration",
            "# GENERATED: true",
            f"# PROJECTS: {', '.join(self.profiles.keys())}",
            "",
            "CONFIG[1]{key, value}:",
            "  mode, cross-project",
            "",
        ]

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

"""Convenience functions for quick test generation."""

from __future__ import annotations

from pathlib import Path

from .test_generator import TestGenerator
from .multi import MultiProjectTestGenerator


def generate_for_project(project_path: str | Path) -> list[Path]:
    """Generate tests for a single project.

    This is the simplest entry point for test generation.

    Args:
        project_path: Path to the project directory

    Returns:
        List of paths to generated scenario files

    Example:
        >>> from testql.generators import generate_for_project
        >>> files = generate_for_project("/path/to/my-project")
        >>> print(f"Generated {len(files)} test files")
    """
    generator = TestGenerator(project_path)
    return generator.generate_tests()


def generate_for_workspace(workspace_path: str | Path) -> dict[str, list[Path]]:
    """Generate tests for all projects in a workspace.

    Discovers all projects in the workspace and generates tests
    for each one, plus cross-project integration tests.

    Args:
        workspace_path: Path to the workspace directory

    Returns:
        Dictionary mapping project names to lists of generated file paths

    Example:
        >>> from testql.generators import generate_for_workspace
        >>> results = generate_for_workspace("/path/to/workspace")
        >>> for project, files in results.items():
        ...     print(f"{project}: {len(files)} files")
    """
    multi_gen = MultiProjectTestGenerator(workspace_path)
    multi_gen.analyze_all()
    return multi_gen.generate_all()

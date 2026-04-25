"""Base classes and data models for TestQL generators."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from collections import defaultdict


@dataclass
class TestPattern:
    """Discovered test pattern from source code."""
    __test__ = False  # Not a pytest test class
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


class BaseAnalyzer:
    """Base class for project analyzers.
    
    Provides common initialization and shared utilities.
    """

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.profile = ProjectProfile(
            name=self.project_path.name,
            root_path=self.project_path,
            project_type="mixed"
        )

    def _get_exclude_dirs(self) -> set[str]:
        """Return default set of directories to exclude from scanning."""
        return {
            '.venv', 'venv', 'node_modules', '__pycache__',
            '.git', '.pytest_cache', '.ruff_cache', '.idea',
            'dist', 'build', '.tox', '.eggs', '*.egg-info'
        }

    def _should_exclude_path(self, path: Path) -> bool:
        """Check if a path should be excluded from scanning."""
        exclude_dirs = self._get_exclude_dirs()
        parts = set(path.parts)
        return bool(parts & exclude_dirs)

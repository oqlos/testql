"""Base class for endpoint detectors."""

from __future__ import annotations

from pathlib import Path

from .models import EndpointInfo


class BaseEndpointDetector:
    """Base class for endpoint detectors."""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.endpoints: list[EndpointInfo] = []

    def detect(self) -> list[EndpointInfo]:
        """Run detection and return endpoints."""
        raise NotImplementedError

    def _find_files(self, pattern: str, exclude_dirs: set[str] | None = None) -> list[Path]:
        """Find files matching pattern."""
        exclude_dirs = exclude_dirs or {
            '.venv', 'venv', 'node_modules', '__pycache__', '.git',
            '.pytest_cache', '.ruff_cache', '.idea', 'dist', 'build'
        }
        files = []
        try:
            for path in self.project_path.rglob(pattern):
                if not any(d in str(path) for d in exclude_dirs):
                    files.append(path)
        except Exception:
            pass
        return files

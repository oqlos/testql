"""Test file collection utilities for suite command."""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path


# Default test file extensions
DEFAULT_TEST_EXTENSIONS = ("*.testql.toon.yaml", "*.testtoon", "*.iql")

# Default directories to search for tests
DEFAULT_TEST_DIRS = ("testql", "testql/scenarios/tests", "tests", ".")


def _find_files(base_dir: Path, file_pattern: str) -> list[Path]:
    """Find files matching *file_pattern* under *base_dir*."""
    matched: list[Path] = []
    if not base_dir.exists():
        return matched

    # Handle path separators in pattern
    if "/" in file_pattern or "\\" in file_pattern:
        parts = file_pattern.replace("\\", "/").split("/")
        search_dir = base_dir
        for part in parts[:-1]:
            search_dir = search_dir / part
        file_only = parts[-1]
    else:
        search_dir = base_dir
        file_only = file_pattern

    if not search_dir.exists():
        return matched

    for root, _dirs, files in os.walk(search_dir):
        for filename in files:
            if fnmatch.fnmatch(filename, file_only):
                matched.append(Path(root) / filename)
    return matched


def _collect_from_suite(target_path: Path, suite_name: str, config: dict) -> list[Path]:
    """Collect files from a named suite definition in config."""
    suite_patterns = config.get("suites", {}).get(suite_name, [])
    if isinstance(suite_patterns, str):
        suite_patterns = [suite_patterns]

    base = target_path if target_path.is_dir() else target_path.parent
    files: list[Path] = []

    for p in suite_patterns:
        files.extend(_find_files(base, str(p)))
    return files


def _collect_by_pattern(target_path: Path, pattern: str) -> list[Path]:
    """Collect files matching a glob pattern."""
    base = target_path if target_path.is_dir() else target_path.parent
    return _find_files(base, str(pattern))


def _collect_recursive(target_path: Path) -> list[Path]:
    """Collect all test files under default directories."""
    files: list[Path] = []
    for subdir in DEFAULT_TEST_DIRS:
        td = target_path / subdir
        if td.exists():
            for ext in DEFAULT_TEST_EXTENSIONS:
                files.extend(_find_files(td, ext))
    return files


def _deduplicate_files(files: list[Path]) -> list[Path]:
    """Remove duplicate files and filter non-existent."""
    seen: set[str] = set()
    unique: list[Path] = []
    for f in files:
        key = str(f)
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return [f for f in unique if f.exists()]


def collect_test_files(
    target_path: Path,
    suite_name: str | None,
    pattern: str | None,
    config: dict,
) -> list[Path]:
    """Collect test files based on suite, pattern, or default recursive search."""
    # Determine collection strategy
    if suite_name and config.get("suites", {}).get(suite_name):
        test_files = _collect_from_suite(target_path, suite_name, config)
    elif pattern:
        test_files = _collect_by_pattern(target_path, pattern)
    elif target_path.is_file():
        test_files = [target_path]
    else:
        test_files = _collect_recursive(target_path)

    return _deduplicate_files(test_files)


# For list command
LIST_SEARCH_DIRS = ("testql", "testql/scenarios/tests", "tests", ".")
LIST_EXTENSIONS = ("*.testql.toon.yaml", "*.testtoon")


def collect_list_files(target_path: Path) -> list[Path]:
    """Glob test files from standard search locations."""
    raw: list[Path] = []
    for subdir in LIST_SEARCH_DIRS:
        sd = target_path / subdir
        if sd.exists():
            for ext in LIST_EXTENSIONS:
                raw.extend(sd.glob(ext))
    return sorted(set(raw))

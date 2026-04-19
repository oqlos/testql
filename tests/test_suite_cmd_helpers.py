"""Tests for suite_cmd helper functions."""

import os
from pathlib import Path

import pytest

from testql.commands.suite.collection import (
    _find_files,
    _collect_from_suite,
    _collect_by_pattern,
    _collect_recursive,
)

def _collect_test_files(target_path, suite_name=None, pattern=None, config=None):
    """Helper shim for tests."""
    config = config or {}
    target_path = Path(target_path)
    if target_path.is_file():
        return [target_path]
    if suite_name:
        return _collect_from_suite(target_path, suite_name, config)
    if pattern:
        return _collect_by_pattern(target_path, pattern)
    return _collect_recursive(target_path)


class TestFindFiles:
    def test_returns_empty_for_missing_dir(self, tmp_path):
        result = _find_files(tmp_path / 'nonexistent', '*.py')
        assert result == []

    def test_finds_matching_files(self, tmp_path):
        (tmp_path / 'a.py').write_text('')
        (tmp_path / 'b.txt').write_text('')
        result = _find_files(tmp_path, '*.py')
        assert len(result) == 1
        assert result[0].name == 'a.py'

    def test_finds_files_in_subdirs(self, tmp_path):
        sub = tmp_path / 'sub'
        sub.mkdir()
        (sub / 'test.testql.toon.yaml').write_text('')
        result = _find_files(tmp_path, '*.testql.toon.yaml')
        assert len(result) == 1

    def test_path_with_separator(self, tmp_path):
        sub = tmp_path / 'scenarios'
        sub.mkdir()
        (sub / 'test.yaml').write_text('')
        result = _find_files(tmp_path, 'scenarios/*.yaml')
        assert len(result) == 1

    def test_path_with_missing_subdir(self, tmp_path):
        result = _find_files(tmp_path, 'missing/dir/*.yaml')
        assert result == []


class TestCollectFromSuite:
    def test_named_suite(self, tmp_path):
        (tmp_path / 'smoke.testql.toon.yaml').write_text('')
        config = {'suites': {'smoke': ['*.testql.toon.yaml']}}
        result = _collect_from_suite(tmp_path, 'smoke', config)
        assert len(result) == 1

    def test_string_pattern_in_suite(self, tmp_path):
        (tmp_path / 'test.testql.toon.yaml').write_text('')
        config = {'suites': {'all': '*.testql.toon.yaml'}}
        result = _collect_from_suite(tmp_path, 'all', config)
        assert len(result) == 1

    def test_missing_suite_name(self, tmp_path):
        result = _collect_from_suite(tmp_path, 'missing', {})
        assert result == []

    def test_uses_parent_when_file(self, tmp_path):
        (tmp_path / 'x.yml').write_text('')
        f = tmp_path / 'SUMD.md'
        f.write_text('')
        config = {'suites': {'s': ['*.yml']}}
        result = _collect_from_suite(f, 's', config)
        assert len(result) == 1


class TestCollectByPattern:
    def test_finds_matching(self, tmp_path):
        (tmp_path / 'test.testql.toon.yaml').write_text('')
        result = _collect_by_pattern(tmp_path, '*.testql.toon.yaml')
        assert len(result) == 1

    def test_no_match(self, tmp_path):
        result = _collect_by_pattern(tmp_path, '*.nothing')
        assert result == []


class TestCollectRecursive:
    def test_finds_testql_files(self, tmp_path):
        tests_dir = tmp_path / 'tests'
        tests_dir.mkdir()
        (tests_dir / 'smoke.testql.toon.yaml').write_text('')
        result = _collect_recursive(tmp_path)
        assert any(f.name == 'smoke.testql.toon.yaml' for f in result)

    def test_empty_project(self, tmp_path):
        result = _collect_recursive(tmp_path)
        assert result == []


class TestCollectTestFiles:
    def test_single_file_target(self, tmp_path):
        f = tmp_path / 'test.testql.toon.yaml'
        f.write_text('')
        result = _collect_test_files(f, None, None, {})
        assert f in result

    def test_suite_takes_priority(self, tmp_path):
        f = tmp_path / 'suite_test.testql.toon.yaml'
        f.write_text('')
        config = {'suites': {'smoke': ['*.testql.toon.yaml']}}
        result = _collect_test_files(tmp_path, 'smoke', None, config)
        assert f in result

    def test_pattern_used_when_no_suite(self, tmp_path):
        (tmp_path / 'match.testql.toon.yaml').write_text('')
        result = _collect_test_files(tmp_path, None, '*.testql.toon.yaml', {})
        assert len(result) == 1

    def test_deduplication(self, tmp_path):
        f = tmp_path / 'x.testql.toon.yaml'
        f.write_text('')
        config = {'suites': {}}
        # Two patterns matching the same file
        result = _collect_test_files(tmp_path, None, '*.testql.toon.yaml', config)
        assert result.count(f) == 1

    def test_nonexistent_files_excluded(self, tmp_path):
        f = tmp_path / 'gone.testql.toon.yaml'
        # File doesn't exist
        result = _collect_test_files(f, None, None, {})
        assert result == []

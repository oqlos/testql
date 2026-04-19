"""Tests for testql/generators modules."""

import json
import tempfile
from pathlib import Path

import pytest

from testql.generators.base import BaseAnalyzer, TestPattern, ProjectProfile
from testql.generators.analyzers import ProjectAnalyzer


class TestBaseAnalyzer:
    def test_init(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        assert analyzer.project_path == tmp_path
        assert isinstance(analyzer.profile, ProjectProfile)
        assert analyzer.profile.name == tmp_path.name

    def test_get_exclude_dirs(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        exclude = analyzer._get_exclude_dirs()
        assert 'venv' in exclude
        assert '__pycache__' in exclude
        assert '.git' in exclude

    def test_should_exclude_path_venv(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        venv_path = tmp_path / 'venv' / 'lib' / 'site.py'
        assert analyzer._should_exclude_path(venv_path)

    def test_should_exclude_path_src(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        src_path = tmp_path / 'src' / 'app.py'
        assert not analyzer._should_exclude_path(src_path)


class TestProjectAnalyzerDetectType:
    def test_detect_python_api_fastapi(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool.poetry]\nfastapi = "^0.100"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-api'

    def test_detect_python_api_flask(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[dependencies]\nflask = "*"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-api'

    def test_detect_python_cli(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool]\nclick = "^8"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-cli'

    def test_detect_python_lib(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool.poetry]\nname = "mylib"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-lib'

    def test_detect_hardware(self, tmp_path):
        (tmp_path / 'hardware').mkdir()
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'hardware'

    def test_detect_mixed_default(self, tmp_path):
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'mixed'

    def test_detect_web_frontend(self, tmp_path):
        (tmp_path / 'package.json').write_text('{}')
        (tmp_path / 'vite.config.js').write_text('')
        (tmp_path / 'index.html').write_text('')
        (tmp_path / 'playwright.config.js').write_text('')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'web-frontend'

    def test_detect_web_frontend_missing_e2e_markers(self, tmp_path):
        # Has frontend markers but no e2e markers => falls through to next check
        (tmp_path / 'package.json').write_text('{}')
        (tmp_path / 'vite.config.js').write_text('')
        (tmp_path / 'index.html').write_text('')
        analyzer = ProjectAnalyzer(tmp_path)
        # No e2e marker means _detect_web_frontend returns None
        result = analyzer._detect_web_frontend(
            frozenset(['package.json', 'vite.config.js', 'index.html'])
        )
        assert result is None


class TestTestPattern:
    def test_defaults(self):
        pattern = TestPattern(
            name='test_login',
            target='/api/login',
            pattern_type='api',
            commands=[],
            assertions=[],
        )
        assert pattern.name == 'test_login'
        assert pattern.metadata == {}

    def test_metadata(self):
        pattern = TestPattern(
            name='test',
            target='target',
            pattern_type='unit',
            commands=[{'cmd': 'get'}],
            assertions=[{'assert': 'status'}],
            metadata={'author': 'tester'},
        )
        assert pattern.metadata['author'] == 'tester'

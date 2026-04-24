"""Tests for testql.generators.test_generator.TestGenerator."""
from __future__ import annotations

from pathlib import Path

import pytest

from testql.generators.test_generator import TestGenerator


class TestTestGeneratorAnalyze:
    def test_analyze_returns_profile(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        profile = g.analyze()
        assert profile is g.profile

    def test_analyze_empty_project_mixed_type(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.profile.project_type == "mixed"

    def test_analyze_fastapi_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[tool.poetry]\nfastapi = "^0.100"')
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.profile.project_type == "python-api"

    def test_analyze_cli_project(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text('[dependencies]\nclick = "^8.0"')
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.profile.project_type == "python-cli"

    def test_analyze_argparse_cli_project(self, tmp_path):
        """Projects using argparse should be detected as python-cli."""
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "myapp"')
        cli_dir = tmp_path / "myapp"
        cli_dir.mkdir()
        (cli_dir / "cli.py").write_text(
            'import argparse\nparser = argparse.ArgumentParser()\n'
            'parser.add_argument("--version")\n'
        )
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.profile.project_type == "python-cli"

    def test_analyze_typer_cli_project(self, tmp_path):
        """Projects using typer should be detected as python-cli."""
        (tmp_path / "pyproject.toml").write_text('[dependencies]\ntyper = "^0.9"')
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.profile.project_type == "python-cli"

    def test_analyze_sets_project_path(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        g.analyze()
        assert g.project_path == Path(str(tmp_path))


class TestTestGeneratorGenerateTests:
    def test_generate_empty_project_returns_empty_list(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        files = g.generate_tests(tmp_path / "out")
        assert files == []

    def test_generate_creates_output_dir(self, tmp_path):
        out = tmp_path / "scenarios"
        g = TestGenerator(str(tmp_path))
        g.generate_tests(out)
        assert out.exists()

    def test_generate_default_output_dir(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        g.generate_tests()
        assert (tmp_path / "testql-scenarios").exists()

    def test_generate_auto_analyzes_if_not_analyzed(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        # profile not yet populated via analyze()
        files = g.generate_tests(tmp_path / "out")
        # should not raise; project_type should be set
        assert g.profile.project_type is not None

    def test_generate_returns_list(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        result = g.generate_tests(tmp_path / "out")
        assert isinstance(result, list)

    def test_generate_with_python_tests(self, tmp_path):
        """Having test files may trigger python test generator."""
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_foo.py").write_text(
            "def test_add():\n    assert 1 + 1 == 2\n"
        )
        g = TestGenerator(str(tmp_path))
        g.analyze()
        files = g.generate_tests(tmp_path / "out")
        assert isinstance(files, list)

    def test_generate_accepts_string_output_dir(self, tmp_path):
        g = TestGenerator(str(tmp_path))
        files = g.generate_tests(str(tmp_path / "out"))
        assert isinstance(files, list)

    def test_generate_with_discovered_routes(self, tmp_path):
        """Discovered routes triggers API test generation."""
        (tmp_path / "app.py").write_text(
            "from flask import Flask\napp = Flask(__name__)\n"
            "@app.route('/users')\ndef users(): return []\n"
        )
        g = TestGenerator(str(tmp_path))
        g.analyze()
        # Patch profile to have a discovered_routes entry to force api gen branch
        g.profile.config["discovered_routes"] = [{"method": "GET", "path": "/users"}]
        files = g.generate_tests(tmp_path / "out")
        assert isinstance(files, list)

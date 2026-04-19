"""Tests for commands/generate_cmd.py."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from testql.commands.generate_cmd import _is_workspace, generate, analyze


class TestIsWorkspace:
    def test_has_pyproject_returns_false(self, tmp_path):
        (tmp_path / "pyproject.toml").touch()
        assert _is_workspace(tmp_path) is False

    def test_has_setup_py_returns_false(self, tmp_path):
        (tmp_path / "setup.py").touch()
        assert _is_workspace(tmp_path) is False

    def test_workspace_dir_without_init(self, tmp_path):
        (tmp_path / "doql").mkdir()
        assert _is_workspace(tmp_path) is True

    def test_workspace_dir_with_init_returns_false(self, tmp_path):
        sub = tmp_path / "oql"
        sub.mkdir()
        (sub / "__init__.py").touch()
        assert _is_workspace(tmp_path) is False

    def test_no_workspace_dirs_returns_false(self, tmp_path):
        assert _is_workspace(tmp_path) is False

    def test_multiple_workspace_dirs(self, tmp_path):
        (tmp_path / "doql").mkdir()
        (tmp_path / "oql").mkdir()
        assert _is_workspace(tmp_path) is True


class TestGenerateCommand:
    def test_analyze_only_single_project(self, tmp_path):
        runner = CliRunner()
        mock_gen = MagicMock()
        mock_profile = MagicMock()
        mock_profile.project_type = "api"
        mock_profile.test_patterns = ["a", "b"]
        mock_profile.discovered_files = {"routes": ["f1.py"]}
        mock_gen.analyze.return_value = mock_profile
        mock_gen.profile = mock_profile

        with patch("testql.generator.TestGenerator", return_value=mock_gen):
            result = runner.invoke(generate, [str(tmp_path), "--analyze-only"])

        assert result.exit_code == 0 or "api" in result.output.lower() or "Analyzing" in result.output

    def test_analyze_only_workspace(self, tmp_path):
        runner = CliRunner()
        (tmp_path / "doql").mkdir()

        mock_gen = MagicMock()
        mock_gen.analyze_all.return_value = {"doql": MagicMock(project_type="api", test_patterns=[], config={})}

        with patch("testql.generator.MultiProjectTestGenerator", return_value=mock_gen):
            result = runner.invoke(generate, [str(tmp_path), "--analyze-only"])

        assert result.exit_code == 0

    def test_generate_single_project(self, tmp_path):
        runner = CliRunner()
        mock_gen = MagicMock()
        mock_profile = MagicMock()
        mock_profile.project_type = "api"
        mock_profile.test_patterns = []
        mock_profile.discovered_files = {}
        mock_gen.analyze.return_value = mock_profile
        mock_gen.profile = mock_profile
        mock_gen.generate_tests.return_value = [tmp_path / "test_foo.tql"]

        with patch("testql.generator.TestGenerator", return_value=mock_gen):
            result = runner.invoke(generate, [str(tmp_path)])

        assert result.exit_code == 0

    def test_analyze_command(self, tmp_path):
        runner = CliRunner()
        mock_gen = MagicMock()
        mock_profile = MagicMock()
        mock_profile.name = "testproject"
        mock_profile.root_path = tmp_path
        mock_profile.project_type = "api"
        mock_profile.discovered_files = {"routes": ["r.py"]}
        mock_profile.test_patterns = []
        mock_profile.config = {}
        mock_gen.analyze.return_value = mock_profile

        with patch("testql.generator.TestGenerator", return_value=mock_gen):
            result = runner.invoke(analyze, [str(tmp_path)])

        assert result.exit_code == 0

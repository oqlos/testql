"""Tests for commands/misc_cmds.py — init and create commands."""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from testql.commands.misc_cmds import init, create


class TestInitCommand:
    def test_creates_dirs_and_config(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(init, ["--path", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "testql").is_dir()
        assert (tmp_path / "testql" / "fixtures").is_dir()
        assert (tmp_path / "testql" / "reports").is_dir()
        assert (tmp_path / "testql.yaml").exists()

    def test_config_contains_project_name(self, tmp_path):
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path), "--name", "myproject"])
        config = (tmp_path / "testql.yaml").read_text()
        assert "myproject" in config

    def test_api_type_creates_api_template(self, tmp_path):
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path), "--type", "api"])
        assert (tmp_path / "testql" / "test-api-health.testql.toon.yaml").exists()
        assert not (tmp_path / "testql" / "test-gui-navigation.testql.toon.yaml").exists()

    def test_gui_type_creates_gui_template(self, tmp_path):
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path), "--type", "gui"])
        assert (tmp_path / "testql" / "test-gui-navigation.testql.toon.yaml").exists()

    def test_encoder_type_creates_encoder_template(self, tmp_path):
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path), "--type", "encoder"])
        assert (tmp_path / "testql" / "test-encoder-basic.testql.toon.yaml").exists()

    def test_all_type_creates_all_templates(self, tmp_path):
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path), "--type", "all"])
        assert (tmp_path / "testql" / "test-api-health.testql.toon.yaml").exists()
        assert (tmp_path / "testql" / "test-gui-navigation.testql.toon.yaml").exists()
        assert (tmp_path / "testql" / "test-encoder-basic.testql.toon.yaml").exists()

    def test_existing_config_not_overwritten(self, tmp_path):
        config = tmp_path / "testql.yaml"
        config.write_text("custom: true\n")
        runner = CliRunner()
        runner.invoke(init, ["--path", str(tmp_path)])
        assert config.read_text() == "custom: true\n"

    def test_default_path_is_current_dir(self, tmp_path):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(init, [])
        assert result.exit_code == 0


class TestCreateCommand:
    def test_creates_test_file(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(create, ["my-test", "--output", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "my-test.testql.toon.yaml").exists()

    def test_file_contains_name(self, tmp_path):
        runner = CliRunner()
        runner.invoke(create, ["login-test", "--output", str(tmp_path)])
        content = (tmp_path / "login-test.testql.toon.yaml").read_text()
        assert len(content) > 0

    def test_fails_if_exists_without_force(self, tmp_path):
        existing = tmp_path / "existing.testql.toon.yaml"
        existing.write_text("old content\n")
        runner = CliRunner()
        result = runner.invoke(create, ["existing", "--output", str(tmp_path)])
        assert result.exit_code != 0
        assert existing.read_text() == "old content\n"

    def test_force_overwrites_existing(self, tmp_path):
        existing = tmp_path / "existing.testql.toon.yaml"
        existing.write_text("old content\n")
        runner = CliRunner()
        result = runner.invoke(create, ["existing", "--output", str(tmp_path), "--force"])
        assert result.exit_code == 0
        assert existing.read_text() != "old content\n"

    def test_api_type(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(create, ["api-test", "--type", "api", "--output", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "api-test.testql.toon.yaml").exists()

    def test_with_module(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(create, ["mod-test", "--module", "auth", "--output", str(tmp_path)])
        assert result.exit_code == 0

    def test_creates_output_dir_if_missing(self, tmp_path):
        new_dir = tmp_path / "newdir"
        runner = CliRunner()
        result = runner.invoke(create, ["t", "--output", str(new_dir)])
        assert result.exit_code == 0
        assert new_dir.is_dir()

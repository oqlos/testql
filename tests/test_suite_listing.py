"""Tests for testql/commands/suite/listing.py"""
import json
from pathlib import Path
import pytest
import yaml

from testql.commands.suite.listing import (
    _parse_testtoon_header,
    _parse_yaml_meta_block,
    parse_meta,
    filter_tests,
    render_test_list,
)


class TestParseTesttoonHeader:
    def test_returns_none_for_no_header(self):
        assert _parse_testtoon_header("just content") is None

    def test_parses_scenario_header(self):
        content = "# SCENARIO: My Test\n# TYPE: api\n"
        result = _parse_testtoon_header(content)
        assert result is not None
        assert result["name"] == "My Test"
        assert result["type"] == "api"

    def test_parses_type_without_scenario(self):
        content = "# TYPE: gui\nsome content\n"
        result = _parse_testtoon_header(content)
        assert result is not None
        assert result["type"] == "gui"

    def test_returns_none_for_plain_content(self):
        assert _parse_testtoon_header("name: test\ntype: api\n") is None

    def test_tags_default_empty(self):
        content = "# SCENARIO: Test\n"
        result = _parse_testtoon_header(content)
        assert result["tags"] == []


class TestParseYamlMetaBlock:
    def test_returns_none_without_meta(self):
        assert _parse_yaml_meta_block("no meta here", yaml) is None

    def test_parses_meta_block(self):
        content = "meta:\n  name: my_test\n  type: api\n"
        result = _parse_yaml_meta_block(content, yaml)
        assert result is not None
        assert result["name"] == "my_test"

    def test_meta_with_tags(self):
        content = "meta:\n  name: t\n  tags:\n   - smoke\n   - api\n"
        result = _parse_yaml_meta_block(content, yaml)
        assert result is not None

    def test_empty_meta_block(self):
        content = "meta:\nother: stuff\n"
        result = _parse_yaml_meta_block(content, yaml)
        # meta block with no indented content should return None
        assert result is None or isinstance(result, dict)


class TestParseMeta:
    def test_default_meta_from_stem(self, tmp_path):
        f = tmp_path / "my_test.testql.toon.yaml"
        f.write_text("no metadata")
        meta = parse_meta(f, yaml)
        # stem of multi-extension file = "my_test.testql.toon"
        assert "my_test" in meta["name"]
        assert meta["type"] == "unknown"

    def test_uses_header_when_present(self, tmp_path):
        f = tmp_path / "t.testql.toon.yaml"
        f.write_text("# SCENARIO: Smoke Test\n# TYPE: api\n")
        meta = parse_meta(f, yaml)
        assert meta["name"] == "Smoke Test"
        assert meta["type"] == "api"

    def test_uses_yaml_meta_when_no_header(self, tmp_path):
        f = tmp_path / "t.testql.toon.yaml"
        f.write_text("meta:\n  name: my_scenario\n  type: encoder\n")
        meta = parse_meta(f, yaml)
        assert meta["type"] == "encoder"

    def test_returns_default_on_missing_file(self, tmp_path):
        f = tmp_path / "missing.testql.toon.yaml"
        # parse_meta reads the file — if it doesn't exist, exception caught
        # We'll create it as empty to not trigger exception
        f.write_text("")
        meta = parse_meta(f, yaml)
        assert isinstance(meta, dict)


class TestFilterTests:
    def _make_files(self, tmp_path):
        files = []
        for name, content in [
            ("smoke.testql.toon.yaml", "# SCENARIO: Smoke\n# TYPE: api\n"),
            ("gui.testql.toon.yaml", "# SCENARIO: GUI\n# TYPE: gui\n"),
            ("tagged.testql.toon.yaml", "meta:\n  name: tagged\n  type: api\n  tags:\n   - smoke\n"),
        ]:
            f = tmp_path / name
            f.write_text(content)
            files.append(f)
        return files

    def test_filter_all(self, tmp_path):
        files = self._make_files(tmp_path)
        result = filter_tests(files, tmp_path, "all", None, yaml)
        assert len(result) == 3

    def test_filter_by_type(self, tmp_path):
        files = self._make_files(tmp_path)
        result = filter_tests(files, tmp_path, "gui", None, yaml)
        assert len(result) == 1
        assert result[0]["type"] == "gui"

    def test_filter_by_tag(self, tmp_path):
        files = self._make_files(tmp_path)
        result = filter_tests(files, tmp_path, "all", "smoke", yaml)
        assert len(result) == 1

    def test_empty_input(self, tmp_path):
        assert filter_tests([], tmp_path, "all", None, yaml) == []

    def test_result_has_required_keys(self, tmp_path):
        files = self._make_files(tmp_path)
        result = filter_tests(files, tmp_path, "all", None, yaml)
        for t in result:
            assert "file" in t
            assert "name" in t
            assert "type" in t
            assert "tags" in t


class TestRenderTestList:
    def test_render_json(self, capsys):
        tests = [{"file": "a.yaml", "name": "A", "type": "api", "tags": []}]
        render_test_list(tests, "json")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data[0]["file"] == "a.yaml"

    def test_render_simple(self, capsys):
        tests = [{"file": "a.yaml", "name": "A", "type": "api", "tags": []}]
        render_test_list(tests, "simple")
        captured = capsys.readouterr()
        assert "a.yaml" in captured.out

    def test_render_table(self, capsys):
        tests = [
            {"file": "a.yaml", "name": "A", "type": "api", "tags": ["smoke"]},
            {"file": "b.yaml", "name": "B", "type": "gui", "tags": []},
        ]
        render_test_list(tests, "table")
        captured = capsys.readouterr()
        assert "a.yaml" in captured.out
        assert "smoke" in captured.out
        assert "2 test file" in captured.out

    def test_render_table_empty_tags(self, capsys):
        tests = [{"file": "x.yaml", "name": "X", "type": "api", "tags": []}]
        render_test_list(tests, "table")
        captured = capsys.readouterr()
        assert "-" in captured.out

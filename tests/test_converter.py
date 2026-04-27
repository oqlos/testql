"""Tests for testql.interpreter._converter re-export shim and converter core."""
from __future__ import annotations

from pathlib import Path

import pytest

from testql.interpreter._converter import (
    Row,
    Section,
    convert_directory,
    convert_file,
    convert_oql_to_testtoon,
)


class TestRow:
    def test_row_creation(self):
        r = Row({"key": "value"})
        assert r.values == {"key": "value"}

    def test_row_empty(self):
        r = Row({})
        assert r.values == {}

    def test_row_multiple_fields(self):
        r = Row({"a": "1", "b": "2"})
        assert r.values["a"] == "1"
        assert r.values["b"] == "2"


class TestSection:
    def test_section_creation(self):
        s = Section("NAVIGATE", ["path", "wait_ms"])
        assert s.type == "NAVIGATE"
        assert s.columns == ["path", "wait_ms"]
        assert s.rows == []
        assert s.comment == ""

    def test_section_with_rows(self):
        s = Section("FLOW", ["command", "target"], rows=[{"command": "click", "target": "#btn"}])
        assert len(s.rows) == 1

    def test_section_with_comment(self):
        s = Section("NAVIGATE", ["path"], comment="UI nav")
        assert s.comment == "UI nav"


class TestConvertOqlToTesttoon:
    def test_navigate_command(self):
        src = "NAVIGATE http://localhost"
        result = convert_oql_to_testtoon(src, "test.tql")
        assert "NAVIGATE" in result
        assert "http://localhost" in result

    def test_scenario_name_from_filename(self):
        src = "NAVIGATE http://example.com"
        result = convert_oql_to_testtoon(src, "my_scenario.tql")
        assert "My_Scenario" in result or "my_scenario" in result.lower() or "SCENARIO" in result

    def test_header_present(self):
        result = convert_oql_to_testtoon("NAVIGATE http://x.com")
        assert "# SCENARIO:" in result
        assert "# TYPE:" in result
        assert "# VERSION:" in result

    def test_click_converts_to_flow(self):
        src = "CLICK #btn"
        result = convert_oql_to_testtoon(src)
        assert "FLOW" in result or "click" in result

    def test_assert_text_converts(self):
        src = "ASSERT_TEXT .title Hello"
        result = convert_oql_to_testtoon(src)
        assert "assert_text" in result or "ASSERT" in result

    def test_empty_source(self):
        result = convert_oql_to_testtoon("", "empty.tql")
        assert "# SCENARIO:" in result

    def test_get_request(self):
        src = "GET /api/v1/users"
        result = convert_oql_to_testtoon(src, "api.tql")
        assert "# TYPE: api" in result

    def test_default_filename(self):
        result = convert_oql_to_testtoon("NAVIGATE http://x.com")
        assert "SCENARIO" in result

    def test_returns_string(self):
        result = convert_oql_to_testtoon("NAVIGATE http://x.com")
        assert isinstance(result, str)

    def test_multiline_script(self):
        src = "NAVIGATE http://localhost\nCLICK button\nASSERT_TEXT .title Hello"
        result = convert_oql_to_testtoon(src, "multi.tql")
        assert "NAVIGATE" in result
        assert isinstance(result, str)


class TestConvertFile:
    def test_creates_output_file(self, tmp_path):
        src = tmp_path / "test.tql"
        src.write_text("NAVIGATE http://example.com")
        out = convert_file(src)
        assert out.exists()

    def test_output_filename_pattern(self, tmp_path):
        src = tmp_path / "my_test.tql"
        src.write_text("NAVIGATE http://example.com")
        out = convert_file(src)
        assert out.name == "my_test.testql.toon.yaml"

    def test_oql_extension(self, tmp_path):
        src = tmp_path / "api.oql"
        src.write_text("GET /api/users")
        out = convert_file(src)
        assert out.name == "api.testql.toon.yaml"

    def test_output_is_in_same_dir(self, tmp_path):
        src = tmp_path / "scenario.tql"
        src.write_text("NAVIGATE http://x.com")
        out = convert_file(src)
        assert out.parent == tmp_path

    def test_output_content_has_scenario(self, tmp_path):
        src = tmp_path / "s.tql"
        src.write_text("NAVIGATE http://example.com")
        out = convert_file(src)
        assert "SCENARIO" in out.read_text()

    def test_returns_path(self, tmp_path):
        src = tmp_path / "s.tql"
        src.write_text("NAVIGATE http://example.com")
        out = convert_file(src)
        assert isinstance(out, Path)


class TestConvertDirectory:
    def test_empty_directory(self, tmp_path):
        result = convert_directory(tmp_path)
        assert result == []

    def test_converts_tql_files(self, tmp_path):
        (tmp_path / "a.tql").write_text("NAVIGATE http://example.com")
        result = convert_directory(tmp_path)
        assert len(result) == 1

    def test_converts_oql_files(self, tmp_path):
        (tmp_path / "b.oql").write_text("GET /api/v1")
        result = convert_directory(tmp_path)
        assert len(result) == 1

    def test_converts_multiple_files(self, tmp_path):
        (tmp_path / "a.tql").write_text("NAVIGATE http://a.com")
        (tmp_path / "b.oql").write_text("GET /b")
        result = convert_directory(tmp_path)
        assert len(result) == 2

    def test_returns_list_of_paths(self, tmp_path):
        (tmp_path / "x.tql").write_text("NAVIGATE http://x.com")
        result = convert_directory(tmp_path)
        assert all(isinstance(p, Path) for p in result)

    def test_recursive_subdirectory(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "c.tql").write_text("NAVIGATE http://c.com")
        result = convert_directory(tmp_path)
        assert len(result) == 1
        assert result[0].name == "c.testql.toon.yaml"

    def test_ignores_non_tql_files(self, tmp_path):
        (tmp_path / "readme.md").write_text("# docs")
        (tmp_path / "note.txt").write_text("notes")
        result = convert_directory(tmp_path)
        assert result == []

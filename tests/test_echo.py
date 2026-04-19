"""Tests for echo command modules: context, parsers, formatters."""

import textwrap
from pathlib import Path

import pytest
import yaml

from testql.commands.echo.context import generate_context, _find_doql_file, _find_toon_path
from testql.commands.echo.parsers.toon import parse_toon_scenarios, _extract_endpoint, _extract_assert
from testql.commands.echo.formatters.text import (
    _fmt_interfaces,
    _fmt_workflows,
    _fmt_contracts,
    _fmt_entities,
    format_text_output,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_toon(tmp_path: Path, name: str, content: dict) -> Path:
    f = tmp_path / f"{name}.testql.toon.yaml"
    f.write_text(yaml.dump(content))
    return f


# ---------------------------------------------------------------------------
# _find_doql_file / _find_toon_path
# ---------------------------------------------------------------------------


class TestFindDoqlFile:
    def test_finds_less_file(self, tmp_path):
        f = tmp_path / "app.doql.less"
        f.write_text("")
        result = _find_doql_file(tmp_path)
        assert result == f

    def test_prefers_less_over_css(self, tmp_path):
        css = tmp_path / "app.doql.css"
        css.write_text("")
        less = tmp_path / "app.doql.less"
        less.write_text("")
        result = _find_doql_file(tmp_path)
        assert result == less

    def test_returns_none_when_missing(self, tmp_path):
        assert _find_doql_file(tmp_path) is None


class TestFindToonPath:
    def test_returns_testql_scenarios_if_exists(self, tmp_path):
        scenarios = tmp_path / "testql-scenarios"
        scenarios.mkdir()
        assert _find_toon_path(tmp_path) == scenarios

    def test_falls_back_to_path(self, tmp_path):
        assert _find_toon_path(tmp_path) == tmp_path


# ---------------------------------------------------------------------------
# generate_context
# ---------------------------------------------------------------------------


class TestGenerateContext:
    def test_returns_dict_with_project(self, tmp_path):
        ctx = generate_context(tmp_path)
        assert "project" in ctx
        assert ctx["project"]["name"] == tmp_path.name

    def test_no_doql_when_excluded(self, tmp_path):
        ctx = generate_context(tmp_path, include_doql=False)
        assert "system_model" not in ctx

    def test_no_toon_when_excluded(self, tmp_path):
        ctx = generate_context(tmp_path, include_toon=False)
        assert "api_contracts" not in ctx

    def test_empty_contracts_when_no_toon_files(self, tmp_path):
        ctx = generate_context(tmp_path)
        assert ctx.get("api_contracts") == []


# ---------------------------------------------------------------------------
# Toon parser — helpers
# ---------------------------------------------------------------------------


class TestExtractEndpoint:
    def test_dict_value(self):
        ep = _extract_endpoint("GET", {"url": "/api/users", "status": 200})
        assert ep["method"] == "GET"
        assert ep["path"] == "/api/users"
        assert ep["status"] == 200

    def test_string_value(self):
        ep = _extract_endpoint("post", "/api/items")
        assert ep["method"] == "POST"
        assert ep["path"] == "/api/items"
        assert ep["status"] is None


class TestExtractAssert:
    def test_basic(self):
        a = _extract_assert("ASSERT_STATUS", 200)
        assert a["type"] == "ASSERT_STATUS"
        assert a["condition"] == 200


# ---------------------------------------------------------------------------
# parse_toon_scenarios
# ---------------------------------------------------------------------------


class TestParseToonScenarios:
    def test_empty_dir(self, tmp_path):
        result = parse_toon_scenarios(tmp_path)
        assert result == []

    def test_parses_single_file(self, tmp_path):
        write_toon(tmp_path, "smoke", {
            "meta": {"name": "smoke test", "type": "api"},
            "GET": {"url": "/health", "status": 200},
        })
        result = parse_toon_scenarios(tmp_path)
        assert len(result) == 1
        assert result[0]["name"] == "smoke test"
        assert len(result[0]["endpoints"]) == 1

    def test_multiple_http_methods(self, tmp_path):
        write_toon(tmp_path, "multi", {
            "meta": {"name": "multi", "type": "api"},
            "GET": "/users",
            "POST": "/users",
            "DELETE": "/users/1",
        })
        result = parse_toon_scenarios(tmp_path)
        assert len(result[0]["endpoints"]) == 3

    def test_skips_empty_files(self, tmp_path):
        (tmp_path / "empty.testql.toon.yaml").write_text("")
        result = parse_toon_scenarios(tmp_path)
        assert result == []

    def test_assert_blocks_parsed(self, tmp_path):
        write_toon(tmp_path, "assert_test", {
            "meta": {"name": "t"},
            "ASSERT_STATUS": 200,
        })
        result = parse_toon_scenarios(tmp_path)
        assert len(result[0]["asserts"]) == 1


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


class TestFmtInterfaces:
    def test_empty_when_no_system_model(self):
        assert _fmt_interfaces({}) == []

    def test_shows_interfaces(self):
        ctx = {"system_model": {"interfaces": [{"type": "REST", "framework": "fastapi"}]}}
        lines = _fmt_interfaces(ctx)
        assert any("REST" in l for l in lines)

    def test_empty_interfaces_returns_empty(self):
        ctx = {"system_model": {"interfaces": []}}
        assert _fmt_interfaces(ctx) == []


class TestFmtWorkflows:
    def test_empty_when_no_workflows(self):
        assert _fmt_workflows({}) == []

    def test_shows_workflow_name(self):
        ctx = {"system_model": {"workflows": [{"name": "deploy", "steps": [1, 2]}]}}
        lines = _fmt_workflows(ctx)
        assert any("deploy" in l for l in lines)


class TestFmtContracts:
    def test_empty_when_no_contracts(self):
        assert _fmt_contracts({}) == []

    def test_shows_contract_name(self):
        ctx = {"api_contracts": [{"name": "login", "type": "api", "endpoints": [
            {"method": "POST", "path": "/login"}
        ]}]}
        lines = _fmt_contracts(ctx)
        assert any("login" in l for l in lines)

    def test_truncates_long_endpoint_list(self):
        endpoints = [{"method": "GET", "path": f"/{i}"} for i in range(10)]
        ctx = {"api_contracts": [{"name": "big", "type": "api", "endpoints": endpoints}]}
        lines = _fmt_contracts(ctx)
        assert any("more" in l for l in lines)


class TestFmtEntities:
    def test_empty_when_no_entities(self):
        assert _fmt_entities({}) == []

    def test_shows_entity_count(self):
        ctx = {"system_model": {"entities": [
            {"name": "User", "fields": ["id", "name"]},
        ]}}
        lines = _fmt_entities(ctx)
        assert any("User" in l for l in lines)


class TestFormatTextOutput:
    def test_returns_string(self, tmp_path):
        ctx = generate_context(tmp_path)
        out = format_text_output(ctx)
        assert isinstance(out, str)

    def test_contains_project_name(self, tmp_path):
        ctx = generate_context(tmp_path)
        out = format_text_output(ctx)
        assert tmp_path.name in out

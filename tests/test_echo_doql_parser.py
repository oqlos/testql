"""Tests for testql/commands/echo/parsers/doql.py"""
from pathlib import Path
import pytest

from testql.commands.echo.parsers.doql import (
    _parse_kv_block,
    _parse_app_block,
    _parse_entities,
    _parse_interfaces,
    _parse_workflows,
    _parse_deploy,
    _parse_environment,
    _parse_integrations,
    parse_doql_less,
)

SAMPLE_LESS = """\
app {
  name: myapp;
  version: 1.2.3;
}

entity[name="User"] {
  intent: identify human users;
  domain: auth;
  fields: id, name, email;
}

entity[name="Order"] {
  fields: id, total;
}

interface[type="rest"] {
  framework: fastapi;
  version: 3;
}

workflow[name="deploy"] {
  trigger: push;
  intent: ship;
  step-1: run tests;
  step-2: deploy to prod;
}

deploy {
  platform: k8s;
  region: eu-west-1;
}

environment[name="production"] {
  host: prod.example.com;
  port: 443;
}

integration[name="stripe"] {
  type: payment;
  type: webhook;
}
"""


class TestParseKvBlock:
    def test_simple(self):
        result = _parse_kv_block("  name: myapp;\n  version: 1.0;")
        assert result["name"] == "myapp"
        assert result["version"] == "1.0"

    def test_empty(self):
        assert _parse_kv_block("") == {}

    def test_no_colon_line_ignored(self):
        result = _parse_kv_block("no colon here\nkey: val;")
        assert result == {"key": "val"}

    def test_strips_trailing_semicolon(self):
        result = _parse_kv_block("x: hello world;")
        assert result["x"] == "hello world"


class TestParseAppBlock:
    def test_parses_name_and_version(self):
        result = _parse_app_block(SAMPLE_LESS)
        assert result["name"] == "myapp"
        assert result["version"] == "1.2.3"

    def test_no_app_block_returns_empty(self):
        assert _parse_app_block("no app here") == {}


class TestParseEntities:
    def test_count(self):
        result = _parse_entities(SAMPLE_LESS)
        assert len(result) == 2

    def test_entity_name(self):
        result = _parse_entities(SAMPLE_LESS)
        names = [e["name"] for e in result]
        assert "User" in names
        assert "Order" in names

    def test_annotations_extracted(self):
        result = _parse_entities(SAMPLE_LESS)
        user = next(e for e in result if e["name"] == "User")
        assert user["annotations"]["intent"] == "identify human users"
        assert user["annotations"]["domain"] == "auth"

    def test_fields_extracted(self):
        result = _parse_entities(SAMPLE_LESS)
        user = next(e for e in result if e["name"] == "User")
        assert any("fields" in f for f in user["fields"])

    def test_no_entities_returns_empty(self):
        assert _parse_entities("app { name: x; }") == []

    def test_entity_without_annotations(self):
        result = _parse_entities(SAMPLE_LESS)
        order = next(e for e in result if e["name"] == "Order")
        assert order["annotations"] == {}


class TestParseInterfaces:
    def test_count(self):
        result = _parse_interfaces(SAMPLE_LESS)
        assert len(result) == 1

    def test_type(self):
        result = _parse_interfaces(SAMPLE_LESS)
        assert result[0]["type"] == "rest"

    def test_framework(self):
        result = _parse_interfaces(SAMPLE_LESS)
        assert result[0]["framework"] == "fastapi"

    def test_no_interfaces(self):
        assert _parse_interfaces("app { name: x; }") == []


class TestParseWorkflows:
    def test_count(self):
        result = _parse_workflows(SAMPLE_LESS)
        assert len(result) == 1

    def test_name(self):
        result = _parse_workflows(SAMPLE_LESS)
        assert result[0]["name"] == "deploy"

    def test_trigger(self):
        result = _parse_workflows(SAMPLE_LESS)
        assert result[0]["trigger"] == "push"

    def test_steps(self):
        result = _parse_workflows(SAMPLE_LESS)
        assert len(result[0]["steps"]) == 2

    def test_annotations(self):
        result = _parse_workflows(SAMPLE_LESS)
        assert result[0]["annotations"]["intent"] == "ship"

    def test_no_workflows(self):
        assert _parse_workflows("app {}") == []


class TestParseDeploy:
    def test_platform(self):
        result = _parse_deploy(SAMPLE_LESS)
        assert result["platform"] == "k8s"

    def test_no_deploy(self):
        assert _parse_deploy("app {}") == {}


class TestParseEnvironment:
    def test_name(self):
        result = _parse_environment(SAMPLE_LESS)
        assert result["name"] == "production"

    def test_host(self):
        result = _parse_environment(SAMPLE_LESS)
        assert result["host"] == "prod.example.com"

    def test_no_environment(self):
        assert _parse_environment("app {}") == {}


class TestParseIntegrations:
    def test_count(self):
        result = _parse_integrations(SAMPLE_LESS)
        assert len(result) == 1

    def test_name(self):
        result = _parse_integrations(SAMPLE_LESS)
        assert result[0]["name"] == "stripe"

    def test_types_deduped(self):
        result = _parse_integrations(SAMPLE_LESS)
        assert set(result[0]["types"]) == {"payment", "webhook"}

    def test_no_integrations(self):
        assert _parse_integrations("app {}") == []


class TestParseDoqlLess:
    def test_returns_all_keys(self, tmp_path):
        f = tmp_path / "app.doql.less"
        f.write_text(SAMPLE_LESS)
        result = parse_doql_less(f)
        assert set(result.keys()) == {"app", "entities", "interfaces", "workflows", "deploy", "environment", "integrations"}

    def test_app_name_in_result(self, tmp_path):
        f = tmp_path / "app.doql.less"
        f.write_text(SAMPLE_LESS)
        result = parse_doql_less(f)
        assert result["app"]["name"] == "myapp"

    def test_entities_count(self, tmp_path):
        f = tmp_path / "app.doql.less"
        f.write_text(SAMPLE_LESS)
        result = parse_doql_less(f)
        assert len(result["entities"]) == 2

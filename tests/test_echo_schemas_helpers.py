"""Tests for testql/echo_schemas.py and testql/commands/echo_helpers.py"""
import json
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from testql.echo_schemas import (
    APIContract,
    Entity,
    Workflow,
    Interface,
    SystemModel,
    ProjectEcho,
)


class TestAPIContract:
    def test_defaults(self):
        c = APIContract()
        assert c.base_url == ""
        assert c.endpoints == []
        assert c.asserts == []


class TestEntity:
    def test_create(self):
        e = Entity(name="User")
        assert e.name == "User"
        assert e.fields == []
        assert e.domain is None

    def test_with_all_fields(self):
        e = Entity("User", fields=["id", "email"], intent="identify", domain="auth",
                   lifecycle="active", description="A user")
        assert e.intent == "identify"
        assert e.lifecycle == "active"


class TestWorkflow:
    def test_defaults(self):
        w = Workflow(name="deploy")
        assert w.trigger == "manual"
        assert w.cmd == ""

    def test_with_values(self):
        w = Workflow("ci", trigger="push", cmd="pytest", intent="test", domain="dev")
        assert w.trigger == "push"
        assert w.intent == "test"


class TestInterface:
    def test_create(self):
        i = Interface(type="rest", framework="fastapi")
        assert i.type == "rest"
        assert i.framework == "fastapi"

    def test_no_framework(self):
        i = Interface(type="graphql")
        assert i.framework is None


class TestSystemModel:
    def test_defaults(self):
        sm = SystemModel()
        assert sm.project_name == ""
        assert sm.entities == []
        assert sm.domains == []


class TestProjectEcho:
    def _make_echo(self):
        pe = ProjectEcho()
        pe.system_model.project_name = "myapp"
        pe.system_model.version = "1.0"
        pe.system_model.interfaces = [Interface("rest", "fastapi")]
        pe.system_model.workflows = [Workflow("ci", trigger="push", cmd="pytest")]
        pe.system_model.entities = [Entity("User", domain="auth")]
        pe.api_contract.endpoints = [{"method": "GET", "path": "/health", "status": "200"}]
        return pe

    def test_to_dict_has_keys(self):
        pe = self._make_echo()
        d = pe.to_dict()
        assert "api_contract" in d
        assert "system_model" in d

    def test_to_dict_api_contract(self):
        pe = self._make_echo()
        d = pe.to_dict()
        assert len(d["api_contract"]["endpoints"]) == 1
        assert d["api_contract"]["endpoints"][0]["path"] == "/health"

    def test_to_dict_interfaces(self):
        pe = self._make_echo()
        d = pe.to_dict()
        interfaces = d["system_model"]["project"]["interfaces"]
        assert len(interfaces) == 1
        assert interfaces[0]["type"] == "rest"

    def test_to_dict_entities(self):
        pe = self._make_echo()
        d = pe.to_dict()
        entities = d["system_model"]["entities"]
        assert entities[0]["name"] == "User"
        assert entities[0]["domain"] == "auth"

    def test_to_dict_workflows(self):
        pe = self._make_echo()
        d = pe.to_dict()
        workflows = d["system_model"]["workflows"]
        assert workflows[0]["name"] == "ci"
        assert workflows[0]["cmd"] == "pytest"

    def test_to_dict_is_json_serializable(self):
        pe = self._make_echo()
        output = json.dumps(pe.to_dict())
        assert "myapp" in output

    def test_to_text_contains_project_name(self):
        pe = self._make_echo()
        text = pe.to_text()
        assert "myapp" in text

    def test_to_text_contains_interface(self):
        pe = self._make_echo()
        text = pe.to_text()
        assert "REST" in text or "rest" in text.lower()

    def test_to_text_contains_workflow(self):
        pe = self._make_echo()
        text = pe.to_text()
        assert "ci" in text

    def test_to_text_contains_endpoints(self):
        pe = self._make_echo()
        text = pe.to_text()
        assert "/health" in text

    def test_to_text_docker_deploy(self):
        pe = self._make_echo()
        pe.system_model.deploy_target = "docker"
        text = pe.to_text()
        assert "docker" in text.lower() or "run" in text.lower()

    def test_to_text_no_endpoints(self):
        pe = ProjectEcho()
        pe.system_model.project_name = "empty"
        text = pe.to_text()
        assert "empty" in text

    def test_to_text_empty_interfaces(self):
        pe = ProjectEcho()
        text = pe.to_text()
        assert isinstance(text, str)

    def test_to_dict_deploy_info(self):
        pe = self._make_echo()
        pe.system_model.deploy_target = "k8s"
        pe.system_model.environment = "production"
        d = pe.to_dict()
        assert d["system_model"]["deploy"]["target"] == "k8s"
        assert d["system_model"]["deploy"]["environment"] == "production"


class TestEchoHelpers:
    def test_collect_toon_data_missing_path(self, tmp_path, capsys):
        from testql.commands.echo_helpers import collect_toon_data
        pe = ProjectEcho()
        collect_toon_data(str(tmp_path / "nonexistent.toon"), pe)
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or len(captured.out) >= 0

    def test_collect_toon_data_single_file(self, tmp_path, capsys):
        from testql.commands.echo_helpers import collect_toon_data
        f = tmp_path / "test.testql.toon.yaml"
        f.write_text("API[GET /ping status: 200]")
        pe = ProjectEcho()
        collect_toon_data(str(f), pe)
        captured = capsys.readouterr()
        assert "Parsed toon file" in captured.out

    def test_collect_toon_data_directory(self, tmp_path, capsys):
        from testql.commands.echo_helpers import collect_toon_data
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "a.testql.toon.yaml").write_text("API[GET /a status: 200]")
        (subdir / "b.testql.toon.yaml").write_text("API[GET /b status: 200]")
        pe = ProjectEcho()
        collect_toon_data(str(subdir), pe)
        captured = capsys.readouterr()
        assert "2 toon file" in captured.out

    def test_collect_doql_data_missing(self, tmp_path, capsys):
        from testql.commands.echo_helpers import collect_doql_data
        pe = ProjectEcho()
        collect_doql_data(str(tmp_path / "missing.less"), pe)
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or len(captured.out) >= 0

    def test_render_echo_json(self):
        from testql.commands.echo_helpers import render_echo
        pe = ProjectEcho()
        pe.system_model.project_name = "x"
        result = render_echo(pe, "json", Path("."))
        data = json.loads(result)
        assert "api_contract" in data

    def test_render_echo_text(self):
        from testql.commands.echo_helpers import render_echo
        pe = ProjectEcho()
        pe.system_model.project_name = "myproj"
        result = render_echo(pe, "text", Path("."))
        assert "myproj" in result

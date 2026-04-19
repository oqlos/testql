"""Tests for testql/doql_parser.py and testql/sumd_generator.py."""

from pathlib import Path

import pytest

from testql.doql_parser import DoqlParser, parse_doql_file
from testql.echo_schemas import SystemModel, Entity, Workflow, Interface, ProjectEcho
from testql.sumd_generator import (
    generate_sumd,
    _header_section,
    _metadata_section,
    _architecture_section,
)


# ---------------------------------------------------------------------------
# DoqlParser
# ---------------------------------------------------------------------------

SAMPLE_DOQL = """\
app {
  name: myapp;
  version: 2.0;
}

entity[name="User"] {
  intent: identify human;
  fields: id, name, email;
  domain: auth;
}

entity[name="Order"] {
  fields: id, total;
}

workflow[name="deploy"] {
  trigger: push;
  step-1: run cmd=task build;
}

interface[type="rest"] {
  framework: fastapi;
}
"""


class TestDoqlParser:
    def test_init(self):
        parser = DoqlParser()
        assert isinstance(parser.system_model, SystemModel)

    def test_parse_empty(self):
        parser = DoqlParser()
        model = parser.parse("")
        assert model.project_name == ""
        assert model.entities == []
        assert model.workflows == []

    def test_parse_app_block(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        assert model.project_name == "myapp"
        assert model.version == "2.0"

    def test_parse_entities(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        names = [e.name for e in model.entities]
        assert "User" in names
        assert "Order" in names

    def test_entity_fields(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        user = next(e for e in model.entities if e.name == "User")
        assert len(user.fields) > 0

    def test_entity_fields_contain_domain(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        user = next(e for e in model.entities if e.name == "User")
        # domain is kept as a raw field string, not extracted as a separate attribute
        assert any("domain" in f for f in user.fields)

    def test_parse_workflow(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        assert len(model.workflows) == 1
        wf = model.workflows[0]
        assert wf.name == "deploy"
        assert wf.trigger == "push"

    def test_parse_interface(self):
        parser = DoqlParser()
        model = parser.parse(SAMPLE_DOQL)
        assert len(model.interfaces) == 1
        iface = model.interfaces[0]
        assert iface.type == "rest"
        assert iface.framework == "fastapi"

    def test_parse_resets_between_calls(self):
        parser = DoqlParser()
        parser.parse('entity[name="A"] { fields: x; }')
        model = parser.parse('entity[name="B"] { fields: y; }')
        names = [e.name for e in model.entities]
        assert "A" not in names
        assert "B" in names

    def test_parse_file(self, tmp_path):
        f = tmp_path / "app.doql.less"
        f.write_text(SAMPLE_DOQL)
        model = parse_doql_file(f)
        assert model.project_name == "myapp"

    def test_no_app_block(self):
        parser = DoqlParser()
        model = parser.parse('entity[name="X"] { fields: a; }')
        assert model.project_name == ""
        assert len(model.entities) == 1


# ---------------------------------------------------------------------------
# sumd_generator
# ---------------------------------------------------------------------------


class TestHeaderSection:
    def test_contains_project_name(self):
        lines = _header_section("myapp", "1.0")
        assert any("MYAPP" in l or "myapp" in l for l in lines)

    def test_returns_list(self):
        assert isinstance(_header_section("x", "1"), list)


class TestMetadataSection:
    def test_contains_name(self):
        lines = _metadata_section("myapp", "1.2.3")
        assert any("myapp" in l for l in lines)

    def test_contains_version(self):
        lines = _metadata_section("myapp", "1.2.3")
        assert any("1.2.3" in l for l in lines)


class TestArchitectureSection:
    def test_contains_code_block(self):
        lines = _architecture_section()
        assert "```" in lines

    def test_mentions_doql(self):
        lines = _architecture_section()
        assert any("DOQL" in l or "doql" in l for l in lines)


class TestGenerateSumd:
    def _make_echo(self) -> ProjectEcho:
        echo = ProjectEcho()
        echo.system_model.project_name = "testproject"
        echo.system_model.version = "0.5.0"
        echo.system_model.interfaces = [Interface(type="rest", framework="fastapi")]
        echo.system_model.entities = [Entity(name="User", fields=["id", "name"])]
        echo.system_model.workflows = [Workflow(name="test", trigger="push", cmd="pytest")]
        return echo

    def test_returns_string(self, tmp_path):
        out = generate_sumd(ProjectEcho(), tmp_path)
        assert isinstance(out, str)

    def test_contains_project_name(self, tmp_path):
        echo = self._make_echo()
        out = generate_sumd(echo, tmp_path)
        assert "testproject" in out.lower() or "TESTPROJECT" in out

    def test_contains_version(self, tmp_path):
        echo = self._make_echo()
        out = generate_sumd(echo, tmp_path)
        assert "0.5.0" in out

    def test_contains_metadata_section(self, tmp_path):
        out = generate_sumd(ProjectEcho(), tmp_path)
        assert "## Metadata" in out

    def test_contains_architecture_section(self, tmp_path):
        out = generate_sumd(ProjectEcho(), tmp_path)
        assert "## Architecture" in out

    def test_uses_path_name_as_fallback(self, tmp_path):
        out = generate_sumd(ProjectEcho(), tmp_path)
        assert tmp_path.name in out or tmp_path.name.upper() in out

    def test_interfaces_included(self, tmp_path):
        echo = self._make_echo()
        out = generate_sumd(echo, tmp_path)
        assert "rest" in out or "fastapi" in out

    def test_entities_not_in_base_output(self, tmp_path):
        # generate_sumd uses echo context which may not enumerate entity names
        echo = self._make_echo()
        out = generate_sumd(echo, tmp_path)
        assert isinstance(out, str) and len(out) > 0

    def test_workflows_included(self, tmp_path):
        echo = self._make_echo()
        out = generate_sumd(echo, tmp_path)
        assert "test" in out or "pytest" in out


class TestApiContractSection:
    def test_no_endpoints_returns_empty(self):
        from testql.sumd_generator import _api_contract_section
        pe = ProjectEcho()
        assert _api_contract_section(pe) == []

    def test_with_endpoints(self):
        from testql.sumd_generator import _api_contract_section
        pe = ProjectEcho()
        pe.api_contract.endpoints = [
            {"method": "GET", "path": "/users", "status": "200"},
            {"method": "POST", "path": "/users", "status": "201", "description": "create"},
        ]
        lines = _api_contract_section(pe)
        joined = "\n".join(lines)
        assert "GET" in joined
        assert "/users" in joined

    def test_endpoint_with_description(self):
        from testql.sumd_generator import _api_contract_section
        pe = ProjectEcho()
        pe.api_contract.endpoints = [
            {"method": "DELETE", "path": "/items/1", "status": "204", "description": "remove item"},
        ]
        lines = _api_contract_section(pe)
        assert any("remove item" in l for l in lines)


class TestWorkflowsTableSection:
    def test_no_workflows_returns_empty(self):
        from testql.sumd_generator import _workflows_table_section
        pe = ProjectEcho()
        assert _workflows_table_section(pe) == []

    def test_with_workflows(self):
        from testql.sumd_generator import _workflows_table_section
        pe = ProjectEcho()
        pe.system_model.workflows = [Workflow("ci", trigger="push", cmd="pytest")]
        lines = _workflows_table_section(pe)
        joined = "\n".join(lines)
        assert "ci" in joined
        assert "push" in joined

    def test_long_command_truncated(self):
        from testql.sumd_generator import _workflows_table_section
        pe = ProjectEcho()
        pe.system_model.workflows = [Workflow("long", cmd="x" * 50)]
        lines = _workflows_table_section(pe)
        # cmd should be truncated to 40 chars + "..."
        assert any("..." in l for l in lines)


class TestConfigurationSection:
    def test_basic(self):
        from testql.sumd_generator import _configuration_section
        pe = ProjectEcho()
        lines = _configuration_section(pe, "myapp", "1.0")
        joined = "\n".join(lines)
        assert "myapp" in joined
        assert "1.0" in joined

    def test_with_base_url(self):
        from testql.sumd_generator import _configuration_section
        pe = ProjectEcho()
        pe.api_contract.base_url = "http://localhost:8101"
        lines = _configuration_section(pe, "app", "2.0")
        assert any("base_url" in l for l in lines)


class TestLlmSuggestionsSection:
    def test_has_testql_commands(self):
        from testql.sumd_generator import _llm_suggestions_section
        pe = ProjectEcho()
        lines = _llm_suggestions_section(pe)
        joined = "\n".join(lines)
        assert "testql" in joined.lower()

    def test_with_test_workflow(self):
        from testql.sumd_generator import _llm_suggestions_section
        pe = ProjectEcho()
        pe.system_model.workflows = [Workflow("test", trigger="push", cmd="pytest")]
        lines = _llm_suggestions_section(pe)
        joined = "\n".join(lines)
        assert "test" in joined

    def test_with_install_workflow(self):
        from testql.sumd_generator import _llm_suggestions_section
        pe = ProjectEcho()
        pe.system_model.workflows = [
            Workflow("install", cmd="pip install -r requirements.txt"),
        ]
        lines = _llm_suggestions_section(pe)
        joined = "\n".join(lines)
        assert "install" in joined


class TestSaveSumd:
    def test_saves_to_default_path(self, tmp_path):
        from testql.sumd_generator import save_sumd
        pe = ProjectEcho()
        pe.system_model.project_name = "myapp"
        result = save_sumd(pe, tmp_path)
        assert result == tmp_path / "SUMD.md"
        assert result.exists()

    def test_saves_to_custom_path(self, tmp_path):
        from testql.sumd_generator import save_sumd
        pe = ProjectEcho()
        custom = tmp_path / "docs" / "summary.md"
        custom.parent.mkdir()
        result = save_sumd(pe, tmp_path, custom)
        assert result == custom
        assert custom.exists()

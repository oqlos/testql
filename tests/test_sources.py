"""Tests for `testql.generators.sources.*`."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.generators.sources import (
    BaseSource,
    GraphQLSource,
    NLSource,
    OqlSource,
    OpenAPISource,
    ProtoSource,
    PytestSource,
    SqlSource,
    UISource,
    available_sources,
    get_source,
)
from testql.generators.sources.config_source import (
    _extract_phony_targets,
    _extract_target_commands,
    _load_includes,
    _parse_makefile,
)
from testql.ir import (
    ApiStep,
    GraphqlStep,
    GuiStep,
    ProtoStep,
    SqlStep,
    TestPlan,
)


OPENAPI_SPEC = """\
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0"
servers:
  - url: http://localhost:8000
paths:
  /health:
    get:
      operationId: getHealth
      responses:
        "200": { description: OK }
  /items:
    post:
      operationId: createItem
      responses:
        "201": { description: Created }
"""


SQL_DDL = """\
CREATE TABLE users (id INT PRIMARY KEY, email VARCHAR(255));
CREATE TABLE orders (id INT PRIMARY KEY, user_id INT);
"""


PROTO_TEXT = """\
syntax = "proto3";
package example;

message User {
    int64 id = 1;
    string email = 2;
}

message Order {
    int64 id = 1;
    double total = 2;
}
"""


SDL = """\
type User { id: ID! email: String }
type Query { users: [User] }
"""


HTML = """\
<html>
<body>
  <a href="/login">Login</a>
  <form>
    <input name="email" />
    <input name="password" />
    <button>Submit</button>
  </form>
</body>
</html>
"""


NL_MD = """\
# SCENARIO: Quick smoke
TYPE: gui
LANG: en

1. Open `/login`
2. Click `#submit`
"""


# ── Registry ────────────────────────────────────────────────────────────────


_BUILTIN_SOURCE_NAMES = {
    "openapi", "sql", "proto", "graphql", "nl", "ui", "page", "pytest", "oql",
}

_CONFIG_SOURCE_ALIASES = {"config", "makefile", "taskfile", "docker-compose", "buf"}


class TestRegistry:
    def test_builtin_sources(self):
        assert set(available_sources()) == (_BUILTIN_SOURCE_NAMES | _CONFIG_SOURCE_ALIASES)

    @pytest.mark.parametrize("name", sorted(_BUILTIN_SOURCE_NAMES))
    def test_get_source(self, name):
        s = get_source(name)
        assert s is not None
        assert isinstance(s, BaseSource)
        assert s.name == name

    def test_get_unknown(self):
        assert get_source("nope") is None

    @pytest.mark.parametrize("name", sorted(_CONFIG_SOURCE_ALIASES))
    def test_get_config_aliases(self, name):
        s = get_source(name)
        assert s is not None
        assert isinstance(s, BaseSource)
        assert s.name == "config"


# ── OpenAPI ────────────────────────────────────────────────────────────────


class TestOpenAPISource:
    def test_paths_become_api_steps(self):
        plan = OpenAPISource().load(OPENAPI_SPEC)
        steps = [s for s in plan.steps if isinstance(s, ApiStep)]
        assert len(steps) == 2
        methods = {s.method for s in steps}
        assert methods == {"GET", "POST"}

    def test_status_picks_lowest_2xx(self):
        plan = OpenAPISource().load(OPENAPI_SPEC)
        post = next(s for s in plan.steps if isinstance(s, ApiStep) and s.method == "POST")
        assert post.expect_status == 201

    def test_default_status_when_unspecified(self):
        spec = """\
openapi: "3.0.0"
info: { title: x, version: "1" }
paths:
  /x:
    get: {}
"""
        plan = OpenAPISource().load(spec)
        s = next(iter(plan.steps))
        assert s.expect_status == 200

    def test_base_url_from_servers(self):
        plan = OpenAPISource().load(OPENAPI_SPEC)
        assert plan.config["base_url"] == "http://localhost:8000"

    def test_metadata_from_info(self):
        plan = OpenAPISource().load(OPENAPI_SPEC)
        assert plan.metadata.name == "Test API"
        assert plan.metadata.version == "1.0"
        assert plan.metadata.type == "api"

    def test_load_from_path(self, tmp_path: Path):
        p = tmp_path / "api.yaml"
        p.write_text(OPENAPI_SPEC, encoding="utf-8")
        plan = OpenAPISource().load(p)
        assert len(plan.steps) == 2

    def test_load_from_dict(self):
        import yaml
        plan = OpenAPISource().load(yaml.safe_load(OPENAPI_SPEC))
        assert len(plan.steps) == 2


# ── SQL ────────────────────────────────────────────────────────────────────


class TestSqlSource:
    def test_two_tables_yield_four_steps(self):
        plan = SqlSource().load(SQL_DDL)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        # 2 tables × 2 queries (count + sample) = 4
        assert len(sql_steps) == 4

    def test_count_step_has_assert(self):
        plan = SqlSource().load(SQL_DDL)
        users_count = next(s for s in plan.steps
                           if isinstance(s, SqlStep) and s.name == "count_users")
        assert any(a.op == ">=" for a in users_count.asserts)

    def test_schema_fixture_emitted(self):
        plan = SqlSource().load(SQL_DDL)
        assert any(f.name == "sql.schema" for f in plan.fixtures)

    def test_dialect_propagates(self):
        plan = SqlSource(dialect="postgres").load(SQL_DDL)
        for s in plan.steps:
            if isinstance(s, SqlStep):
                assert s.dialect == "postgres"

    def test_load_from_path(self, tmp_path: Path):
        p = tmp_path / "schema.sql"
        p.write_text(SQL_DDL, encoding="utf-8")
        plan = SqlSource().load(p)
        assert plan.steps


# ── Proto ──────────────────────────────────────────────────────────────────


class TestProtoSource:
    def test_one_step_per_message(self):
        plan = ProtoSource().load(PROTO_TEXT)
        steps = [s for s in plan.steps if isinstance(s, ProtoStep)]
        assert len(steps) == 2
        names = {s.name for s in steps}
        assert names == {"User", "Order"}

    def test_sample_fields_blob(self):
        plan = ProtoSource().load(PROTO_TEXT)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        assert "id:int64=" in user.fields["_raw"]
        assert "email:string=" in user.fields["_raw"]

    def test_round_trip_assertion(self):
        plan = ProtoSource().load(PROTO_TEXT)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        assert any(a.expected == "round_trip_equal" for a in user.asserts)

    def test_schema_fixture(self):
        plan = ProtoSource().load(PROTO_TEXT)
        assert any(f.name == "proto.schemas" for f in plan.fixtures)


# ── GraphQL ────────────────────────────────────────────────────────────────


class TestGraphQLSource:
    def test_one_step_per_object_type(self):
        plan = GraphQLSource().load(SDL)
        steps = [s for s in plan.steps if isinstance(s, GraphqlStep)]
        # User and Query — but Query is also OBJECT, so 2 smoke queries.
        assert len(steps) >= 1
        assert any(s.name == "smoke_User" for s in steps)

    def test_endpoint_set_in_config(self):
        plan = GraphQLSource(endpoint="https://api/graphql").load(SDL)
        assert plan.config["endpoint"] == "https://api/graphql"

    def test_query_body_uses_field_list(self):
        plan = GraphQLSource().load(SDL)
        s = next(x for x in plan.steps if isinstance(x, GraphqlStep) and x.name == "smoke_User")
        assert "id" in s.body and "email" in s.body


# ── NL ─────────────────────────────────────────────────────────────────────


class TestNLSource:
    def test_delegates_to_adapter(self):
        plan = NLSource().load(NL_MD)
        assert plan.metadata.name == "Quick smoke"
        # navigate + click → 2 GUI steps
        gui = [s for s in plan.steps if isinstance(s, GuiStep)]
        assert len(gui) == 2


# ── UI ─────────────────────────────────────────────────────────────────────


class TestUISource:
    def test_navigate_first(self):
        plan = UISource().load(HTML)
        assert isinstance(plan.steps[0], GuiStep)
        assert plan.steps[0].action == "navigate"

    def test_inputs_extracted(self):
        plan = UISource().load(HTML)
        inputs = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "input"]
        names = {s.selector for s in inputs}
        assert "[name='email']" in names
        assert "[name='password']" in names

    def test_buttons_extracted(self):
        plan = UISource().load(HTML)
        buttons = [s for s in plan.steps if isinstance(s, GuiStep) and s.action == "click"]
        assert buttons, "expected at least one click step"


# ── Config Source ──────────────────────────────────────────────────────────────


class TestConfigSourceHelpers:
    def test_load_includes_single_file(self, tmp_path: Path):
        """Test loading a single included .mk file."""
        mk_file = tmp_path / "test.mk"
        mk_file.write_text("test-target:\n\techo test")
        content = "include test.mk"
        result = _load_includes(content, tmp_path / "Makefile")
        assert "test-target" in result
        assert "echo test" in result

    def test_load_includes_glob_pattern(self, tmp_path: Path):
        """Test loading multiple .mk files via glob pattern."""
        (tmp_path / "mk1.mk").write_text("target1:\n\techo 1")
        (tmp_path / "mk2.mk").write_text("target2:\n\techo 2")
        content = "include *.mk"
        result = _load_includes(content, tmp_path / "Makefile")
        assert "target1" in result
        assert "target2" in result

    def test_load_includes_nonexistent_file(self, tmp_path: Path):
        """Test that non-existent includes are handled gracefully."""
        content = "include nonexistent.mk"
        result = _load_includes(content, tmp_path / "Makefile")
        # Should not crash, just return original content
        assert "include nonexistent.mk" in result

    def test_extract_phony_targets(self):
        """Test extracting .PHONY target names."""
        content = ".PHONY: test build clean\n.PHONY: deploy"
        result = _extract_phony_targets(content)
        assert set(result) == {"test", "build", "clean", "deploy"}

    def test_extract_phony_targets_multiline(self):
        """Test .PHONY targets on multiple lines."""
        content = """
.PHONY: test build
.PHONY: deploy clean
"""
        result = _extract_phony_targets(content)
        assert set(result) == {"test", "build", "deploy", "clean"}

    def test_extract_phony_targets_none(self):
        """Test content with no .PHONY targets."""
        content = "all:\n\techo all"
        result = _extract_phony_targets(content)
        assert result == []

    def test_extract_target_commands_simple(self):
        """Test extracting simple commands."""
        content = """
target:
\techo hello
\techo world
"""
        result = _extract_target_commands(content, content.index("target:") + len("target:"))
        assert result == ["echo hello", "echo world"]

    def test_extract_target_commands_with_prefixes(self):
        """Test that @, -, + prefixes are removed."""
        content = """
target:
\t@echo silent
\t-echo ignore
\t+echo plus
"""
        result = _extract_target_commands(content, content.index("target:") + len("target:"))
        assert result == ["echo silent", "echo ignore", "echo plus"]

    def test_extract_target_commands_stops_at_next_target(self):
        """Test that command extraction stops at next target definition."""
        content = """
target1:
\techo 1

target2:
\techo 2
"""
        result = _extract_target_commands(content, content.index("target1:") + len("target1:"))
        assert result == ["echo 1"]
        assert "echo 2" not in result

    def test_extract_target_commands_ignores_comments(self):
        """Test that comments are skipped."""
        content = """
target:
\t# comment
\techo actual
"""
        result = _extract_target_commands(content, content.index("target:") + len("target:"))
        assert result == ["echo actual"]

    def test_extract_target_commands_max_lines(self):
        """Test that extraction is limited to 10 lines."""
        content = "\n".join([f"\tcmd{i}" for i in range(15)])
        result = _extract_target_commands(content, 0)
        assert len(result) <= 10


class TestConfigSourceIntegration:
    def test_parse_makefile_simple(self, tmp_path: Path):
        """Test parsing a simple Makefile."""
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
.PHONY: test build

test:
\tpython -m pytest

build:
\tpoetry build
""")
        result = _parse_makefile(makefile.read_text(), makefile)
        assert len(result) == 2
        assert any(t["name"] == "test" for t in result)
        assert any(t["name"] == "build" for t in result)

    def test_parse_makefile_with_includes(self, tmp_path: Path):
        """Test parsing Makefile with included files."""
        mk_file = tmp_path / "common.mk"
        mk_file.write_text("""
.PHONY: lint

lint:
\truff check
""")
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
include common.mk

test:
\tpython -m pytest
""")
        result = _parse_makefile(makefile.read_text(), makefile)
        assert len(result) == 2
        assert any(t["name"] == "lint" for t in result)
        assert any(t["name"] == "test" for t in result)

    def test_parse_makefile_phony_flag(self, tmp_path: Path):
        """Test that .PHONY flag is correctly set."""
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
.PHONY: test

test:
\tpython -m pytest

all:
\tpoetry install
""")
        result = _parse_makefile(makefile.read_text(), makefile)
        test_target = next(t for t in result if t["name"] == "test")
        all_target = next(t for t in result if t["name"] == "all")
        assert test_target["is_phony"] is True
        assert all_target["is_phony"] is False

    def test_parse_makefile_comments(self, tmp_path: Path):
        """Test that target comments are extracted."""
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
test: ## Run tests
\tpython -m pytest

build: ## Build package
\tpoetry build
""")
        result = _parse_makefile(makefile.read_text(), makefile)
        test_target = next(t for t in result if t["name"] == "test")
        build_target = next(t for t in result if t["name"] == "build")
        assert test_target["comment"] == "Run tests"
        assert build_target["comment"] == "Build package"

    def test_parse_makefile_excludes_special_targets(self, tmp_path: Path):
        """Test that .PHONY and .DEFAULT_GOAL are excluded."""
        makefile = tmp_path / "Makefile"
        makefile.write_text("""
.PHONY: test
.DEFAULT_GOAL = test

test:
\tpython -m pytest
""")
        result = _parse_makefile(makefile.read_text(), makefile)
        assert not any(t["name"] == ".PHONY" for t in result)
        assert not any(t["name"] == ".DEFAULT_GOAL" for t in result)
        assert any(t["name"] == "test" for t in result)

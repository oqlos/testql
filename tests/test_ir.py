"""Tests for the Unified IR (`testql.ir`)."""

from __future__ import annotations

from testql.ir import (
    ApiStep,
    Assertion,
    EncoderStep,
    Fixture,
    GraphqlStep,
    GuiStep,
    NlStep,
    ProtoStep,
    ScenarioMetadata,
    ShellStep,
    SqlStep,
    Step,
    TestPlan,
    UnitStep,
)


class TestScenarioMetadata:
    def test_defaults(self):
        md = ScenarioMetadata()
        assert md.name == ""
        assert md.type == ""
        assert md.version is None
        assert md.lang is None
        assert md.tags == []
        assert md.extra == {}

    def test_to_dict_minimal(self):
        md = ScenarioMetadata(name="login", type="gui")
        d = md.to_dict()
        assert d["name"] == "login"
        assert d["type"] == "gui"
        assert "version" not in d
        assert "lang" not in d

    def test_to_dict_full(self):
        md = ScenarioMetadata(name="x", type="api", version="1.0", lang="pl", tags=["smoke"], extra={"a": "b"})
        d = md.to_dict()
        assert d["version"] == "1.0"
        assert d["lang"] == "pl"
        assert d["tags"] == ["smoke"]
        assert d["extra"] == {"a": "b"}


class TestAssertion:
    def test_defaults(self):
        a = Assertion(field="status")
        assert a.op == "=="
        assert a.expected is None

    def test_to_dict_minimal(self):
        a = Assertion(field="status", op="==", expected=200)
        d = a.to_dict()
        assert d == {"field": "status", "op": "==", "expected": 200}

    def test_to_dict_full(self):
        a = Assertion(field="x", op=">", expected=1, actual_path="data.x", message="check")
        d = a.to_dict()
        assert d["actual_path"] == "data.x"
        assert d["message"] == "check"


class TestFixture:
    def test_defaults(self):
        f = Fixture(name="db")
        assert f.scope == "scenario"
        assert f.setup is None
        assert f.teardown is None

    def test_to_dict(self):
        f = Fixture(name="db", setup={"url": "..."}, teardown="DROP", scope="session")
        d = f.to_dict()
        assert d["name"] == "db"
        assert d["setup"] == {"url": "..."}
        assert d["teardown"] == "DROP"
        assert d["scope"] == "session"


class TestStepVariants:
    def test_base_step_kind(self):
        s = Step()
        assert s.kind == "generic"

    def test_api_step(self):
        s = ApiStep(method="POST", path="/api/x", expect_status=201)
        assert s.kind == "api"
        d = s.to_dict()
        assert d["method"] == "POST"
        assert d["path"] == "/api/x"
        assert d["expect_status"] == 201

    def test_gui_step(self):
        s = GuiStep(action="click", selector="#login")
        assert s.kind == "gui"
        d = s.to_dict()
        assert d["action"] == "click"
        assert d["selector"] == "#login"

    def test_encoder_step(self):
        s = EncoderStep(action="scroll", value=10)
        assert s.kind == "encoder"
        d = s.to_dict()
        assert d["action"] == "scroll"
        assert d["value"] == 10

    def test_shell_step(self):
        s = ShellStep(command="ls -la", expect_exit_code=0)
        assert s.kind == "shell"
        d = s.to_dict()
        assert d["command"] == "ls -la"
        assert d["expect_exit_code"] == 0

    def test_unit_step(self):
        s = UnitStep(target="testql.ir::TestPlan", args=[1], kwargs={"k": "v"})
        assert s.kind == "unit"
        d = s.to_dict()
        assert d["target"] == "testql.ir::TestPlan"
        assert d["args"] == [1]
        assert d["kwargs"] == {"k": "v"}

    def test_nl_step(self):
        s = NlStep(text="Kliknij login", lang="pl")
        assert s.kind == "nl"
        d = s.to_dict()
        assert d["text"] == "Kliknij login"
        assert d["lang"] == "pl"

    def test_sql_step(self):
        s = SqlStep(query="SELECT 1", dialect="postgres", params={"x": 1})
        assert s.kind == "sql"
        d = s.to_dict()
        assert d["query"] == "SELECT 1"
        assert d["dialect"] == "postgres"
        assert d["params"] == {"x": 1}

    def test_proto_step(self):
        s = ProtoStep(schema_file="user.proto", message="User", fields={"id": 1})
        assert s.kind == "proto"
        d = s.to_dict()
        assert d["schema_file"] == "user.proto"
        assert d["message"] == "User"
        assert d["fields"] == {"id": 1}
        assert d["check"] == "round_trip_equal"

    def test_graphql_step(self):
        s = GraphqlStep(operation="mutation", body="mutation X { x }")
        assert s.kind == "graphql"
        d = s.to_dict()
        assert d["operation"] == "mutation"
        assert d["body"] == "mutation X { x }"

    def test_step_with_asserts_and_wait(self):
        s = ApiStep(
            method="GET", path="/x",
            asserts=[Assertion(field="status", op="==", expected=200)],
            wait_ms=50,
        )
        d = s.to_dict()
        assert d["wait_ms"] == 50
        assert d["asserts"][0]["field"] == "status"


class TestTestPlan:
    def test_empty(self):
        plan = TestPlan()
        assert plan.steps == []
        assert plan.fixtures == []
        assert plan.config == {}
        assert plan.metadata.name == ""

    def test_name_and_type_shortcuts(self):
        md = ScenarioMetadata(name="login", type="gui")
        plan = TestPlan(metadata=md)
        assert plan.name == "login"
        assert plan.type == "gui"

    def test_to_dict_round_trip_shape(self):
        plan = TestPlan(
            metadata=ScenarioMetadata(name="x", type="api"),
            steps=[ApiStep(method="GET", path="/")],
            fixtures=[Fixture(name="db")],
            config={"base_url": "http://x"},
        )
        d = plan.to_dict()
        assert d["metadata"]["name"] == "x"
        assert d["steps"][0]["method"] == "GET"
        assert d["fixtures"][0]["name"] == "db"
        assert d["config"]["base_url"] == "http://x"

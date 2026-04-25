"""Tests for `testql.adapters.graphql`."""

from __future__ import annotations

from pathlib import Path

from testql.adapters.graphql import (
    GraphQLDSLAdapter,
    SubscriptionPlan,
    classify_operation,
    parse_schema,
    parse_variables,
)
from testql.adapters.graphql.schema_introspection import has_graphql_core
from testql.ir import GraphqlStep, TestPlan


SAMPLE = """\
# SCENARIO: User GraphQL contract
# TYPE: graphql
# VERSION: 1.0

CONFIG[1]{key, value}:
  endpoint, http://localhost:8000/graphql

QUERY[1]{name, body, variables}:
  getUser, "query($id: ID!) { user(id: $id) { id email } }", "{id: '42'}"

MUTATION[1]{name, body, variables}:
  createUser, "mutation { createUser(name: \\"x\\") { id } }", ""

SUBSCRIPTION[1]{name, body, variables}:
  newUsers, "subscription { newUsers { id email } }", ""

ASSERT[2]{path, op, expected}:
  data.user.id, ==, 42
  data.user.email, contains, @
"""


class TestClassifyOperation:
    def test_query(self):
        assert classify_operation("query { foo }") == "query"

    def test_mutation(self):
        assert classify_operation("mutation { foo }") == "mutation"

    def test_subscription(self):
        assert classify_operation("subscription { foo }") == "subscription"

    def test_default_query(self):
        assert classify_operation("{ foo }") == "query"

    def test_empty(self):
        assert classify_operation("") == "query"


class TestParseVariables:
    def test_basic(self):
        out = parse_variables("{id: '42', limit: 10}")
        assert out == {"id": "42", "limit": 10}

    def test_no_braces(self):
        out = parse_variables("id: 1, name: 'x'")
        assert out == {"id": 1, "name": "x"}

    def test_bool_null(self):
        out = parse_variables("{a: true, b: false, c: null}")
        assert out == {"a": True, "b": False, "c": None}

    def test_float(self):
        out = parse_variables("{x: 1.5}")
        assert out == {"x": 1.5}

    def test_empty(self):
        assert parse_variables(None) == {}
        assert parse_variables("") == {}
        assert parse_variables("{}") == {}


class TestParseSchema:
    def test_object_type(self):
        sdl = """\
type User {
    id: ID!
    email: String
}
"""
        types = parse_schema(sdl)
        names = [t.name for t in types]
        assert "User" in names
        user = next(t for t in types if t.name == "User")
        assert "id" in user.fields
        assert "email" in user.fields

    def test_scalar(self):
        types = parse_schema("scalar DateTime")
        assert any(t.name == "DateTime" and t.kind == "SCALAR" for t in types)

    def test_input_renamed_to_input_object(self):
        types = parse_schema("input Filter { name: String }")
        f = next(t for t in types if t.name == "Filter")
        assert f.kind == "INPUT_OBJECT"

    def test_enum(self):
        types = parse_schema("enum Role { ADMIN USER }")
        e = next(t for t in types if t.name == "Role")
        assert e.kind == "ENUM"

    def test_empty(self):
        assert parse_schema("") == []


class TestSubscriptionPlan:
    def test_to_dict(self):
        plan = SubscriptionPlan(name="x", body="subscription { y }",
                                variables={"a": 1}, endpoint="ws://x")
        d = plan.to_dict()
        assert d["name"] == "x"
        assert d["variables"] == {"a": 1}
        assert d["timeout_ms"] == 5000


class TestAdapterDetect:
    def test_by_extension(self, tmp_path: Path):
        p = tmp_path / "x.graphql.testql.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        result = GraphQLDSLAdapter().detect(p)
        assert result.matches

    def test_by_header(self):
        result = GraphQLDSLAdapter().detect(SAMPLE)
        assert result.matches

    def test_negative(self):
        assert not GraphQLDSLAdapter().detect("nope").matches


class TestAdapterParse:
    def test_metadata(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        assert plan.metadata.name == "User GraphQL contract"
        assert plan.metadata.type == "graphql"

    def test_endpoint_in_config(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        assert plan.config["endpoint"] == "http://localhost:8000/graphql"

    def test_query_step(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        queries = [s for s in plan.steps if isinstance(s, GraphqlStep) and s.operation == "query"]
        assert len(queries) == 1
        assert queries[0].name == "getUser"
        assert queries[0].endpoint == "http://localhost:8000/graphql"
        assert queries[0].variables == {"id": "42"}

    def test_mutation_step(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        mutations = [s for s in plan.steps if isinstance(s, GraphqlStep) and s.operation == "mutation"]
        assert len(mutations) == 1
        assert mutations[0].name == "createUser"

    def test_subscription_step(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        subs = [s for s in plan.steps if isinstance(s, GraphqlStep) and s.operation == "subscription"]
        assert len(subs) == 1
        assert subs[0].name == "newUsers"

    def test_asserts_attached(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        # Asserts attach to the *most recent* step (subscription here).
        subs = [s for s in plan.steps if isinstance(s, GraphqlStep) and s.operation == "subscription"]
        assert subs[0].asserts


class TestAdapterRender:
    def test_round_trip_step_count(self):
        plan = GraphQLDSLAdapter().parse(SAMPLE)
        rendered = GraphQLDSLAdapter().render(plan)
        plan2 = GraphQLDSLAdapter().parse(rendered)
        n1 = sum(1 for s in plan.steps if isinstance(s, GraphqlStep))
        n2 = sum(1 for s in plan2.steps if isinstance(s, GraphqlStep))
        assert n1 == n2


class TestRegistration:
    def test_registered(self):
        from testql.adapters import registry
        a = registry.get("graphql")
        assert a is not None
        assert isinstance(a, GraphQLDSLAdapter)


class TestHasGraphQLCore:
    def test_returns_bool(self):
        assert isinstance(has_graphql_core(), bool)

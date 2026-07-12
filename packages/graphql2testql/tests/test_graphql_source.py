"""Tests for the `graphql2testql` generator source (SDL → TestPlan)."""

from __future__ import annotations

from graphql2testql.source import GraphQLSource
from testql.ir import GraphqlStep


SDL = """\
type User { id: ID! email: String }
type Query { users: [User] }
"""


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

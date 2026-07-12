"""graphql2testql — GraphQL contract adapter plugin for TestQL.

Registers the `graphql` DSL adapter via the `testql.plugins` entry point and
the `graphql` generator source via the `testql.sources` entry point. Optional
`graphql-core` dependency: install via `pip install graphql2testql[sdl]` for
canonical SDL parsing and AST validation — the adapter itself degrades
gracefully without it.
"""

from __future__ import annotations

from .adapter import GraphQLDSLAdapter, parse, render
from .query_executor import classify_operation, parse_variables
from .schema_introspection import (
    INTROSPECTION_QUERY,
    TypeDef,
    has_graphql_core,
    parse_schema,
)
from .subscription_runner import SubscriptionPlan


def register_testql_plugin(registry) -> None:
    """`testql.plugins` entry-point hook — see `AdapterRegistry.load_plugins`."""
    registry.register(GraphQLDSLAdapter())


__all__ = [
    "GraphQLDSLAdapter", "parse", "render",
    "INTROSPECTION_QUERY", "TypeDef", "parse_schema", "has_graphql_core",
    "classify_operation", "parse_variables",
    "SubscriptionPlan",
    "register_testql_plugin",
]

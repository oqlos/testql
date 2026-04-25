"""testql.adapters.graphql — GraphQL contract adapter (Phase 3).

Optional `graphql-core` dependency: install via `pip install testql[graphql]`
for canonical SDL parsing and AST validation. The adapter itself works
without graphql-core — only the SDL helpers degrade gracefully.
"""

from __future__ import annotations

from .graphql_adapter import GraphQLDSLAdapter, parse, render
from .query_executor import classify_operation, parse_variables
from .schema_introspection import (
    INTROSPECTION_QUERY,
    TypeDef,
    has_graphql_core,
    parse_schema,
)
from .subscription_runner import SubscriptionPlan

__all__ = [
    "GraphQLDSLAdapter", "parse", "render",
    "INTROSPECTION_QUERY", "TypeDef", "parse_schema", "has_graphql_core",
    "classify_operation", "parse_variables",
    "SubscriptionPlan",
]

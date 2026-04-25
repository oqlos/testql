"""testql.adapters — DSL adapter registry and built-in adapters.

Phase 0 introduces the abstraction. Subsequent phases (NL, SQL, Proto,
GraphQL) plug in by registering a `BaseDSLAdapter` subclass with the
module-level `registry`.
"""

from __future__ import annotations

from .base import (
    BaseDSLAdapter,
    DSLDetectionResult,
    SourceLike,
    ValidationIssue,
    read_source,
)
from .graphql import GraphQLDSLAdapter
from .nl import NLDSLAdapter
from .proto import ProtoDSLAdapter
from .registry import AdapterRegistry, get_registry
from .scenario_yaml import ScenarioYamlAdapter
from .sql import SqlDSLAdapter
from .testtoon_adapter import TestToonAdapter

# Module-level singleton registry, pre-populated with built-in adapters.
registry: AdapterRegistry = get_registry()
registry.register(ScenarioYamlAdapter())
registry.register(TestToonAdapter())
registry.register(NLDSLAdapter())
registry.register(SqlDSLAdapter())
registry.register(ProtoDSLAdapter())
registry.register(GraphQLDSLAdapter())
registry.ensure_plugins_loaded()

__all__ = [
    "BaseDSLAdapter",
    "DSLDetectionResult",
    "ValidationIssue",
    "SourceLike",
    "AdapterRegistry",
    "TestToonAdapter",
    "ScenarioYamlAdapter",
    "NLDSLAdapter",
    "SqlDSLAdapter",
    "ProtoDSLAdapter",
    "GraphQLDSLAdapter",
    "registry",
    "get_registry",
    "read_source",
]

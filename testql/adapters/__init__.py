"""testql.adapters — DSL adapter registry and built-in adapters.

Phase 0 introduces the abstraction. Subsequent phases (NL, SQL, Proto)
plug in by registering a `BaseDSLAdapter` subclass with the module-level
`registry`. Externally packaged adapters (e.g. `graphql2testql`) register
through the `testql.plugins` entry-point group instead.
"""

from __future__ import annotations

from .base import (
    BaseDSLAdapter,
    DSLDetectionResult,
    SourceLike,
    ValidationIssue,
    read_source,
)
from .nl import NLDSLAdapter
from .nlp2dsl import Nlp2DslAdapter
from .nlp2env import Nlp2EnvAdapter
from .registry import AdapterRegistry, get_registry
from .scenario_yaml import ScenarioYamlAdapter
from .testtoon_adapter import TestToonAdapter

# Module-level singleton registry, pre-populated with built-in adapters.
registry: AdapterRegistry = get_registry()
registry.register(ScenarioYamlAdapter())
registry.register(TestToonAdapter())
registry.register(NLDSLAdapter())
registry.register(Nlp2DslAdapter())
registry.register(Nlp2EnvAdapter())
# Entry-point plugins (`testql.plugins` group) are loaded lazily on first
# registry lookup — NOT here. Loading them at import time re-enters any
# plugin whose own import chain is what pulled `testql.adapters` in.

__all__ = [
    "BaseDSLAdapter",
    "DSLDetectionResult",
    "ValidationIssue",
    "SourceLike",
    "AdapterRegistry",
    "TestToonAdapter",
    "ScenarioYamlAdapter",
    "NLDSLAdapter",
    "Nlp2DslAdapter",
    "Nlp2EnvAdapter",
    "registry",
    "get_registry",
    "read_source",
]

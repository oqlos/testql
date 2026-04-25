"""testql.generators.sources — convert external artifacts into Unified IR.

Each source class implements `BaseSource`. The module-level `SOURCES` mapping
is auto-populated from the bundled built-ins and used by `pipeline.run()`.
"""

from __future__ import annotations

from typing import Optional

from .base import BaseSource, SourceLike
from .graphql_source import GraphQLSource
from .nl_source import NLSource
from .openapi_source import OpenAPISource
from .oql_source import OqlSource
from .proto_source import ProtoSource
from .pytest_source import PytestSource
from .sql_source import SqlSource
from .ui_source import UISource


_BUILTIN: dict[str, type[BaseSource]] = {
    "openapi": OpenAPISource,
    "sql": SqlSource,
    "proto": ProtoSource,
    "graphql": GraphQLSource,
    "nl": NLSource,
    "ui": UISource,
    "pytest": PytestSource,
    "oql": OqlSource,
}


def get_source(name: str) -> Optional[BaseSource]:
    """Instantiate a registered source by name (e.g. "openapi")."""
    cls = _BUILTIN.get(name.lower())
    return cls() if cls else None


def available_sources() -> list[str]:
    return sorted(_BUILTIN.keys())


__all__ = [
    "BaseSource",
    "SourceLike",
    "OpenAPISource",
    "SqlSource",
    "ProtoSource",
    "GraphQLSource",
    "NLSource",
    "UISource",
    "PytestSource",
    "OqlSource",
    "get_source",
    "available_sources",
]

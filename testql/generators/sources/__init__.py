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
from .oql_models import OqlCommand, ParsedScenario
from .oql_parser import OqlParser
from .proto_source import ProtoSource
from .pytest_source import PytestSource
from .sql_source import SqlSource
from .ui_source import UISource
from .page_source import PageSource


_BUILTIN: dict[str, type[BaseSource]] = {
    "openapi": OpenAPISource,
    "sql": SqlSource,
    "proto": ProtoSource,
    "graphql": GraphQLSource,
    "nl": NLSource,
    "ui": UISource,
    "page": PageSource,
    "pytest": PytestSource,
    "oql": OqlSource,
}


def _get_config_source() -> type[BaseSource]:
    """Lazy import to avoid circular dependency."""
    from .config_source import ConfigSource
    return ConfigSource


def get_source(name: str) -> Optional[BaseSource]:
    """Instantiate a registered source by name (e.g. "openapi")."""
    cls = _BUILTIN.get(name.lower())
    if cls is None and name.lower() in ("config", "makefile", "taskfile", "docker-compose", "buf"):
        cls = _get_config_source()
    return cls() if cls else None


def get_source(name: str) -> Optional[BaseSource]:
    """Instantiate a registered source by name (e.g. "openapi")."""
    cls = _BUILTIN.get(name.lower())
    if cls is None and name.lower() in ("config", "makefile", "taskfile", "docker-compose", "buf"):
        from .config_source import ConfigSource
        cls = ConfigSource
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
    "PageSource",
    "PytestSource",
    "OqlSource",
    "OqlCommand",
    "ParsedScenario",
    "OqlParser",
    "get_source",
    "available_sources",
]

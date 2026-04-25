"""GraphQL SDL → TestPlan IR (one introspection query per declared type)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from testql.adapters.graphql.schema_introspection import TypeDef, parse_schema
from testql.ir import Assertion, GraphqlStep, ScenarioMetadata, TestPlan

from .base import BaseSource, SourceLike


def _load_sdl(source: SourceLike) -> str:
    if isinstance(source, dict):
        return str(source.get("sdl", ""))
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if "\n" not in source and Path(source).is_file():
        return Path(source).read_text(encoding="utf-8")
    return source


def _type_to_query(t: TypeDef, endpoint: str) -> GraphqlStep:
    """Generate a smoke query for a top-level OBJECT/INTERFACE type."""
    field_list = " ".join(t.fields[:5]) or "__typename"
    body = f"query {{ {t.name[0].lower()}{t.name[1:]} {{ {field_list} }} }}"
    return GraphqlStep(
        name=f"smoke_{t.name}",
        operation="query",
        body=body,
        endpoint=endpoint or None,
        asserts=[Assertion(field=f"data.{t.name[0].lower()}{t.name[1:]}", op="!=", expected=None)],
    )


def _is_smoke_target(t: TypeDef) -> bool:
    if t.kind not in {"OBJECT", "INTERFACE"}:
        return False
    return not t.name.startswith("__") and bool(t.fields)


@dataclass
class GraphQLSource(BaseSource):
    """GraphQL SDL → TestPlan with one smoke query per top-level type."""

    name: str = "graphql"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".graphql", ".gql"))
    endpoint: str = "http://localhost:8000/graphql"

    def load(self, source: SourceLike) -> TestPlan:
        sdl = _load_sdl(source)
        types = parse_schema(sdl)
        plan = TestPlan(metadata=ScenarioMetadata(
            name="GraphQL smoke",
            type="graphql",
            extra={"source": "graphql"},
        ))
        plan.config["endpoint"] = self.endpoint
        for t in types:
            if _is_smoke_target(t):
                plan.steps.append(_type_to_query(t, self.endpoint))
        return plan


__all__ = ["GraphQLSource"]

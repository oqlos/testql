"""GraphQLDSLAdapter — `*.graphql.testql.yaml` scenarios → Unified IR.

Format:

    # SCENARIO: User GraphQL contract
    # TYPE: graphql
    # VERSION: 1.0

    CONFIG[1]{key, value}:
      endpoint, http://localhost:8000/graphql

    QUERY[1]{name, body, variables}:
      getUser, "query($id: ID!) { user(id: $id) { id email } }", "{id: '42'}"

    ASSERT[2]{path, op, expected}:
      data.user.id, ==, 42
      data.user.email, contains, @
"""

from __future__ import annotations

from dataclasses import dataclass, field

from testql.interpreter._testtoon_parser import (
    ToonScript,
    ToonSection,
    parse_testtoon as _parse_testtoon,
)
from testql.ir import (
    Assertion,
    GraphqlStep,
    ScenarioMetadata,
    Step,
    TestPlan,
)

from ..base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source
from .query_executor import classify_operation, parse_variables


# ── Section translators ─────────────────────────────────────────────────────


def _config_section(section: ToonSection) -> dict:
    out: dict = {}
    for row in section.rows:
        key = str(row.get("key", "")).strip()
        if not key:
            continue
        out[key] = row.get("value")
    return out


def _query_section(section: ToonSection, endpoint: str) -> list[GraphqlStep]:
    steps: list[GraphqlStep] = []
    for row in section.rows:
        name = str(row.get("name", "")).strip() or "query"
        body = str(row.get("body", "")).strip()
        if not body:
            continue
        steps.append(GraphqlStep(
            name=name,
            operation=classify_operation(body),
            body=body,
            variables=parse_variables(row.get("variables")),
            endpoint=endpoint or None,
        ))
    return steps


def _mutation_section(section: ToonSection, endpoint: str) -> list[GraphqlStep]:
    steps = _query_section(section, endpoint)
    for s in steps:
        s.operation = "mutation"
    return steps


def _subscription_section(section: ToonSection, endpoint: str) -> list[GraphqlStep]:
    steps = _query_section(section, endpoint)
    for s in steps:
        s.operation = "subscription"
    return steps


def _assert_section(section: ToonSection,
                    steps: list[GraphqlStep]) -> list[Step]:
    """ASSERT[path, op, expected] → asserts attached to the most recent op."""
    asserts: list[Assertion] = []
    for row in section.rows:
        asserts.append(Assertion(
            field=str(row.get("path", "")).strip(),
            op=str(row.get("op", "==")).strip(),
            expected=row.get("expected"),
        ))
    if not asserts:
        return []
    if steps:
        steps[-1].asserts.extend(asserts)
        return []
    return [Step(kind="assert", name="ASSERT", asserts=asserts)]


# ── ToonScript → TestPlan ───────────────────────────────────────────────────


def _toon_to_plan(toon: ToonScript) -> TestPlan:
    metadata = ScenarioMetadata(
        name=toon.meta.get("scenario", ""),
        type=toon.meta.get("type", "graphql"),
        version=toon.meta.get("version"),
        extra={k: v for k, v in toon.meta.items()
               if k not in {"scenario", "type", "version"}},
    )
    plan = TestPlan(metadata=metadata)
    gql_steps: list[GraphqlStep] = []
    for section in toon.sections:
        _apply_section(section, plan, gql_steps)
    return plan


def _apply_section(section: ToonSection, plan: TestPlan,
                   gql_steps: list[GraphqlStep]) -> None:
    handler = _SECTION_HANDLERS.get(section.type)
    if handler is None:
        plan.steps.append(Step(kind=section.type.lower(), name=section.type,
                               extra={"rows": list(section.rows)}))
        return
    handler(section, plan, gql_steps)


def _h_config(section: ToonSection, plan: TestPlan,
              gql_steps: list[GraphqlStep]) -> None:
    plan.config.update(_config_section(section))


def _h_query(section: ToonSection, plan: TestPlan,
             gql_steps: list[GraphqlStep]) -> None:
    endpoint = str(plan.config.get("endpoint", "") or "")
    new_steps = _query_section(section, endpoint)
    gql_steps.extend(new_steps)
    plan.steps.extend(new_steps)


def _h_mutation(section: ToonSection, plan: TestPlan,
                gql_steps: list[GraphqlStep]) -> None:
    endpoint = str(plan.config.get("endpoint", "") or "")
    new_steps = _mutation_section(section, endpoint)
    gql_steps.extend(new_steps)
    plan.steps.extend(new_steps)


def _h_subscription(section: ToonSection, plan: TestPlan,
                    gql_steps: list[GraphqlStep]) -> None:
    endpoint = str(plan.config.get("endpoint", "") or "")
    new_steps = _subscription_section(section, endpoint)
    gql_steps.extend(new_steps)
    plan.steps.extend(new_steps)


def _h_assert(section: ToonSection, plan: TestPlan,
              gql_steps: list[GraphqlStep]) -> None:
    plan.steps.extend(_assert_section(section, gql_steps))


_SECTION_HANDLERS = {
    "CONFIG": _h_config,
    "QUERY": _h_query,
    "MUTATION": _h_mutation,
    "SUBSCRIPTION": _h_subscription,
    "ASSERT": _h_assert,
}


# ── Renderer ────────────────────────────────────────────────────────────────


def _render_meta(metadata: ScenarioMetadata) -> list[str]:
    out = []
    if metadata.name:
        out.append(f"# SCENARIO: {metadata.name}")
    out.append(f"# TYPE: {metadata.type or 'graphql'}")
    if metadata.version:
        out.append(f"# VERSION: {metadata.version}")
    return out


def _render_config(plan: TestPlan) -> list[str]:
    if not plan.config:
        return []
    lines = [f"CONFIG[{len(plan.config)}]" + "{key, value}:"]
    lines.extend(f"  {k}, {v}" for k, v in plan.config.items())
    return lines


def _format_variables(variables: dict) -> str:
    if not variables:
        return ""
    return "{" + ", ".join(f"{k}: {v!r}" for k, v in variables.items()) + "}"


def _render_operation_section(plan: TestPlan, op: str, header: str) -> list[str]:
    steps = [s for s in plan.steps if isinstance(s, GraphqlStep) and s.operation == op]
    if not steps:
        return []
    lines = [f"{header}[{len(steps)}]" + "{name, body, variables}:"]
    lines.extend(f'  {s.name}, "{s.body}", "{_format_variables(s.variables)}"' for s in steps)
    return lines


def _render_asserts(plan: TestPlan) -> list[str]:
    rows: list[tuple[str, str, object]] = []
    for s in plan.steps:
        for a in s.asserts:
            rows.append((a.field, a.op, a.expected))
    if not rows:
        return []
    lines = [f"ASSERT[{len(rows)}]" + "{path, op, expected}:"]
    lines.extend(f"  {p}, {op}, {ex}" for p, op, ex in rows)
    return lines


def _render_plan(plan: TestPlan) -> str:
    parts = _render_meta(plan.metadata)
    if parts:
        parts.append("")
    parts.extend(_render_config(plan))
    parts.extend(_render_operation_section(plan, "query", "QUERY"))
    parts.extend(_render_operation_section(plan, "mutation", "MUTATION"))
    parts.extend(_render_operation_section(plan, "subscription", "SUBSCRIPTION"))
    parts.extend(_render_asserts(plan))
    return "\n".join(parts) + ("\n" if parts else "")


# ── Adapter ─────────────────────────────────────────────────────────────────


@dataclass
class GraphQLDSLAdapter(BaseDSLAdapter):
    """Adapter for `*.graphql.testql.yaml` GraphQL contract scenarios."""

    name: str = "graphql"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".graphql.testql.yaml",
        ".graphql.testql.yml",
    ))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.95, reason=f"extension {ext}")
        if "# TYPE: graphql" in text:
            return DSLDetectionResult(matches=True, confidence=0.7, reason="graphql header")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no graphql markers")

    def parse(self, source: SourceLike) -> TestPlan:
        text, filename = read_source(source)
        toon = _parse_testtoon(text, filename=filename)
        return _toon_to_plan(toon)

    def render(self, plan: TestPlan) -> str:
        return _render_plan(plan)


def parse(source: SourceLike) -> TestPlan:
    return GraphQLDSLAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return GraphQLDSLAdapter().render(plan)


__all__ = ["GraphQLDSLAdapter", "parse", "render"]

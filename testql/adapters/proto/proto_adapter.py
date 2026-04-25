"""ProtoDSLAdapter — `*.proto.testql.yaml` scenarios → Unified IR.

Format:

    # SCENARIO: User proto contract
    # TYPE: proto
    # VERSION: 1.0

    PROTO[1]{file}:
      schemas/user.proto

    MESSAGE[2]{name, fields}:
      User, "id:int64=1, email:string=user@example.com, active:bool=true"
      Order, "id:int64=42, user_id:int64=1, total:double=99.99"

    ASSERT[3]{name, check}:
      User, round_trip_equal
      User, all_required_present
      User_v1_compatible_with_v2, true
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
    Fixture,
    ProtoStep,
    ScenarioMetadata,
    Step,
    TestPlan,
)

from ..base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source


# ── Section translators ─────────────────────────────────────────────────────


def _proto_section(section: ToonSection) -> Fixture:
    files = [str(row.get("file", "")).strip() for row in section.rows
             if str(row.get("file", "")).strip()]
    return Fixture(name="proto.schemas", setup={"files": files}, scope="scenario")


def _message_section(section: ToonSection, schema_files: list[str]) -> list[ProtoStep]:
    steps: list[ProtoStep] = []
    primary_file = schema_files[0] if schema_files else ""
    for row in section.rows:
        name = str(row.get("name", "")).strip()
        fields_blob = str(row.get("fields", "")).strip()
        if not name:
            continue
        steps.append(ProtoStep(
            name=name,
            schema_file=primary_file,
            message=name,
            fields={"_raw": fields_blob} if fields_blob else {},
            check="round_trip_equal",
        ))
    return steps


def _assert_section(section: ToonSection,
                    steps_by_name: dict[str, ProtoStep]) -> list[Step]:
    orphan: list[Assertion] = []
    for row in section.rows:
        target = str(row.get("name", "")).strip()
        check = str(row.get("check", "")).strip() or "round_trip_equal"
        owner = steps_by_name.get(target)
        if owner is not None:
            owner.asserts.append(Assertion(field=target, op="check", expected=check))
        else:
            orphan.append(Assertion(field=target, op="check", expected=check))
    if orphan:
        return [Step(kind="assert", name="ASSERT", asserts=orphan)]
    return []


# ── ToonScript → TestPlan ───────────────────────────────────────────────────


def _toon_to_plan(toon: ToonScript) -> TestPlan:
    metadata = ScenarioMetadata(
        name=toon.meta.get("scenario", ""),
        type=toon.meta.get("type", "proto"),
        version=toon.meta.get("version"),
        extra={k: v for k, v in toon.meta.items()
               if k not in {"scenario", "type", "version"}},
    )
    plan = TestPlan(metadata=metadata)
    proto_steps: list[ProtoStep] = []
    schema_files: list[str] = []
    for section in toon.sections:
        _apply_section(section, plan, proto_steps, schema_files)
    return plan


def _apply_section(section: ToonSection, plan: TestPlan,
                   proto_steps: list[ProtoStep],
                   schema_files: list[str]) -> None:
    handler = _SECTION_HANDLERS.get(section.type)
    if handler is None:
        plan.steps.append(Step(kind=section.type.lower(), name=section.type,
                               extra={"rows": list(section.rows)}))
        return
    handler(section, plan, proto_steps, schema_files)


def _h_proto(section: ToonSection, plan: TestPlan,
             proto_steps: list[ProtoStep], schema_files: list[str]) -> None:
    fx = _proto_section(section)
    plan.fixtures.append(fx)
    schema_files.extend(fx.setup.get("files", []))


def _h_message(section: ToonSection, plan: TestPlan,
               proto_steps: list[ProtoStep], schema_files: list[str]) -> None:
    new_steps = _message_section(section, schema_files)
    proto_steps.extend(new_steps)
    plan.steps.extend(new_steps)


def _h_assert(section: ToonSection, plan: TestPlan,
              proto_steps: list[ProtoStep], schema_files: list[str]) -> None:
    plan.steps.extend(_assert_section(section, {s.name: s for s in proto_steps if s.name}))


_SECTION_HANDLERS = {
    "PROTO": _h_proto,
    "MESSAGE": _h_message,
    "ASSERT": _h_assert,
}


# ── Renderer (IR → proto TestTOON) ──────────────────────────────────────────


def _render_meta(metadata: ScenarioMetadata) -> list[str]:
    out = []
    if metadata.name:
        out.append(f"# SCENARIO: {metadata.name}")
    out.append(f"# TYPE: {metadata.type or 'proto'}")
    if metadata.version:
        out.append(f"# VERSION: {metadata.version}")
    return out


def _render_proto_files(plan: TestPlan) -> list[str]:
    files: list[str] = []
    for fx in plan.fixtures:
        if fx.name == "proto.schemas":
            files.extend((fx.setup or {}).get("files", []))
    if not files:
        return []
    lines = [f"PROTO[{len(files)}]" + "{file}:"]
    lines.extend(f"  {f}" for f in files)
    return lines


def _render_messages(plan: TestPlan) -> list[str]:
    proto_steps = [s for s in plan.steps if isinstance(s, ProtoStep)]
    if not proto_steps:
        return []
    lines = [f"MESSAGE[{len(proto_steps)}]" + "{name, fields}:"]
    for s in proto_steps:
        raw = s.fields.get("_raw", "") if s.fields else ""
        lines.append(f"  {s.name}, \"{raw}\"")
    return lines


def _render_asserts(plan: TestPlan) -> list[str]:
    rows: list[tuple[str, str]] = []
    for s in plan.steps:
        for a in s.asserts:
            rows.append((a.field, str(a.expected)))
    if not rows:
        return []
    lines = [f"ASSERT[{len(rows)}]" + "{name, check}:"]
    lines.extend(f"  {n}, {c}" for n, c in rows)
    return lines


def _render_plan(plan: TestPlan) -> str:
    parts = _render_meta(plan.metadata)
    if parts:
        parts.append("")
    parts.extend(_render_proto_files(plan))
    parts.extend(_render_messages(plan))
    parts.extend(_render_asserts(plan))
    return "\n".join(parts) + ("\n" if parts else "")


# ── Adapter ─────────────────────────────────────────────────────────────────


@dataclass
class ProtoDSLAdapter(BaseDSLAdapter):
    """Adapter for `*.proto.testql.yaml` Protocol Buffers contracts."""

    name: str = "proto"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        ".proto.testql.yaml",
        ".proto.testql.yml",
    ))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, filename = read_source(source)
        for ext in self.file_extensions:
            if filename.lower().endswith(ext):
                return DSLDetectionResult(matches=True, confidence=0.95, reason=f"extension {ext}")
        if "# TYPE: proto" in text or "PROTO[" in text:
            return DSLDetectionResult(matches=True, confidence=0.7, reason="proto header")
        return DSLDetectionResult(matches=False, confidence=0.0, reason="no proto markers")

    def parse(self, source: SourceLike) -> TestPlan:
        text, filename = read_source(source)
        toon = _parse_testtoon(text, filename=filename)
        return _toon_to_plan(toon)

    def render(self, plan: TestPlan) -> str:
        return _render_plan(plan)


# ── Convenience ─────────────────────────────────────────────────────────


def parse(source: SourceLike) -> TestPlan:
    return ProtoDSLAdapter().parse(source)


def render(plan: TestPlan) -> str:
    return ProtoDSLAdapter().render(plan)


__all__ = ["ProtoDSLAdapter", "parse", "render"]

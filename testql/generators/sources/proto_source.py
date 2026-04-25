"""`.proto` schema → TestPlan IR (round-trip tests per message)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from testql.adapters.proto.descriptor_loader import (
    MessageDef,
    ProtoFile,
    SCALAR_TYPES,
    parse_proto,
)
from testql.ir import Assertion, Fixture, ProtoStep, ScenarioMetadata, TestPlan

from .base import BaseSource, SourceLike


_SAMPLE_VALUES: dict[str, str] = {
    "int32": "1", "int64": "1", "uint32": "1", "uint64": "1",
    "sint32": "1", "sint64": "1",
    "fixed32": "1", "fixed64": "1", "sfixed32": "1", "sfixed64": "1",
    "double": "1.0", "float": "1.0",
    "bool": "true",
    "string": "sample",
    "bytes": "sample",
}


def _load_proto_text(source: SourceLike) -> tuple[str, str]:
    if isinstance(source, dict):
        return str(source.get("proto", "")), source.get("file", "schema.proto")
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8"), str(source)
    if "\n" not in source and Path(source).is_file():
        p = Path(source)
        return p.read_text(encoding="utf-8"), str(p)
    return source, "schema.proto"


def _sample_value_for(type_name: str) -> str:
    return _SAMPLE_VALUES.get(type_name, "sample")


def _sample_fields_blob(message: MessageDef) -> str:
    pieces = []
    for f in message.fields:
        if f.type in SCALAR_TYPES:
            pieces.append(f"{f.name}:{f.type}={_sample_value_for(f.type)}")
    return ", ".join(pieces)


def _message_to_step(message: MessageDef, schema_file: str) -> ProtoStep:
    raw = _sample_fields_blob(message)
    return ProtoStep(
        name=message.name,
        schema_file=schema_file,
        message=message.name,
        fields={"_raw": raw} if raw else {},
        check="round_trip_equal",
        asserts=[Assertion(field=message.name, op="check", expected="round_trip_equal")],
    )


@dataclass
class ProtoSource(BaseSource):
    """`.proto` file or text → TestPlan with one round-trip step per message."""

    name: str = "proto"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".proto",))

    def load(self, source: SourceLike) -> TestPlan:
        text, filename = _load_proto_text(source)
        proto: ProtoFile = parse_proto(text)
        plan = TestPlan(metadata=ScenarioMetadata(
            name=proto.package or "Proto round-trip",
            type="proto",
            extra={"source": "proto", "syntax": proto.syntax},
        ))
        plan.fixtures.append(Fixture(
            name="proto.schemas",
            setup={"files": [filename]},
            scope="scenario",
        ))
        for message in proto.messages:
            plan.steps.append(_message_to_step(message, filename))
        return plan


__all__ = ["ProtoSource"]

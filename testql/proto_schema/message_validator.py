"""Validation of declared message instances against a `.proto` schema.

Operates entirely on the IR — no protobuf runtime required. Type-checks scalar
fields, ensures every declared field exists in the message, and provides a
deterministic round-trip helper that re-encodes scalar values to canonical form.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .descriptor_loader import FieldDef, MessageDef, ProtoFile, SCALAR_TYPES


@dataclass
class ValidationIssue:
    severity: str       # "error" | "warning"
    message: str
    field: Optional[str] = None


@dataclass
class ValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "issues": [{"severity": i.severity, "message": i.message, "field": i.field}
                       for i in self.issues],
        }


# ── Field-value parsing ─────────────────────────────────────────────────────

_INSTANCE_FIELD_RE = re.compile(
    r"\s*(?P<name>[A-Za-z_][\w]*)\s*:\s*(?P<type>[A-Za-z_][\w.]*)\s*=\s*(?P<value>[^,]+?)\s*(?:,|$)"
)


def parse_instance_fields(text: str) -> list[tuple[str, str, str]]:
    """Parse `name:type=value, name:type=value` into [(name, type, raw_value)].

    The format intentionally mirrors `MESSAGE[N]{name, fields}` rows in
    `.proto.testql.yaml`. Whitespace is permissive; values may be quoted.
    """
    if not text:
        return []
    out: list[tuple[str, str, str]] = []
    for m in _INSTANCE_FIELD_RE.finditer(text + ","):
        raw = m.group("value").strip()
        if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
            raw = raw[1:-1]
        out.append((m.group("name"), m.group("type"), raw))
    return out


def coerce_scalar(type_name: str, raw: Any) -> Any:
    """Parse a raw string value into the Python type expected for a proto scalar."""
    s = str(raw).strip()
    if type_name in {"bool"}:
        return s.lower() in {"1", "true", "yes", "on"}
    if type_name in {"int32", "int64", "uint32", "uint64",
                     "sint32", "sint64", "fixed32", "fixed64",
                     "sfixed32", "sfixed64"}:
        return int(s)
    if type_name in {"double", "float"}:
        return float(s)
    if type_name == "bytes":
        return s.encode("utf-8")
    return s


# ── Validation ──────────────────────────────────────────────────────────────


def _validate_field_known(name: str, message: MessageDef) -> Optional[ValidationIssue]:
    if message.field_by_name(name) is None:
        return ValidationIssue(severity="error",
                               message=f"unknown field {name!r} in {message.name}",
                               field=name)
    return None


def _validate_field_type(name: str, declared: str, message: MessageDef) -> Optional[ValidationIssue]:
    fd = message.field_by_name(name)
    if fd is None:
        return None
    if fd.type != declared:
        return ValidationIssue(
            severity="error",
            message=f"field {name!r} declared as {declared!r} but schema says {fd.type!r}",
            field=name,
        )
    return None


def _validate_field_value(name: str, declared: str, raw: Any) -> Optional[ValidationIssue]:
    if declared not in SCALAR_TYPES:
        return None
    try:
        coerce_scalar(declared, raw)
    except (ValueError, TypeError) as e:
        return ValidationIssue(severity="error",
                               message=f"field {name!r}: cannot coerce {raw!r} to {declared}: {e}",
                               field=name)
    return None


def validate_message_instance(
    message: MessageDef,
    instance: list[tuple[str, str, str]],
    *,
    require_all_required: bool = True,
) -> ValidationResult:
    """Cross-check an instance row against `message`'s field declarations."""
    result = ValidationResult()
    seen: set[str] = set()
    for name, declared, raw in instance:
        seen.add(name)
        for issue in _row_issues(name, declared, raw, message):
            result.issues.append(issue)
    if require_all_required:
        for missing in _missing_required(message, seen):
            result.issues.append(missing)
    return result


def _row_issues(name: str, declared: str, raw: str,
                message: MessageDef) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for check in (
        _validate_field_known(name, message),
        _validate_field_type(name, declared, message),
        _validate_field_value(name, declared, raw),
    ):
        if check is not None:
            issues.append(check)
    return issues


def _missing_required(message: MessageDef, seen: set[str]) -> list[ValidationIssue]:
    return [
        ValidationIssue(severity="error",
                        message=f"missing required field {f.name!r} in {message.name}",
                        field=f.name)
        for f in message.fields if f.label == "required" and f.name not in seen
    ]


# ── Round-trip ──────────────────────────────────────────────────────────────


def round_trip_equal(message: MessageDef,
                     instance: list[tuple[str, str, str]]) -> bool:
    """Return True iff coercing each field's value yields a stable (Python-equal)
    canonical form when coerced again — a structural round-trip check that
    works without an actual protobuf runtime.
    """
    for name, declared, raw in instance:
        if declared not in SCALAR_TYPES:
            continue
        try:
            once = coerce_scalar(declared, raw)
            twice = coerce_scalar(declared, once if isinstance(once, (int, float, bool)) else str(once))
        except (ValueError, TypeError):
            return False
        if once != twice:
            return False
    return True


def lookup_message(proto: ProtoFile, name: str) -> Optional[MessageDef]:
    return proto.message(name)


__all__ = [
    "ValidationIssue", "ValidationResult",
    "parse_instance_fields", "coerce_scalar",
    "validate_message_instance", "round_trip_equal", "lookup_message",
]

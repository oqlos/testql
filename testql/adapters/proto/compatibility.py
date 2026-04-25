"""Schema compatibility checks between two `ProtoFile` versions.

The rules implemented here mirror Google's documented proto compatibility
guidelines for proto3 evolution:

    * Removing a field is **breaking** unless the field is unused/reserved.
    * Adding a new field is safe (proto3 fields are optional by default).
    * Changing a field's tag number is breaking.
    * Changing a field's type is *usually* breaking — wire-compatible swaps
      (e.g. int32 ↔ uint32 ↔ bool) are allowed; everything else is breaking.
    * Renaming a field is safe on the wire (numbers identify fields), but is
      reported as a `warning` because it breaks JSON serialisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .descriptor_loader import FieldDef, MessageDef, ProtoFile


# Wire-compatible type substitutions (Google's compatibility table, simplified).
_WIRE_COMPAT_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"int32", "uint32", "int64", "uint64", "bool"}),
    frozenset({"sint32", "sint64"}),
    frozenset({"fixed32", "sfixed32"}),
    frozenset({"fixed64", "sfixed64"}),
    frozenset({"string", "bytes"}),
)


def _wire_compatible(a: str, b: str) -> bool:
    if a == b:
        return True
    return any(a in g and b in g for g in _WIRE_COMPAT_GROUPS)


@dataclass
class CompatibilityIssue:
    severity: str  # "breaking" | "warning" | "info"
    message: str
    message_name: Optional[str] = None
    field_name: Optional[str] = None
    code: Optional[str] = None


@dataclass
class CompatibilityReport:
    issues: list[CompatibilityIssue] = field(default_factory=list)

    @property
    def is_compatible(self) -> bool:
        return not any(i.severity == "breaking" for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "is_compatible": self.is_compatible,
            "issues": [vars(i) for i in self.issues],
        }


def _compare_field(old: FieldDef, new: Optional[FieldDef], message_name: str) -> list[CompatibilityIssue]:
    if new is None:
        return [CompatibilityIssue(
            severity="breaking",
            message=f"field {old.name!r} removed from {message_name}",
            message_name=message_name, field_name=old.name, code="field_removed",
        )]
    issues: list[CompatibilityIssue] = []
    if old.number != new.number:
        issues.append(CompatibilityIssue(
            severity="breaking",
            message=f"field {old.name!r}: tag number changed {old.number} → {new.number}",
            message_name=message_name, field_name=old.name, code="tag_changed",
        ))
    if not _wire_compatible(old.type, new.type):
        issues.append(CompatibilityIssue(
            severity="breaking",
            message=f"field {old.name!r}: incompatible type change {old.type} → {new.type}",
            message_name=message_name, field_name=old.name, code="type_changed",
        ))
    if old.name != new.name:
        issues.append(CompatibilityIssue(
            severity="warning",
            message=f"field tag {old.number}: name changed {old.name!r} → {new.name!r}",
            message_name=message_name, field_name=old.name, code="field_renamed",
        ))
    return issues


def _find_candidate_field(old_field: FieldDef, new_message: MessageDef) -> Optional[FieldDef]:
    """Find the new-side counterpart of `old_field`: prefer same number, else same name."""
    by_number = next((f for f in new_message.fields if f.number == old_field.number), None)
    if by_number is not None:
        return by_number
    return next((f for f in new_message.fields if f.name == old_field.name), None)


def _compare_message(old: MessageDef, new: MessageDef) -> list[CompatibilityIssue]:
    issues: list[CompatibilityIssue] = []
    for old_field in old.fields:
        candidate = _find_candidate_field(old_field, new)
        issues.extend(_compare_field(old_field, candidate, old.name))
    return issues


def _scan_old_messages(old: ProtoFile, new_messages: dict[str, MessageDef],
                       report: "CompatibilityReport") -> None:
    for old_message in old.messages:
        new_message = new_messages.get(old_message.name)
        if new_message is None:
            report.issues.append(CompatibilityIssue(
                severity="breaking",
                message=f"message {old_message.name!r} removed",
                message_name=old_message.name, code="message_removed",
            ))
            continue
        report.issues.extend(_compare_message(old_message, new_message))


def _scan_new_messages(old: ProtoFile, new: ProtoFile,
                       report: "CompatibilityReport") -> None:
    old_names = {m.name for m in old.messages}
    for new_message in new.messages:
        if new_message.name not in old_names:
            report.issues.append(CompatibilityIssue(
                severity="info",
                message=f"message {new_message.name!r} added",
                message_name=new_message.name, code="message_added",
            ))


def compare_schemas(old: ProtoFile, new: ProtoFile) -> CompatibilityReport:
    """Diff two `ProtoFile`s and return a `CompatibilityReport`."""
    report = CompatibilityReport()
    new_messages = {m.name: m for m in new.messages}
    _scan_old_messages(old, new_messages, report)
    _scan_new_messages(old, new, report)
    return report


__all__ = ["CompatibilityIssue", "CompatibilityReport", "compare_schemas"]

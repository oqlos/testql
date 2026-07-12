"""testql.proto_schema — dependency-free `.proto` schema utilities.

Regex-based descriptor parsing and IR-level message validation, used by the
core IR runner (`ProtoStep` executor), the meta coverage analyzer, and the
`proto2testql` plugin. Lives in core (not in the plugin) because executing
and analysing proto steps must work without the adapter installed.
"""

from __future__ import annotations

from .descriptor_loader import (
    SCALAR_TYPES,
    FieldDef,
    MessageDef,
    ProtoFile,
    load_proto_file,
    parse_proto,
)
from .message_validator import (
    ValidationIssue,
    ValidationResult,
    coerce_scalar,
    lookup_message,
    parse_instance_fields,
    round_trip_equal,
    validate_message_instance,
)

__all__ = [
    "SCALAR_TYPES", "FieldDef", "MessageDef", "ProtoFile",
    "parse_proto", "load_proto_file",
    "ValidationIssue", "ValidationResult",
    "parse_instance_fields", "coerce_scalar",
    "validate_message_instance", "round_trip_equal", "lookup_message",
]

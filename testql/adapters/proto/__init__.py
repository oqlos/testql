"""testql.adapters.proto — Protocol Buffers contract adapter (Phase 3).

Optional `protobuf` dependency: install via `pip install testql[proto]` for
binary serialisation. The adapter itself works without protobuf using a
regex-based `.proto` parser and IR-level validation/round-trip checks.
"""

from __future__ import annotations

from .compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    compare_schemas,
)
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
from .proto_adapter import ProtoDSLAdapter, parse, render


def has_protobuf() -> bool:
    """Return True iff the optional `protobuf` runtime is importable."""
    try:
        import google.protobuf  # noqa: F401
    except ImportError:
        return False
    return True


__all__ = [
    "ProtoDSLAdapter", "parse", "render",
    "SCALAR_TYPES", "FieldDef", "MessageDef", "ProtoFile",
    "parse_proto", "load_proto_file",
    "ValidationIssue", "ValidationResult",
    "parse_instance_fields", "coerce_scalar",
    "validate_message_instance", "round_trip_equal", "lookup_message",
    "CompatibilityIssue", "CompatibilityReport", "compare_schemas",
    "has_protobuf",
]

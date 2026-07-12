"""proto2testql — Protocol Buffers contract adapter plugin for TestQL.

Registers the `proto` DSL adapter via the `testql.plugins` entry point and
the `proto` generator source via the `testql.sources` entry point. Optional
`protobuf` dependency: install via `pip install proto2testql[protobuf]` for
binary serialisation — the adapter itself works without it using the
regex-based `.proto` parser from `testql.proto_schema`.
"""

from __future__ import annotations

from testql.proto_schema import (
    SCALAR_TYPES,
    FieldDef,
    MessageDef,
    ProtoFile,
    ValidationIssue,
    ValidationResult,
    coerce_scalar,
    load_proto_file,
    lookup_message,
    parse_instance_fields,
    parse_proto,
    round_trip_equal,
    validate_message_instance,
)

from .adapter import ProtoDSLAdapter, parse, render
from .compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    compare_schemas,
)


def has_protobuf() -> bool:
    """Return True iff the optional `protobuf` runtime is importable."""
    try:
        import google.protobuf  # noqa: F401
    except ImportError:
        return False
    return True


def register_testql_plugin(registry) -> None:
    """`testql.plugins` entry-point hook — see `AdapterRegistry.load_plugins`."""
    registry.register(ProtoDSLAdapter())


__all__ = [
    "ProtoDSLAdapter", "parse", "render",
    "SCALAR_TYPES", "FieldDef", "MessageDef", "ProtoFile",
    "parse_proto", "load_proto_file",
    "ValidationIssue", "ValidationResult",
    "parse_instance_fields", "coerce_scalar",
    "validate_message_instance", "round_trip_equal", "lookup_message",
    "CompatibilityIssue", "CompatibilityReport", "compare_schemas",
    "has_protobuf",
    "register_testql_plugin",
]

"""Tests for `testql.adapters.proto.message_validator`."""

from __future__ import annotations

from testql.adapters.proto.descriptor_loader import parse_proto
from testql.adapters.proto.message_validator import (
    coerce_scalar,
    parse_instance_fields,
    round_trip_equal,
    validate_message_instance,
)


PROTO = """\
syntax = "proto3";
message User {
    int64 id = 1;
    string email = 2;
    bool active = 3;
}
"""


class TestParseInstanceFields:
    def test_basic(self):
        out = parse_instance_fields("id:int64=1, email:string=foo@bar.com, active:bool=true")
        assert out == [("id", "int64", "1"),
                       ("email", "string", "foo@bar.com"),
                       ("active", "bool", "true")]

    def test_quoted_value(self):
        out = parse_instance_fields('email:string="user@example.com"')
        assert out == [("email", "string", "user@example.com")]

    def test_empty(self):
        assert parse_instance_fields("") == []
        assert parse_instance_fields(None) == []  # type: ignore[arg-type]


class TestCoerceScalar:
    def test_int(self):
        assert coerce_scalar("int64", "42") == 42
        assert coerce_scalar("uint32", "0") == 0

    def test_float(self):
        assert coerce_scalar("double", "1.5") == 1.5

    def test_bool(self):
        assert coerce_scalar("bool", "true") is True
        assert coerce_scalar("bool", "0") is False

    def test_string_passthrough(self):
        assert coerce_scalar("string", "hello") == "hello"

    def test_bytes(self):
        assert coerce_scalar("bytes", "abc") == b"abc"

    def test_unknown_type_returns_string(self):
        assert coerce_scalar("CustomType", "x") == "x"


class TestValidateMessageInstance:
    def test_ok(self):
        pf = parse_proto(PROTO)
        instance = parse_instance_fields("id:int64=1, email:string=user@x, active:bool=true")
        result = validate_message_instance(pf.message("User"), instance)
        assert result.ok
        assert result.issues == []

    def test_unknown_field(self):
        pf = parse_proto(PROTO)
        instance = parse_instance_fields("nope:int64=1")
        result = validate_message_instance(pf.message("User"), instance,
                                           require_all_required=False)
        assert not result.ok
        assert any("unknown" in i.message for i in result.issues)

    def test_type_mismatch(self):
        pf = parse_proto(PROTO)
        # Declares email as int64 instead of string.
        instance = [("email", "int64", "1")]
        result = validate_message_instance(pf.message("User"), instance,
                                           require_all_required=False)
        assert not result.ok

    def test_value_coercion_failure(self):
        pf = parse_proto(PROTO)
        instance = [("id", "int64", "not-a-number")]
        result = validate_message_instance(pf.message("User"), instance,
                                           require_all_required=False)
        assert not result.ok
        assert any("coerce" in i.message for i in result.issues)

    def test_required_missing(self):
        proto = "message X { required int64 id = 1; required string name = 2; }"
        pf = parse_proto(proto)
        instance = parse_instance_fields("id:int64=1")
        result = validate_message_instance(pf.message("X"), instance,
                                           require_all_required=True)
        assert not result.ok
        assert any("missing required" in i.message for i in result.issues)

    def test_to_dict(self):
        pf = parse_proto(PROTO)
        instance = parse_instance_fields("id:int64=1")
        result = validate_message_instance(pf.message("User"), instance,
                                           require_all_required=False)
        d = result.to_dict()
        assert "ok" in d
        assert "issues" in d


class TestRoundTrip:
    def test_clean_round_trip(self):
        pf = parse_proto(PROTO)
        instance = parse_instance_fields("id:int64=42, email:string=x, active:bool=true")
        assert round_trip_equal(pf.message("User"), instance) is True

    def test_round_trip_failure_on_invalid_value(self):
        pf = parse_proto(PROTO)
        instance = [("id", "int64", "not-a-number")]
        assert round_trip_equal(pf.message("User"), instance) is False

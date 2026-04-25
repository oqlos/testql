"""Tests for `testql.adapters.proto.descriptor_loader`."""

from __future__ import annotations

from pathlib import Path

from testql.adapters.proto.descriptor_loader import (
    SCALAR_TYPES,
    FieldDef,
    MessageDef,
    ProtoFile,
    load_proto_file,
    parse_proto,
)


SIMPLE = """\
syntax = "proto3";
package example.users;

// User contract
message User {
    int64 id = 1;
    string email = 2;
    bool active = 3;
}

message Order {
    int64 id = 1;
    int64 user_id = 2;
    double total = 3;
}
"""


WITH_LABELS_AND_DEFAULTS = """\
syntax = "proto2";

message Item {
    required int64 id = 1;
    optional string label = 2 [default = "n/a"];
    repeated string tags = 3;
}
"""


class TestParseHeader:
    def test_syntax(self):
        pf = parse_proto(SIMPLE)
        assert pf.syntax == "proto3"

    def test_package(self):
        pf = parse_proto(SIMPLE)
        assert pf.package == "example.users"

    def test_default_syntax(self):
        pf = parse_proto("message X {}")
        assert pf.syntax == "proto3"


class TestParseMessages:
    def test_two_messages(self):
        pf = parse_proto(SIMPLE)
        assert {m.name for m in pf.messages} == {"User", "Order"}

    def test_field_count(self):
        pf = parse_proto(SIMPLE)
        user = pf.message("User")
        assert user is not None
        assert len(user.fields) == 3

    def test_field_types(self):
        pf = parse_proto(SIMPLE)
        user = pf.message("User")
        types = {f.name: f.type for f in user.fields}
        assert types == {"id": "int64", "email": "string", "active": "bool"}

    def test_field_numbers_unique(self):
        pf = parse_proto(SIMPLE)
        user = pf.message("User")
        numbers = [f.number for f in user.fields]
        assert numbers == [1, 2, 3]


class TestLabelsAndDefaults:
    def test_required(self):
        pf = parse_proto(WITH_LABELS_AND_DEFAULTS)
        item = pf.message("Item")
        f = item.field_by_name("id")
        assert f.label == "required"

    def test_optional_with_default(self):
        pf = parse_proto(WITH_LABELS_AND_DEFAULTS)
        item = pf.message("Item")
        f = item.field_by_name("label")
        assert f.label == "optional"
        assert f.default is not None
        # Default may be quoted; both forms are acceptable.
        assert "n/a" in f.default

    def test_repeated(self):
        pf = parse_proto(WITH_LABELS_AND_DEFAULTS)
        item = pf.message("Item")
        f = item.field_by_name("tags")
        assert f.label == "repeated"


class TestComments:
    def test_line_comments_stripped(self):
        text = """\
syntax = "proto3";
// removed
message X {
    int64 id = 1; // inline
}
"""
        pf = parse_proto(text)
        assert pf.message("X") is not None

    def test_block_comments_stripped(self):
        text = """\
syntax = "proto3";
/* multi
   line */
message X {
    int64 id = 1;
}
"""
        pf = parse_proto(text)
        assert pf.message("X") is not None


class TestLookups:
    def test_field_by_name(self):
        pf = parse_proto(SIMPLE)
        f = pf.message("User").field_by_name("email")
        assert f is not None
        assert f.number == 2

    def test_field_by_number(self):
        pf = parse_proto(SIMPLE)
        f = pf.message("User").field_by_number(3)
        assert f.name == "active"

    def test_field_by_name_missing(self):
        pf = parse_proto(SIMPLE)
        assert pf.message("User").field_by_name("nope") is None

    def test_message_missing(self):
        pf = parse_proto(SIMPLE)
        assert pf.message("Nope") is None


class TestLoadProtoFile:
    def test_round_trip(self, tmp_path: Path):
        p = tmp_path / "user.proto"
        p.write_text(SIMPLE, encoding="utf-8")
        pf = load_proto_file(p)
        assert pf.message("User") is not None


class TestScalarTypes:
    def test_includes_canonical_proto_scalars(self):
        for t in ("int32", "int64", "uint32", "uint64", "string", "bool", "double", "float", "bytes"):
            assert t in SCALAR_TYPES


class TestToDict:
    def test_round_trip_shape(self):
        pf = parse_proto("syntax = \"proto3\"; message X { int64 id = 1; }")
        d = pf.to_dict()
        assert d["syntax"] == "proto3"
        assert d["messages"][0]["name"] == "X"
        assert d["messages"][0]["fields"][0]["name"] == "id"

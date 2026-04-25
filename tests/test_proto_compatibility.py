"""Tests for `testql.adapters.proto.compatibility`."""

from __future__ import annotations

from testql.adapters.proto.compatibility import (
    CompatibilityIssue,
    CompatibilityReport,
    compare_schemas,
)
from testql.adapters.proto.descriptor_loader import parse_proto


V1 = """\
syntax = "proto3";
message User {
    int64 id = 1;
    string email = 2;
    bool active = 3;
}
"""


class TestIdentitySchemas:
    def test_no_issues(self):
        old = parse_proto(V1)
        new = parse_proto(V1)
        report = compare_schemas(old, new)
        assert report.is_compatible
        assert all(i.severity != "breaking" for i in report.issues)


class TestRemovedField:
    def test_breaking(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 id = 1;
    string email = 2;
}
""")
        report = compare_schemas(old, new)
        assert not report.is_compatible
        codes = {i.code for i in report.issues}
        assert "field_removed" in codes


class TestAddedField:
    def test_safe(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 id = 1;
    string email = 2;
    bool active = 3;
    string nickname = 4;
}
""")
        report = compare_schemas(old, new)
        assert report.is_compatible


class TestTypeChange:
    def test_incompatible_breaking(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 id = 1;
    bytes email = 2;
    bool active = 3;
}
""")
        # string -> bytes is wire-compatible per the table (both length-delimited)
        report = compare_schemas(old, new)
        assert report.is_compatible

    def test_string_to_int_breaking(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 id = 1;
    int64 email = 2;
    bool active = 3;
}
""")
        report = compare_schemas(old, new)
        assert not report.is_compatible
        assert any(i.code == "type_changed" for i in report.issues)

    def test_int32_to_uint32_safe(self):
        old = parse_proto("syntax='proto3'; message X { int32 a = 1; }".replace("'", '"'))
        new = parse_proto("syntax='proto3'; message X { uint32 a = 1; }".replace("'", '"'))
        report = compare_schemas(old, new)
        assert report.is_compatible


class TestTagChange:
    def test_breaking(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 id = 5;
    string email = 2;
    bool active = 3;
}
""")
        report = compare_schemas(old, new)
        assert not report.is_compatible
        assert any(i.code == "tag_changed" for i in report.issues)


class TestRename:
    def test_rename_is_warning(self):
        old = parse_proto(V1)
        new = parse_proto("""\
syntax = "proto3";
message User {
    int64 user_id = 1;
    string email = 2;
    bool active = 3;
}
""")
        report = compare_schemas(old, new)
        # Rename alone is wire-compatible (number-based) but warning-level.
        assert report.is_compatible
        assert any(i.code == "field_renamed" for i in report.issues)


class TestRemovedMessage:
    def test_breaking(self):
        old = parse_proto(V1 + "\nmessage Order { int64 id = 1; }")
        new = parse_proto(V1)
        report = compare_schemas(old, new)
        assert not report.is_compatible
        assert any(i.code == "message_removed" for i in report.issues)


class TestAddedMessage:
    def test_info_only(self):
        old = parse_proto(V1)
        new = parse_proto(V1 + "\nmessage Order { int64 id = 1; }")
        report = compare_schemas(old, new)
        assert report.is_compatible
        assert any(i.code == "message_added" for i in report.issues)


class TestReportShape:
    def test_to_dict(self):
        report = CompatibilityReport(issues=[
            CompatibilityIssue(severity="info", message="x", code="x")
        ])
        d = report.to_dict()
        assert d["is_compatible"] is True
        assert d["issues"][0]["code"] == "x"

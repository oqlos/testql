"""Tests for the `proto2testql` generator source (.proto → TestPlan)."""

from __future__ import annotations

from proto2testql.source import ProtoSource
from testql.ir import ProtoStep


PROTO_TEXT = """\
syntax = "proto3";
package example;

message User {
    int64 id = 1;
    string email = 2;
}

message Order {
    int64 id = 1;
    double total = 2;
}
"""


class TestProtoSource:
    def test_one_step_per_message(self):
        plan = ProtoSource().load(PROTO_TEXT)
        steps = [s for s in plan.steps if isinstance(s, ProtoStep)]
        assert len(steps) == 2
        names = {s.name for s in steps}
        assert names == {"User", "Order"}

    def test_sample_fields_blob(self):
        plan = ProtoSource().load(PROTO_TEXT)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        assert "id:int64=" in user.fields["_raw"]
        assert "email:string=" in user.fields["_raw"]

    def test_round_trip_assertion(self):
        plan = ProtoSource().load(PROTO_TEXT)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        assert any(a.expected == "round_trip_equal" for a in user.asserts)

    def test_schema_fixture(self):
        plan = ProtoSource().load(PROTO_TEXT)
        assert any(f.name == "proto.schemas" for f in plan.fixtures)

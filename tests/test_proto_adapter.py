"""Tests for `testql.adapters.proto.proto_adapter`."""

from __future__ import annotations

from pathlib import Path

from testql.adapters.proto import ProtoDSLAdapter, parse, render
from testql.ir import ProtoStep, TestPlan


SAMPLE = """\
# SCENARIO: User proto contract
# TYPE: proto
# VERSION: 1.0

PROTO[1]{file}:
  schemas/user.proto

MESSAGE[2]{name, fields}:
  User, "id:int64=1, email:string=user@example.com, active:bool=true"
  Order, "id:int64=42, user_id:int64=1, total:double=99.99"

ASSERT[3]{name, check}:
  User, round_trip_equal
  User, all_required_present
  Order, round_trip_equal
"""


class TestDetect:
    def test_by_extension(self, tmp_path: Path):
        p = tmp_path / "x.proto.testql.yaml"
        p.write_text(SAMPLE, encoding="utf-8")
        result = ProtoDSLAdapter().detect(p)
        assert result.matches
        assert result.confidence >= 0.9

    def test_by_header(self):
        result = ProtoDSLAdapter().detect(SAMPLE)
        assert result.matches

    def test_negative(self):
        assert not ProtoDSLAdapter().detect("plain text\n").matches


class TestParseMetadata:
    def test_name_type_version(self):
        plan = parse(SAMPLE)
        assert plan.metadata.name == "User proto contract"
        assert plan.metadata.type == "proto"
        assert plan.metadata.version == "1.0"


class TestParseSchemas:
    def test_proto_files_become_fixture(self):
        plan = parse(SAMPLE)
        proto_fxs = [f for f in plan.fixtures if f.name == "proto.schemas"]
        assert len(proto_fxs) == 1
        assert proto_fxs[0].setup["files"] == ["schemas/user.proto"]


class TestParseMessages:
    def test_step_count(self):
        plan = parse(SAMPLE)
        proto_steps = [s for s in plan.steps if isinstance(s, ProtoStep)]
        assert len(proto_steps) == 2

    def test_message_names(self):
        plan = parse(SAMPLE)
        names = [s.name for s in plan.steps if isinstance(s, ProtoStep)]
        assert names == ["User", "Order"]

    def test_schema_file_propagated(self):
        plan = parse(SAMPLE)
        for s in plan.steps:
            if isinstance(s, ProtoStep):
                assert s.schema_file == "schemas/user.proto"

    def test_fields_blob_preserved(self):
        plan = parse(SAMPLE)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        assert "id:int64=1" in user.fields["_raw"]


class TestParseAsserts:
    def test_assertions_attach_to_message(self):
        plan = parse(SAMPLE)
        user = next(s for s in plan.steps if isinstance(s, ProtoStep) and s.name == "User")
        checks = [a.expected for a in user.asserts]
        assert "round_trip_equal" in checks
        assert "all_required_present" in checks

    def test_orphan_assert(self):
        plan = parse("""\
# SCENARIO: x
# TYPE: proto

ASSERT[1]{name, check}:
  Unknown, round_trip_equal
""")
        assert_steps = [s for s in plan.steps if s.kind == "assert"]
        assert assert_steps
        assert assert_steps[0].asserts[0].field == "Unknown"


class TestRender:
    def test_round_trip_step_count(self):
        plan = parse(SAMPLE)
        rendered = render(plan)
        plan2 = parse(rendered)
        n1 = sum(1 for s in plan.steps if isinstance(s, ProtoStep))
        n2 = sum(1 for s in plan2.steps if isinstance(s, ProtoStep))
        assert n1 == n2

    def test_render_includes_meta(self):
        plan = parse(SAMPLE)
        out = render(plan)
        assert "# TYPE: proto" in out
        assert "# VERSION: 1.0" in out


class TestRegistration:
    def test_registered(self):
        from testql.adapters import registry
        a = registry.get("proto")
        assert a is not None
        assert isinstance(a, ProtoDSLAdapter)

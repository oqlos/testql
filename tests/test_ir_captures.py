"""Tests for `testql.ir.captures.Capture` and step-level `captures` field."""

from __future__ import annotations

from testql.ir import ApiStep, Capture, SqlStep, Step


class TestCaptureDataclass:
    def test_minimal(self):
        c = Capture(var_name="device_id", from_path="data.id")
        assert c.var_name == "device_id"
        assert c.from_path == "data.id"

    def test_to_dict(self):
        c = Capture(var_name="x", from_path="rows.0.id")
        assert c.to_dict() == {"var_name": "x", "from_path": "rows.0.id"}


class TestStepCapturesField:
    def test_default_empty(self):
        assert Step().captures == []
        assert ApiStep().captures == []

    def test_attaches_to_api_step(self):
        step = ApiStep(
            method="POST", path="/x",
            captures=[Capture(var_name="id", from_path="data.id")],
        )
        assert len(step.captures) == 1
        assert step.captures[0].var_name == "id"

    def test_to_dict_omits_empty_captures(self):
        d = ApiStep(method="GET", path="/x").to_dict()
        assert "captures" not in d

    def test_to_dict_includes_populated_captures(self):
        d = ApiStep(
            method="POST", path="/x",
            captures=[Capture(var_name="id", from_path="data.id"),
                      Capture(var_name="name", from_path="data.name")],
        ).to_dict()
        assert d["captures"] == [
            {"var_name": "id", "from_path": "data.id"},
            {"var_name": "name", "from_path": "data.name"},
        ]

    def test_works_on_sql_step(self):
        step = SqlStep(query="SELECT id FROM u",
                       captures=[Capture(var_name="uid", from_path="rows.0.id")])
        assert step.to_dict()["captures"][0]["var_name"] == "uid"

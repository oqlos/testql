"""Regression tests for JSON-path navigation used by ASSERT_JSON / CAPTURE.

Pins the behaviour that broke between testql 0.2.0 and 1.2.x:
indexed paths like ``results[0].id`` must descend into the list at
``results`` and then read the ``id`` field of element 0.

Covers both the pure helper ``_navigate_json_path`` and the behavioural
contract on ``IqlInterpreter`` for ``ASSERT_JSON`` and ``CAPTURE``.
"""

from __future__ import annotations

from testql.interpreter import IqlInterpreter
from testql.interpreter._api_runner import _navigate_json_path


SAMPLE_RESPONSE = {
    "results": [
        {"id": "abc-1", "title": "Identification: JAN_TEST_42"},
        {"id": "abc-2", "title": "Identification: other"},
    ],
    "total_count": 2,
    "data": {"items": [{"name": "first"}, {"name": "second"}]},
}


class TestNavigateJsonPath:
    def test_indexed_first_element_field(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "results[0].id") == "abc-1"

    def test_indexed_second_element_field(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "results[1].id") == "abc-2"

    def test_indexed_nested_field(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "data.items[1].name") == "second"

    def test_top_level_scalar(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "total_count") == 2

    def test_missing_key_returns_none(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "results[0].missing") is None

    def test_out_of_range_index_returns_none(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "results[99].id") is None

    def test_length_of_list(self):
        assert _navigate_json_path(SAMPLE_RESPONSE, "results.length") == 2


class TestAssertJsonAndCaptureWithIndexedPath:
    """Behavioural regression: ASSERT_JSON / CAPTURE must support results[0].id."""

    def _make_interp(self) -> IqlInterpreter:
        interp = IqlInterpreter(dry_run=True, quiet=True)
        # Simulate a previous API response without doing real HTTP.
        interp.last_response = SAMPLE_RESPONSE
        interp.last_status = 200
        return interp

    def test_assert_json_indexed_path_passes(self):
        interp = self._make_interp()
        result = interp.run('ASSERT_JSON results[0].id == "abc-1"', "regress.tql")
        assert result.ok, result.errors
        assert result.passed >= 1
        assert result.failed == 0

    def test_assert_json_indexed_path_fails_on_mismatch(self):
        interp = self._make_interp()
        result = interp.run('ASSERT_JSON results[0].id == "wrong"', "regress.tql")
        assert not result.ok
        assert result.failed >= 1

    def test_capture_indexed_path_stores_value(self):
        interp = self._make_interp()
        result = interp.run(
            'CAPTURE first_id FROM "results[0].id"',
            "regress.tql",
        )
        assert result.ok, result.errors
        assert result.variables.get("first_id") == "abc-1"

    def test_assert_json_total_count_ge(self):
        interp = self._make_interp()
        result = interp.run("ASSERT_JSON total_count >= 1", "regress.tql")
        assert result.ok, result.errors
        assert result.passed >= 1

    def test_assert_json_results_length_ge(self):
        interp = self._make_interp()
        result = interp.run("ASSERT_JSON results.length >= 1", "regress.tql")
        assert result.ok, result.errors
        assert result.passed >= 1


class TestToonBareImperativeIndexedPath:
    """End-to-end: TestTOON parser -> COMMANDS -> IqlScript -> ASSERT_JSON / CAPTURE.

    Note: We invoke commands directly because dry-run API responses would
    override last_response. This still tests the full path through the
    parser + command execution.
    """

    TOON_SOURCE = """\
# SCENARIO: Regress indexed path
# TYPE: api

CONFIG[1]{key, value}:
  api_url, http://localhost:8101

API POST /identify {"type": "user"}
ASSERT_STATUS 200
ASSERT_JSON results[0].id == "abc-1"
CAPTURE captured_id FROM "results[0].id"
ASSERT_JSON results.length >= 1
"""

    def _make_interp(self):
        from testql.interpreter import IqlInterpreter

        interp = IqlInterpreter(dry_run=True, quiet=True)
        interp.last_response = {
            "results": [
                {"id": "abc-1", "title": "Identification: JAN_TEST_42"},
            ],
            "total_count": 1,
        }
        interp.last_status = 200
        return interp

    def test_toon_parser_parses_bare_commands(self):
        from testql.interpreter._testtoon_parser import testtoon_to_iql

        script = testtoon_to_iql(self.TOON_SOURCE, "regress.testql.toon.yaml")
        # Verify the parser collected bare commands into COMMANDS section
        assert any(cmd.command == "API" for cmd in script.lines)
        assert any(cmd.command == "ASSERT_STATUS" for cmd in script.lines)
        assert any(cmd.command == "ASSERT_JSON" for cmd in script.lines)
        assert any(cmd.command == "CAPTURE" for cmd in script.lines)

    def test_toon_assert_json_indexed_passes(self):
        interp = self._make_interp()
        from testql.interpreter._parser import IqlLine

        # Simulate the ASSERT_JSON command that would come from parsed TOON
        line = IqlLine(number=4, command="ASSERT_JSON", args='results[0].id == "abc-1"', raw='ASSERT_JSON results[0].id == "abc-1"')
        interp._cmd_assert_json(line.args, line)

        assert interp.results[-1].status.value == "passed"
        assert interp.errors == []

    def test_toon_capture_stores_value(self):
        interp = self._make_interp()
        from testql.interpreter._parser import IqlLine

        # Simulate the CAPTURE command that would come from parsed TOON
        line = IqlLine(number=5, command="CAPTURE", args='captured_id FROM "results[0].id"', raw='CAPTURE captured_id FROM "results[0].id"')
        interp._cmd_capture(line.args, line)

        assert interp.vars.get("captured_id") == "abc-1"
        assert interp.results[-1].status.value == "passed"

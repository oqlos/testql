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

"""Tests for interpreter/converter/handlers/api.py and assertions.py."""
import pytest

from testql.interpreter.converter.handlers.api import handle_api
from testql.interpreter.converter.handlers.assertions import collect_assert


class TestCollectAssert:
    def test_no_assert(self):
        filtered = [("NAVIGATE", "http://x")]
        j, status, key, value = collect_assert(filtered, 0)
        assert j == 0 and status == 200 and key is None and value is None

    def test_assert_status(self):
        filtered = [("ASSERT_STATUS", "404")]
        j, status, key, value = collect_assert(filtered, 0)
        assert j == 1 and status == 404 and key is None

    def test_assert_status_invalid_defaults_200(self):
        filtered = [("ASSERT_STATUS", "bad")]
        j, status, _, _ = collect_assert(filtered, 0)
        assert status == 200 and j == 1

    def test_assert_ok(self):
        filtered = [("ASSERT_OK", "")]
        j, status, _, _ = collect_assert(filtered, 0)
        assert status == 200 and j == 1

    def test_assert_json_three_parts(self):
        filtered = [("ASSERT_JSON", 'data.name == "Alice"')]
        j, status, key, value = collect_assert(filtered, 0)
        assert j == 1 and key == "data.name" and value == "Alice"

    def test_assert_contains_one_part(self):
        filtered = [("ASSERT_CONTAINS", "status")]
        j, status, key, value = collect_assert(filtered, 0)
        assert key == "status" and value == "-"

    def test_multiple_asserts(self):
        filtered = [("ASSERT_STATUS", "201"), ("ASSERT_JSON", 'id == "123"')]
        j, status, key, value = collect_assert(filtered, 0)
        assert j == 2 and status == 201 and key == "id"

    def test_stops_at_non_assert(self):
        filtered = [("ASSERT_STATUS", "200"), ("NAVIGATE", "http://x")]
        j, _, _, _ = collect_assert(filtered, 0)
        assert j == 1

    def test_empty(self):
        j, status, key, value = collect_assert([], 0)
        assert j == 0 and status == 200 and key is None


class TestHandleApi:
    def test_simple_get(self):
        filtered = [("API", "GET /users")]
        i, section = handle_api(filtered, 0)
        assert i == 1
        assert section.type == "API"
        assert section.rows[0]["method"] == "GET"
        assert section.rows[0]["endpoint"] == "/users"
        assert section.rows[0]["status"] == "200"

    def test_post_with_assert_status(self):
        filtered = [("API", "POST /items"), ("ASSERT_STATUS", "201")]
        i, section = handle_api(filtered, 0)
        assert i == 2
        assert section.rows[0]["status"] == "201"

    def test_with_assert_json(self):
        filtered = [("API", "GET /users"), ("ASSERT_JSON", 'data.id == "1"')]
        _, section = handle_api(filtered, 0)
        assert "assert_key" in section.columns
        assert section.rows[0]["assert_key"] == "data.id"

    def test_multiple_api_calls(self):
        filtered = [("API", "GET /a"), ("API", "GET /b")]
        i, section = handle_api(filtered, 0)
        assert i == 2 and len(section.rows) == 2

    def test_stops_at_non_api(self):
        filtered = [("API", "GET /a"), ("NAVIGATE", "http://x")]
        i, section = handle_api(filtered, 0)
        assert i == 1 and len(section.rows) == 1

    def test_columns_without_assert(self):
        filtered = [("API", "GET /x")]
        _, section = handle_api(filtered, 0)
        assert "assert_key" not in section.columns

"""Basic tests for TestQL interpreter — IQL and TestTOON formats."""

from __future__ import annotations

from testql.interpreter import (
    IqlInterpreter,
    parse_iql,
    parse_testtoon,
    validate_testtoon,
)
from testql.interpreter._testtoon_parser import testtoon_to_iql as _testtoon_to_iql


class TestParseIql:
    def test_empty(self):
        script = parse_iql("")
        assert script.lines == []

    def test_comments_ignored(self):
        script = parse_iql("# comment\n\n# another")
        assert script.lines == []

    def test_basic_commands(self):
        source = 'SET api_url "http://localhost"\nLOG "hello"\nWAIT 500'
        script = parse_iql(source)
        assert len(script.lines) == 3
        assert script.lines[0].command == "SET"
        assert script.lines[1].command == "LOG"
        assert script.lines[2].command == "WAIT"


class TestParseTestTOON:
    def test_empty(self):
        result = parse_testtoon("")
        assert result.sections == []

    def test_meta(self):
        source = "# SCENARIO: Test\n# TYPE: api\n# VERSION: 1.0"
        result = parse_testtoon(source)
        assert result.meta["scenario"] == "Test"
        assert result.meta["type"] == "api"
        assert result.meta["version"] == "1.0"

    def test_api_section(self):
        source = (
            "# SCENARIO: Smoke\n"
            "# TYPE: api\n"
            "API[2]{method, endpoint, status}:\n"
            "  GET,  /api/v3/health,  200\n"
            "  GET,  /api/v3/devices, 200\n"
        )
        result = parse_testtoon(source)
        assert len(result.sections) == 1
        assert result.sections[0].type == "API"
        assert len(result.sections[0].rows) == 2
        assert result.sections[0].rows[0]["method"] == "GET"
        assert result.sections[0].rows[0]["endpoint"] == "/api/v3/health"
        assert result.sections[0].rows[0]["status"] == 200

    def test_encoder_section(self):
        source = (
            "ENCODER[3]{action, target, value, wait_ms}:\n"
            "  on,  -,  -,  300\n"
            "  focus,  col1,  -,  200\n"
            "  scroll,  -,  1,  150\n"
        )
        result = parse_testtoon(source)
        assert len(result.sections) == 1
        sec = result.sections[0]
        assert sec.type == "ENCODER"
        assert len(sec.rows) == 3
        assert sec.rows[0]["action"] == "on"
        assert sec.rows[1]["target"] == "col1"
        assert sec.rows[2]["value"] == 1
        assert sec.rows[2]["wait_ms"] == 150

    def test_validation_pass(self):
        source = "API[2]{method, endpoint}:\n  GET,  /a\n  GET,  /b\n"
        result = parse_testtoon(source)
        assert validate_testtoon(result) == []

    def test_validation_fail(self):
        source = "API[3]{method, endpoint}:\n  GET,  /a\n  GET,  /b\n"
        result = parse_testtoon(source)
        errors = validate_testtoon(result)
        assert len(errors) == 1
        assert "declared 3" in errors[0]


class TestTestTOONExpansion:
    def test_api_expansion(self):
        source = (
            "API[2]{method, endpoint, status}:\n"
            "  GET,  /health,  200\n"
            "  POST, /devices, 201\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert len(script.lines) == 4  # 2 API + 2 ASSERT_STATUS
        assert script.lines[0].command == "API"
        assert script.lines[1].command == "ASSERT_STATUS"
        assert "200" in script.lines[1].args
        assert script.lines[2].command == "API"
        assert script.lines[3].command == "ASSERT_STATUS"
        assert "201" in script.lines[3].args

    def test_encoder_expansion(self):
        source = (
            "ENCODER[2]{action, target, value, wait_ms}:\n"
            "  on,  -,  -,  300\n"
            "  scroll,  -,  1,  150\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert script.lines[0].command == "ENCODER_ON"
        assert script.lines[1].command == "WAIT"
        assert script.lines[1].args == "300"
        assert script.lines[2].command == "ENCODER_SCROLL"
        assert script.lines[2].args == "1"
        assert script.lines[3].command == "WAIT"
        assert script.lines[3].args == "150"

    def test_config_expansion(self):
        source = (
            "CONFIG[1]{key, value}:\n"
            "  api_url,  http://localhost:8101\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert len(script.lines) == 1
        assert script.lines[0].command == "SET"

    def test_config_mapping_expansion(self):
        source = (
            "CONFIG:\n"
            "  api_url: http://localhost:8101\n"
            "  encoder_url: http://localhost:8100\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert [(line.command, line.args) for line in script.lines] == [
            ("SET", 'api_url "http://localhost:8101"'),
            ("SET", 'encoder_url "http://localhost:8100"'),
        ]

    def test_config_mapping_applies_to_encoder_flow(self):
        source = (
            "CONFIG:\n"
            "  encoder_url: http://localhost:8100\n"
            "  encoder_endpoint_prefix: /dashboard/action\n"
            "ENCODER[1]{action, target, value, wait_ms}:\n"
            "  status, -, -, -\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert script.lines[0].command == "SET"
        assert script.lines[0].args == 'encoder_url "http://localhost:8100"'
        assert script.lines[1].command == "SET"
        assert script.lines[1].args == 'encoder_endpoint_prefix "/dashboard/action"'
        assert script.lines[2].command == "ENCODER_STATUS"

    def test_navigate_expansion(self):
        source = (
            "NAVIGATE[2]{path, wait_ms}:\n"
            "  /connect-test,  500\n"
            "  /connect-id,    300\n"
        )
        script = _testtoon_to_iql(source, "test.testql.toon.yaml")
        assert len(script.lines) == 4  # 2 NAVIGATE + 2 WAIT
        assert script.lines[0].command == "NAVIGATE"
        assert script.lines[1].command == "WAIT"
        assert script.lines[1].args == "500"


class TestIqlInterpreter:
    def test_dry_run_api(self):
        source = (
            'SET api_url "http://localhost:8101"\n'
            'API GET "/health"\n'
            "ASSERT_STATUS 200\n"
        )
        interp = IqlInterpreter(dry_run=True, quiet=True)
        result = interp.run(source, "test.tql")
        assert result.ok
        assert result.passed >= 1

    def test_set_get(self):
        source = 'SET foo "bar"\nGET foo'
        interp = IqlInterpreter(dry_run=True, quiet=True)
        result = interp.run(source, "test.tql")
        assert result.ok
        assert result.variables.get("foo") == "bar"

    def test_testtoon_dry_run(self):
        source = (
            "# SCENARIO: Dry Run Test\n"
            "# TYPE: api\n"
            "API[1]{method, endpoint, status}:\n"
            '  GET,  /health,  200\n'
        )
        interp = IqlInterpreter(dry_run=True, quiet=True)
        result = interp.run(source, "test.testql.toon.yaml")
        assert result.ok
        assert result.passed >= 1

    def test_assert_json_nested_virtual_encoder_status_path(self):
        interp = IqlInterpreter(dry_run=True, quiet=True)
        interp.vars.set("_encoder_status", {"active": False, "error": "no_response"})

        result = interp.run(
            'ASSERT_JSON _encoder_status.error == "no_response"',
            "encoder-assert.tql",
        )

        assert result.ok, result.errors
        assert result.failed == 0

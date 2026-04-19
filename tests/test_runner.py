"""Tests for testql/runner.py DSL parser and executor."""
import pytest
from unittest.mock import MagicMock, patch

from testql.runner import (
    DslCommand,
    ExecutionResult,
    parse_line,
    parse_script,
    DslCliExecutor,
)


class TestDslCommand:
    def test_create_minimal(self):
        cmd = DslCommand(type="API", target="/users")
        assert cmd.type == "API"
        assert cmd.target == "/users"
        assert cmd.params is None
        assert cmd.expected is None
        assert cmd.comment is None

    def test_create_full(self):
        cmd = DslCommand("CLICK", "#btn", {"id": 1}, "success", "click button")
        assert cmd.params == {"id": 1}
        assert cmd.comment == "click button"


class TestExecutionResult:
    def test_success(self):
        cmd = DslCommand("API", "/x")
        r = ExecutionResult(True, cmd, {"ok": True}, None, 50)
        assert r.success is True
        assert r.duration_ms == 50

    def test_failure(self):
        cmd = DslCommand("API", "/x")
        r = ExecutionResult(False, cmd, None, "conn refused", 10)
        assert r.success is False
        assert r.error == "conn refused"


class TestParseLine:
    def test_empty_returns_none(self):
        assert parse_line("") is None

    def test_comment_returns_none(self):
        assert parse_line("# this is a comment") is None

    def test_blank_line_returns_none(self):
        assert parse_line("   ") is None

    def test_api_get(self):
        cmd = parse_line('API GET "/users"')
        assert cmd is not None
        assert cmd.type == "API"
        assert cmd.target == "/users"
        assert cmd.params["method"] == "GET"

    def test_api_post_with_body(self):
        cmd = parse_line('API POST "/users" {"name": "alice"}')
        assert cmd is not None
        assert cmd.params["method"] == "POST"
        assert cmd.params["name"] == "alice"

    def test_api_with_expected(self):
        cmd = parse_line('API GET "/ping" -> success')
        assert cmd is not None
        assert cmd.expected == "success"

    def test_api_with_comment(self):
        cmd = parse_line('API GET "/health" # health check')
        assert cmd is not None
        assert cmd.comment == "health check"

    def test_wait_command(self):
        cmd = parse_line("WAIT 500")
        assert cmd is not None
        assert cmd.type == "WAIT"
        assert cmd.target == "500"

    def test_wait_with_comment(self):
        cmd = parse_line("WAIT 1000 # wait a sec")
        assert cmd is not None
        assert cmd.comment == "wait a sec"

    def test_general_command_with_quotes(self):
        cmd = parse_line('NAVIGATE "/dashboard"')
        assert cmd is not None
        assert cmd.type == "NAVIGATE"
        assert cmd.target == "/dashboard"

    def test_simple_command(self):
        cmd = parse_line("CLICK submit-button")
        assert cmd is not None
        assert cmd.type == "CLICK"
        assert cmd.target == "submit-button"

    def test_api_patch(self):
        cmd = parse_line('API PATCH "/items/1"')
        assert cmd is not None
        assert cmd.params["method"] == "PATCH"

    def test_api_delete(self):
        cmd = parse_line('API DELETE "/items/1"')
        assert cmd is not None
        assert cmd.params["method"] == "DELETE"


class TestParseScript:
    def test_empty_script(self):
        assert parse_script("") == []

    def test_comments_and_blanks_skipped(self):
        result = parse_script("# comment\n\n# another")
        assert result == []

    def test_multiline_script(self):
        script = 'API GET "/a"\nAPI POST "/b"\nWAIT 100'
        result = parse_script(script)
        assert len(result) == 3
        assert result[0].target == "/a"
        assert result[1].target == "/b"
        assert result[2].type == "WAIT"

    def test_mixed_content(self):
        script = "# start\nAPI GET \"/ping\"\n# done\n"
        result = parse_script(script)
        assert len(result) == 1
        assert result[0].target == "/ping"


class TestDslCliExecutor:
    def test_init_defaults(self):
        ex = DslCliExecutor()
        assert ex.base_url == "http://localhost:8000"
        assert ex.verbose is False

    def test_init_custom_url(self):
        ex = DslCliExecutor("http://myserver:9000/")
        assert ex.base_url == "http://myserver:9000"  # trailing slash stripped

    def test_browser_command_skipped(self):
        ex = DslCliExecutor()
        cmd = DslCommand("NAVIGATE", "/home")
        result = ex.execute(cmd)
        assert result.success is True
        assert result.result.get("skipped") is True

    def test_semantic_command_logged(self):
        ex = DslCliExecutor()
        cmd = DslCommand("APP_START", "myapp")
        result = ex.execute(cmd)
        assert result.success is True
        assert result.result.get("logged") is True

    def test_browser_command_verbose(self, capsys):
        ex = DslCliExecutor(verbose=True)
        cmd = DslCommand("CLICK", "#btn")
        result = ex.execute(cmd)
        captured = capsys.readouterr()
        assert result.result.get("skipped") is True

    def test_semantic_command_verbose(self, capsys):
        ex = DslCliExecutor(verbose=True)
        cmd = DslCommand("SESSION_START", "session1")
        result = ex.execute(cmd)
        assert result.result.get("logged") is True

    def test_execute_unknown_command_returns_result(self):
        ex = DslCliExecutor()
        cmd = DslCommand("UNKNOWN_XYZ", "target")
        result = ex.execute(cmd)
        # Either succeeds or fails gracefully
        assert isinstance(result, ExecutionResult)

    def test_execute_returns_duration(self):
        ex = DslCliExecutor()
        cmd = DslCommand("NAVIGATE", "/")
        result = ex.execute(cmd)
        assert result.duration_ms >= 0

    def test_wait_command_via_execute(self):
        ex = DslCliExecutor()
        cmd = DslCommand("WAIT", "10")
        result = ex.execute(cmd)
        assert isinstance(result, ExecutionResult)

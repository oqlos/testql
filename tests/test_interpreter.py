"""Basic tests for TestQL interpreter."""

from __future__ import annotations

from testql.base import StepStatus
from testql.interpreter import IqlInterpreter, parse_iql


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

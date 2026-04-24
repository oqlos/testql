"""Tests for CommandDispatcher (testql.interpreter.dispatcher)."""

from __future__ import annotations

import pytest

from testql.interpreter import IqlInterpreter
from testql.interpreter.dispatcher import CommandDispatcher


class TestCommandDispatcher:
    """Test CommandDispatcher functionality."""

    @pytest.fixture
    def interpreter(self):
        """Create IqlInterpreter instance."""
        return IqlInterpreter(api_url="http://localhost:8101", quiet=True)

    @pytest.fixture
    def dispatcher(self, interpreter):
        """Create CommandDispatcher instance."""
        return CommandDispatcher(interpreter)

    def test_auto_discovery(self, dispatcher):
        """Test auto-discovery of _cmd_* methods."""
        commands = dispatcher.list_commands()
        assert len(commands) > 20  # Should have many commands from all mixins
        assert "set" in commands
        assert "get" in commands
        assert "api" in commands
        assert "shell" in commands
        assert "wait" in commands

    def test_has_command(self, dispatcher):
        """Test has_command method."""
        assert dispatcher.has_command("set")
        assert dispatcher.has_command("SET")  # Case-insensitive
        assert dispatcher.has_command("shell")
        assert not dispatcher.has_command("nonexistent")

    def test_dispatch_known_command(self, dispatcher, interpreter):
        """Test dispatching a known command."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SET", args="key value", raw="SET key value")
        result = dispatcher.dispatch("SET", "key value", line)

        assert result is True
        assert interpreter.vars.get("key") == "value"

    def test_dispatch_unknown_command(self, dispatcher, interpreter):
        """Test dispatching an unknown command."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="UNKNOWN", args="", raw="UNKNOWN")
        result = dispatcher.dispatch("UNKNOWN", "", line)

        assert result is False
        # Should have warning in output
        assert any("Unknown command" in line for line in interpreter.out.lines)

    def test_dispatch_with_suggestion(self, dispatcher, interpreter):
        """Test dispatching unknown command with suggestion."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SIT", args="", raw="SIT")
        result = dispatcher.dispatch("SIT", "", line)

        assert result is False
        # Should suggest "SET" as similar command
        assert any("Did you mean" in line for line in interpreter.out.lines)

    def test_register_custom_command(self, dispatcher, interpreter):
        """Test registering a custom command."""
        def custom_handler(args: str, line):
            interpreter.out.step("🔧", f"CUSTOM: {args}")

        dispatcher.register("custom", custom_handler)
        assert dispatcher.has_command("custom")

        from testql.interpreter._parser import IqlLine
        line = IqlLine(number=1, command="CUSTOM", args="test", raw="CUSTOM test")
        result = dispatcher.dispatch("CUSTOM", "test", line)

        assert result is True
        assert any("CUSTOM: test" in line for line in interpreter.out.lines)

    def test_case_insensitive_dispatch(self, dispatcher):
        """Test that dispatch is case-insensitive."""
        assert dispatcher.has_command("set")
        assert dispatcher.has_command("SET")
        assert dispatcher.has_command("SeT")


class TestDispatcherIntegration:
    """Test CommandDispatcher integration with IqlInterpreter."""

    @pytest.fixture
    def interpreter(self):
        """Create IqlInterpreter with dispatcher."""
        return IqlInterpreter(api_url="http://localhost:8101", quiet=True)

    def test_interpreter_uses_dispatcher(self, interpreter):
        """Test that IqlInterpreter uses CommandDispatcher."""
        assert hasattr(interpreter, "dispatcher")
        assert isinstance(interpreter.dispatcher, CommandDispatcher)

    def test_dispatch_through_interpreter(self, interpreter):
        """Test dispatching through interpreter's _dispatch method."""
        from testql.interpreter._parser import IqlLine

        line = IqlLine(number=1, command="SET", args="test_key test_value", raw="SET test_key test_value")
        interpreter._dispatch("SET", "test_key test_value", line)

        assert interpreter.vars.get("test_key") == "test_value"

    def test_all_mixin_commands_discovered(self, interpreter):
        """Test that all mixin commands are discovered."""
        commands = interpreter.dispatcher.list_commands()

        # Shell commands
        assert "shell" in commands
        assert "assert_exit_code" in commands

        # Unit commands
        assert "unit_import" in commands
        assert "unit_pytest" in commands

        # GUI commands
        assert "gui_start" in commands
        assert "gui_click" in commands

        # API commands
        assert "api" in commands
        assert "capture" in commands

        # Flow commands
        assert "wait" in commands
        assert "log" in commands

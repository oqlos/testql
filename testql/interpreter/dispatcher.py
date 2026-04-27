"""Command dispatcher for OqlInterpreter — central command routing with auto-discovery."""

from __future__ import annotations

from typing import Callable, Any
from difflib import get_close_matches

from ._parser import OqlLine


class CommandDispatcher:
    """Central command dispatcher with auto-discovery and better error messages."""

    def __init__(self, interpreter: Any):
        """Initialize dispatcher with interpreter instance.

        Args:
            interpreter: OqlInterpreter instance containing mixin handlers
        """
        self.interpreter = interpreter
        self._handlers: dict[str, Callable] = {}
        self._discover_handlers()

    def _discover_handlers(self) -> None:
        """Auto-discover all _cmd_* methods from interpreter's mixins."""
        # Scan all attributes of the interpreter
        for attr_name in dir(self.interpreter):
            if attr_name.startswith("_cmd_"):
                cmd_name = attr_name[5:]  # Remove "_cmd_" prefix
                self._handlers[cmd_name] = getattr(self.interpreter, attr_name)

    def register(self, cmd_name: str, handler: Callable) -> None:
        """Register a custom command handler.

        Args:
            cmd_name: Command name (without _cmd_ prefix)
            handler: Handler function with signature (args: str, line: OqlLine) -> None
        """
        self._handlers[cmd_name.lower()] = handler

    def dispatch(self, cmd: str, args: str, line: OqlLine) -> bool:
        """Dispatch command to registered handler.

        Args:
            cmd: Command name (case-insensitive)
            args: Command arguments
            line: OqlLine with line number and raw content

        Returns:
            True if handler was found and executed, False otherwise
        """
        cmd_lower = cmd.lower()
        handler = self._handlers.get(cmd_lower)

        if handler:
            try:
                handler(args, line)
                return True
            except Exception as e:
                self.interpreter.out.fail(f"Handler error for {cmd}: {e}")
                self.interpreter.errors.append(f"L{line.number}: {cmd} handler error: {e}")
                self.interpreter.results.append(
                    self.interpreter.results.__class__.__name__,
                    name=f"{cmd} handler",
                    status=self.interpreter.results.__class__.__name__,
                    message=str(e),
                ) if hasattr(self.interpreter, 'results') else None
                return True  # Handler found but failed

        # Command not found - suggest similar commands
        suggestions = get_close_matches(cmd_lower, self._handlers.keys(), n=3)
        if suggestions:
            suggestion = f"Did you mean: {', '.join(suggestions)}?"
            self.interpreter.out.warn(f"Unknown command: {cmd}. {suggestion}")
        else:
            self.interpreter.out.warn(f"Unknown command: {cmd}")

        return False

    def list_commands(self) -> list[str]:
        """Return list of all registered commands."""
        return sorted(self._handlers.keys())

    def has_command(self, cmd: str) -> bool:
        """Check if command is registered."""
        return cmd.lower() in self._handlers

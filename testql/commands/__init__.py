"""TestQL commands package with lazy loading to reduce startup fan-out."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from click import Command

# Registry of command paths for lazy loading
_COMMAND_REGISTRY: dict[str, tuple[str, str]] = {
    # module_name: (package_path, object_name)
    "discover": ("testql.commands.discover_cmd", "discover"),
    "topology": ("testql.commands.topology_cmd", "topology"),
    "inspect": ("testql.commands.inspect_cmd", "inspect"),
    "echo": ("testql.commands.echo", "echo"),
    "cli_echo": ("testql.commands.misc_cmds", "echo"),
    "endpoints": ("testql.commands.endpoints_cmd", "endpoints"),
    "openapi": ("testql.commands.endpoints_cmd", "openapi"),
    "analyze": ("testql.commands.generate_cmd", "analyze"),
    "generate": ("testql.commands.generate_cmd", "generate"),
    "generate_topology": ("testql.commands.generate_topology_cmd", "generate_topology"),
    "create": ("testql.commands.misc_cmds", "create"),
    "from_sumd": ("testql.commands.misc_cmds", "from_sumd"),
    "init": ("testql.commands.misc_cmds", "init"),
    "report": ("testql.commands.misc_cmds", "report"),
    "watch": ("testql.commands.misc_cmds", "watch"),
    "run": ("testql.commands.run_cmd", "run"),
    "list_tests": ("testql.commands.suite_cmd", "list_tests"),
    "suite": ("testql.commands.suite_cmd", "suite"),
}

__all__ = list(_COMMAND_REGISTRY.keys())


def __getattr__(name: str) -> Command:
    """Lazy-load command modules on first access."""
    if name not in _COMMAND_REGISTRY:
        raise AttributeError(f"module 'testql.commands' has no attribute '{name}'")
    module_path, obj_name = _COMMAND_REGISTRY[name]
    module = importlib.import_module(module_path)
    return getattr(module, obj_name)

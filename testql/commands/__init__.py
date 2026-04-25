"""TestQL commands package."""

from testql.commands.discover_cmd import discover
from testql.commands.echo import echo
from testql.commands.endpoints_cmd import endpoints, openapi
from testql.commands.generate_cmd import analyze, generate
from testql.commands.inspect_cmd import inspect
from testql.commands.misc_cmds import create
from testql.commands.misc_cmds import echo as cli_echo
from testql.commands.misc_cmds import from_sumd, init, report, watch
from testql.commands.run_cmd import run
from testql.commands.suite_cmd import list_tests, suite
from testql.commands.topology_cmd import topology

__all__ = [
    "discover",
    "topology",
    "inspect",
    "echo",
    "cli_echo",
    "endpoints",
    "openapi",
    "analyze",
    "generate",
    "create",
    "from_sumd",
    "init",
    "report",
    "watch",
    "run",
    "list_tests",
    "suite",
]

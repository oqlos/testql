"""TestQL commands package."""

from testql.commands.echo import echo
from testql.commands.endpoints_cmd import endpoints, openapi
from testql.commands.generate_cmd import analyze, generate
from testql.commands.misc_cmds import create
from testql.commands.misc_cmds import echo as cli_echo
from testql.commands.misc_cmds import from_sumd, init, report, watch
from testql.commands.run_cmd import run
from testql.commands.suite_cmd import list_tests, suite

__all__ = [
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

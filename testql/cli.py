"""TestQL CLI — run .testql.toon.yaml scenarios from the command line."""

from __future__ import annotations

import click

from testql.commands.discover_cmd import discover
from testql.commands.endpoints_cmd import endpoints, openapi
from testql.commands.generate_cmd import analyze, generate
from testql.commands.generate_ir_cmd import generate_ir
from testql.commands.generate_topology_cmd import generate_topology
from testql.commands.inspect_cmd import inspect
from testql.commands.misc_cmds import create, echo, from_sumd, init, report, watch
from testql.commands.run_cmd import run
from testql.commands.run_ir_cmd import run_ir
from testql.commands.self_test_cmd import self_test
from testql.commands.suite_cmd import list_tests, suite
from testql.commands.topology_cmd import topology


@click.group()
@click.version_option(version="0.2.0")
def cli():
    """TestQL — Interface Query Language for Testing."""
    pass


cli.add_command(run)
cli.add_command(run_ir)
cli.add_command(generate)
cli.add_command(generate_topology)
cli.add_command(generate_ir)
cli.add_command(discover)
cli.add_command(topology)
cli.add_command(inspect)
cli.add_command(analyze)
cli.add_command(endpoints)
cli.add_command(openapi)
cli.add_command(suite)
cli.add_command(list_tests, name="list")
cli.add_command(init)
cli.add_command(create)
cli.add_command(watch)
cli.add_command(from_sumd)
cli.add_command(report)
cli.add_command(echo)
cli.add_command(self_test)

def main():
    """Entry point for console script."""
    cli()


if __name__ == "__main__":
    main()

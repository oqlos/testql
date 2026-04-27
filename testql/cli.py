"""TestQL CLI — run .testql.toon.yaml scenarios from the command line."""

from __future__ import annotations

import sys

import click
import httpx
from importlib.metadata import version as pkg_version

from testql.commands.auto_cmd import auto
from testql.commands.discover_cmd import discover
from testql.commands.endpoints_cmd import endpoints, openapi
from testql.commands.generate_cmd import analyze, generate
from testql.commands.generate_from_page_cmd import generate_from_page
from testql.commands.generate_ir_cmd import generate_ir
from testql.commands.generate_topology_cmd import generate_topology
from testql.commands.heal_scenario_cmd import heal_scenario
from testql.commands.inspect_cmd import inspect
from testql.commands.misc_cmds import create, echo, from_sumd, init, report, watch
from testql.commands.run_cmd import run
from testql.commands.run_ir_cmd import run_ir
from testql.commands.self_test_cmd import self_test
from testql.commands.suite_cmd import list_tests, suite
from testql.commands.topology_cmd import topology


@click.command(name="mcp")
def mcp_serve():
    """Start TestQL MCP stdio server for Windsurf / VS Code / JetBrains."""
    try:
        from testql.mcp.server import run_server
        run_server()
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc


@click.group()
@click.version_option(version=pkg_version("testql"))
def cli():
    """TestQL — Interface Query Language for Testing."""
    pass


cli.add_command(auto)
cli.add_command(run)
cli.add_command(run_ir)
cli.add_command(generate)
cli.add_command(generate_from_page)
cli.add_command(generate_topology)
cli.add_command(generate_ir)
cli.add_command(heal_scenario)
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
cli.add_command(mcp_serve)


def _fetch_latest_version() -> str | None:
    try:
        response = httpx.get("https://pypi.org/pypi/testql/json", timeout=2.0)
        response.raise_for_status()
        return response.json()["info"]["version"]
    except Exception:
        return None


def check_and_upgrade():
    """Print version hint to stderr if outdated. Never prompts or blocks."""
    try:
        current_version = pkg_version("testql")
    except Exception:
        return
    latest = _fetch_latest_version()
    if latest and latest != current_version:
        print(
            f"TestQL v{current_version} (latest: v{latest})"
            " — run: pip install --upgrade testql",
            file=sys.stderr,
        )


def main():
    """Entry point for console script."""
    check_and_upgrade()
    cli()


if __name__ == "__main__":
    main()

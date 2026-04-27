"""TestQL CLI — run .testql.toon.yaml scenarios from the command line."""

from __future__ import annotations

import os
import subprocess
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


def check_and_upgrade():
    """Check for updates and auto-upgrade if available (similar to goal)."""
    try:
        current_version = pkg_version("testql")
    except Exception:
        current_version = "unknown"

    try:
        # Check PyPI for latest version
        response = httpx.get("https://pypi.org/pypi/testql/json", timeout=2.0)
        response.raise_for_status()
        latest_version = response.json()["info"]["version"]

        # Display version info
        if current_version == latest_version:
            print(f"TestQL v{current_version} ✓")
        else:
            print(f"TestQL v{current_version} (latest: v{latest_version})")
            if not sys.stdin.isatty():
                print("Non-interactive mode — skipping auto-update. Run manually to update.")
                return

            response = input("Auto-update to latest version? [Y/n] ").strip().lower()

            if response in ('', 'y', 'yes'):
                print(f"🔄 Auto-updating testql from v{current_version} to v{latest_version}...")

                # Auto-upgrade using pip
                try:
                    # Use the same pip that installed testql
                    pip_executable = sys.executable.replace("python", "pip")
                    subprocess.run(
                        [pip_executable, "install", "--upgrade", "testql"],
                        check=True,
                        capture_output=True,
                    )
                    print(f"✅ Successfully updated to v{latest_version}")

                    # Restart the process with the new version
                    print("🔄 Restarting testql with new version...")
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Failed to auto-upgrade: {e}")
                    print("Run: pip install --upgrade testql")
                except Exception as e:
                    print(f"⚠️  Failed to restart: {e}")
            else:
                print("Skipping update.")
    except httpx.RequestError:
        # Network error - just show current version
        print(f"TestQL v{current_version}")
    except Exception:
        # Any other error - just show current version
        print(f"TestQL v{current_version}")


def main():
    """Entry point for console script."""
    check_and_upgrade()
    cli()


if __name__ == "__main__":
    main()

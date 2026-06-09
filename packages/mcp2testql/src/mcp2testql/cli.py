"""CLI entry for mcp2testql MCP server."""

from __future__ import annotations

import argparse
import sys

from mcp2testql.server import create_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcp2testql",
        description="Run TestQL control MCP server (stdio)",
    )
    parser.add_argument("--name", default="testql", help="MCP server name")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("serve", help="Run MCP stdio server (default)")
    sub.add_parser("server", help="Alias for serve")

    args = parser.parse_args(argv or sys.argv[1:])
    cmd = args.cmd or "serve"
    if cmd in {"serve", "server"}:
        create_server(name=args.name).run()
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

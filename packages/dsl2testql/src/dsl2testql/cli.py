"""CLI for TestQL control DSL supporting dual-mode (legacy & subcommands)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2testql.bus import execute_dsl, execute_dsl_line
from dsl2testql.cli_handlers import (
    cmd_decode,
    cmd_encode,
    cmd_exec,
    cmd_replay,
    cmd_run,
    cmd_shell,
    cmd_validate_schema,
)

_SUBCOMMANDS = {"shell", "exec", "run", "validate-schema", "encode", "decode", "replay"}


def _main_legacy(args_list: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="dsl2testql",
        description="Control TestQL manifests via DSL commands (QUERY, PATCH, VALIDATE, ...)",
    )
    parser.add_argument("script", nargs="?", help="Optional .dsl script file")
    parser.add_argument("-c", "--command", help="Execute single DSL command")
    parser.add_argument("--file", help="Default app.testql.less path for block URIs")
    parser.add_argument("--json", action="store_true", help="Print JSON results")
    args = parser.parse_args(args_list)

    if args.command:
        results = [execute_dsl_line(args.command, default_file=args.file)]
    elif args.script:
        text = Path(args.script).read_text(encoding="utf-8")
        results = execute_dsl(text, default_file=args.file)
    else:
        text = sys.stdin.read()
        if not text.strip():
            parser.print_help()
            return 1
        results = execute_dsl(text, default_file=args.file)

    exit_code = 0
    for result in results:
        if args.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            if result.error:
                print(f"error: {result.error}", file=sys.stderr)
            if result.output:
                print(result.output.rstrip())
        if not result.ok:
            exit_code = 1
    return exit_code


_SUBCOMMAND_HANDLERS = {
    "validate-schema": cmd_validate_schema,
    "exec": cmd_exec,
    "run": cmd_run,
    "encode": cmd_encode,
    "decode": cmd_decode,
    "replay": cmd_replay,
    "shell": cmd_shell,
}


def _main_subcommands(args_list: list[str]) -> int:
    sub = args_list[0]
    rest = args_list[1:]
    handler = _SUBCOMMAND_HANDLERS.get(sub)
    if handler is None:
        return 1
    return handler(rest)


def main(argv: list[str] | None = None) -> int:
    args_list = argv or sys.argv[1:]
    if args_list and args_list[0] in _SUBCOMMANDS:
        return _main_subcommands(args_list)
    return _main_legacy(args_list)


if __name__ == "__main__":
    raise SystemExit(main())

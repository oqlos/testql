"""Command handlers for cli2testql."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2testql.engine import execute_dsl, execute_dsl_line


def print_result(result, *, json_out: bool) -> None:
    if json_out:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    if result.error:
        print(f"error: {result.error}", file=sys.stderr)
    if result.output:
        print(result.output.rstrip())


def cmd_run_script(args: argparse.Namespace) -> int:
    text = Path(args.script).read_text(encoding="utf-8")
    exit_code = 0
    for result in execute_dsl(text, default_file=args.file):
        print_result(result, json_out=args.json)
        if not result.ok:
            exit_code = 1
    return exit_code


def cmd_exec_line(args: argparse.Namespace) -> int:
    result = execute_dsl_line(args.command, default_file=args.file)
    print_result(result, json_out=args.json)
    return 0 if result.ok else 1


def run_shell_loop(*, default_file: str | None = None, json_out: bool = False) -> int:
    print("cli2testql shell — TestQL control DSL (exit/quit to leave)")
    exit_code = 0
    while True:
        try:
            line = input("testql> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in {"exit", "quit", ":q"}:
            break
        result = execute_dsl_line(line, default_file=default_file)
        print_result(result, json_out=json_out)
        if not result.ok:
            exit_code = 1
    return exit_code

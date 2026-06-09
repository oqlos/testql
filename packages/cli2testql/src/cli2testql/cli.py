"""Interactive CLI shell for TestQL control DSL."""

from __future__ import annotations

import argparse
import sys

from cli2testql.cli_handlers import cmd_exec_line, cmd_run_script, print_result, run_shell_loop


def run_shell(*, default_file: str | None = None, json_out: bool = False) -> int:
    return run_shell_loop(default_file=default_file, json_out=json_out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cli2testql",
        description="Interactive shell for TestQL control DSL (via dsl2testql)",
    )
    sub = parser.add_subparsers(dest="cmd")

    shell = sub.add_parser("shell", help="Interactive REPL")
    shell.add_argument("--file", help="Default app.testql.less path")
    shell.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="Run a .dsl script file")
    run.add_argument("script", help="DSL script path")
    run.add_argument("--file", help="Default app.testql.less path")
    run.add_argument("--json", action="store_true")

    one = sub.add_parser("exec", help="Execute one DSL command")
    one.add_argument("command", help="DSL command, e.g. QUERY testql://block/app")
    one.add_argument("--file", help="Default app.testql.less path")
    one.add_argument("--json", action="store_true")

    args = parser.parse_args(argv or sys.argv[1:])
    cmd = args.cmd or "shell"

    if cmd == "shell":
        return run_shell(default_file=args.file, json_out=args.json)
    if cmd == "run":
        return cmd_run_script(args)
    if cmd == "exec":
        return cmd_exec_line(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

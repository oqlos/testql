"""Subcommand handlers for dsl2testql CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dsl2testql.bus import execute_dsl, execute_dsl_line
from dsl2testql.events import default_event_store
from dsl2testql.pb_codec import decode_protobuf_to_text, encode_text_to_protobuf
from dsl2testql.schema_registry import validate_schema_registry


def _print_result(result, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return
    if result.error:
        print(f"error: {result.error}", file=sys.stderr)
    if result.output:
        print(result.output.rstrip())


def cmd_validate_schema(_rest: list[str]) -> int:
    errors = validate_schema_registry()
    if errors:
        for err in errors:
            print(f"Schema mismatch error: {err}", file=sys.stderr)
        return 1
    print("Schema registry is valid.")
    return 0


def cmd_exec(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql exec")
    parser.add_argument("cmd_line", help="DSL command line to execute")
    parser.add_argument("--file", help="Default app.testql.less path")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(rest)
    result = execute_dsl_line(args.cmd_line, default_file=args.file)
    _print_result(result, as_json=args.json)
    return 0 if result.ok else 1


def cmd_run(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql run")
    parser.add_argument("script", help="DSL script file path")
    parser.add_argument("--file", help="Default app.testql.less path")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(rest)
    text = Path(args.script).read_text(encoding="utf-8")
    exit_code = 0
    for result in execute_dsl(text, default_file=args.file):
        _print_result(result, as_json=args.json)
        if not result.ok:
            exit_code = 1
    return exit_code


def cmd_encode(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql encode")
    parser.add_argument("cmd_line", help="DSL command line to encode")
    parser.add_argument("--format", choices=["protobuf"], default="protobuf")
    parser.add_argument("--file", help="Default manifest file")
    args = parser.parse_args(rest)
    pb_bytes = encode_text_to_protobuf(args.cmd_line, default_file=args.file or "")
    sys.stdout.buffer.write(pb_bytes)
    return 0


def cmd_decode(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql decode")
    parser.add_argument("--input", help="Path to protobuf command file (defaults to stdin)")
    parser.add_argument("--format", choices=["protobuf"], default="protobuf")
    args = parser.parse_args(rest)
    data = Path(args.input).read_bytes() if args.input else sys.stdin.buffer.read()
    print(decode_protobuf_to_text(data))
    return 0


def cmd_replay(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql replay")
    parser.add_argument("--file", default="app.testql.less", help="Manifest file name")
    args = parser.parse_args(rest)
    store = default_event_store(args.file)
    for ev in store.replay():
        print(f"[{ev.ts_unix}] {ev.id}: {ev.command.get('verb')} -> ok={ev.result.get('ok')}")
    return 0


def cmd_shell(rest: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="dsl2testql shell")
    parser.add_argument("--file", default="app.testql.less", help="Default manifest file")
    args = parser.parse_args(rest)
    print("TestQL DSL Interactive Shell. Type EXIT or CTRL-D to quit.")
    while True:
        try:
            line = input("testql> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break
        if not line:
            continue
        if line.upper() in {"EXIT", "QUIT"}:
            break
        res = execute_dsl_line(line, default_file=args.file)
        if res.error:
            print(f"Error: {res.error}", file=sys.stderr)
        if res.output:
            print(res.output)
    return 0

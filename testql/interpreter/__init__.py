"""
testql.interpreter — package re-export for backward compatibility.

All original public symbols remain importable from `testql.interpreter`:
  from testql.interpreter import OqlInterpreter
  from testql.interpreter import OqlLine, OqlScript, parse_oql
  from testql.interpreter import main
"""

from __future__ import annotations

from .interpreter import OqlInterpreter
from ._parser import OqlLine, OqlScript, parse_oql
from ._testtoon_parser import (
    ToonScript,
    ToonSection,
    parse_testtoon,
    testtoon_to_oql,
    validate_testtoon,
)
from .testtoon_models import ToonScript, ToonSection
from .testtoon_parser import parse_testtoon
from ._converter import convert_oql_to_testtoon

__all__ = [
    "OqlInterpreter",
    "OqlLine",
    "OqlScript",
    "parse_oql",
    "ToonScript",
    "ToonSection",
    "parse_testtoon",
    "testtoon_to_oql",
    "validate_testtoon",
    "convert_oql_to_testtoon",
    "main",
]


def main() -> None:
    """CLI entry point — unchanged from original."""
    import json
    import argparse
    from pathlib import Path
    from typing import Any

    parser = argparse.ArgumentParser(description="TestQL Interpreter — runs .testql.toon.yaml scenarios")
    parser.add_argument("file", nargs="?", help="TestQL scenario file (.testql.toon.yaml / .oql / .tql)")
    parser.add_argument("-u", "--url", default="http://localhost:8101")
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-n", "--dry-run", action="store_true")
    parser.add_argument("-v", "--var", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-c", "--command", help="Execute single command")
    args = parser.parse_args()

    variables: dict[str, Any] = {}
    for v in args.var:
        if "=" in v:
            k, val = v.split("=", 1)
            variables[k.strip()] = val.strip()

    interp = OqlInterpreter(
        api_url=args.url, variables=variables,
        quiet=args.quiet, dry_run=args.dry_run,
    )

    if args.command:
        result = interp.run(args.command, filename="<command>")
    elif args.file:
        file_dir = str(Path(args.file).parent.resolve())
        interp.include_paths = [file_dir, "."]
        result = interp.run_file(args.file)
    else:
        parser.print_help()
        return

    if args.json:
        print(json.dumps({
            "source": result.source,
            "ok": result.ok,
            "passed": result.passed,
            "failed": result.failed,
            "total": len(result.steps),
            "duration_ms": round(result.duration_ms, 1),
            "errors": result.errors,
            "warnings": result.warnings,
            "variables": {k: str(v) for k, v in result.variables.items()},
        }, indent=2, ensure_ascii=False))

    raise SystemExit(0 if result.ok else 1)

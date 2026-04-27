"""
testql.interpreter — backward-compatibility shim.

This module has been refactored into a sub-package:
  testql/testql/interpreter/
    __init__.py    — public API + main()
    interpreter.py — OqlInterpreter class
    _parser.py     — OqlLine, OqlScript, parse_oql
    _api_runner.py — API commands + CAPTURE
    _assertions.py — ASSERT_* commands
    _encoder.py    — ENCODER_* commands
    _flow.py       — WAIT, LOG, INCLUDE, events

All symbols remain importable from this path:
  from testql.interpreter import OqlInterpreter
  from testql.interpreter import parse_oql, main
"""

# ruff: noqa: F401
from testql.interpreter.interpreter import OqlInterpreter  # noqa: F401
from testql.interpreter._parser import OqlLine, OqlScript, parse_oql  # noqa: F401
from testql.interpreter import main  # noqa: F401

__all__ = ["OqlInterpreter", "OqlLine", "OqlScript", "parse_oql", "main"]

if __name__ == "__main__":
    main()

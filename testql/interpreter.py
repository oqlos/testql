"""
testql.interpreter — backward-compatibility shim.

This module has been refactored into a sub-package:
  testql/testql/interpreter/
    __init__.py    — public API + main()
    interpreter.py — IqlInterpreter class
    _parser.py     — IqlLine, IqlScript, parse_iql
    _api_runner.py — API commands + CAPTURE
    _assertions.py — ASSERT_* commands
    _encoder.py    — ENCODER_* commands
    _flow.py       — WAIT, LOG, INCLUDE, events

All symbols remain importable from this path:
  from testql.interpreter import IqlInterpreter
  from testql.interpreter import parse_iql, main
"""

# ruff: noqa: F401
from testql.interpreter.interpreter import IqlInterpreter  # noqa: F401
from testql.interpreter._parser import IqlLine, IqlScript, parse_iql  # noqa: F401
from testql.interpreter import main  # noqa: F401

__all__ = ["IqlInterpreter", "IqlLine", "IqlScript", "parse_iql", "main"]

if __name__ == "__main__":
    main()

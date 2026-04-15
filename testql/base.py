"""
testql/base.py — Bridge to oqlos.core.base (authoritative source).

Falls back to a bundled copy if oqlos is not installed,
so testql stays usable as a standalone package.
"""

try:
    from oqlos.core.base import (  # noqa: F401
        BaseInterpreter,
        EventBridge,
        InterpreterOutput,
        ScriptResult,
        StepResult,
        StepStatus,
        VariableStore,
    )
except ImportError:  # oqlos not installed — use bundled fallback
    from testql._base_fallback import (  # noqa: F401
        BaseInterpreter,
        EventBridge,
        InterpreterOutput,
        ScriptResult,
        StepResult,
        StepStatus,
        VariableStore,
    )

__all__ = [
    "BaseInterpreter",
    "EventBridge",
    "InterpreterOutput",
    "ScriptResult",
    "StepResult",
    "StepStatus",
    "VariableStore",
]

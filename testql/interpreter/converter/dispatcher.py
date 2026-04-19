"""Command dispatcher for IQL/TQL converter.

Uses a registry pattern to dispatch commands to their handlers.
"""

from __future__ import annotations

from typing import Callable

from .models import Section
from .handlers import (
    handle_api,
    handle_encoder,
    handle_flow,
    FLOW_COMMANDS,
    handle_include,
    handle_navigate,
    handle_record_start,
    handle_record_stop,
    handle_select,
    handle_wait,
    handle_unknown,
)

# Handler registry: command predicate -> handler function
HandlerFunc = Callable[[list, int], tuple[int, Section]]

_REGISTRY: list[tuple[Callable[[str], bool], HandlerFunc]] = [
    (lambda cmd: cmd == 'API', handle_api),
    (lambda cmd: cmd == 'NAVIGATE', handle_navigate),
    (lambda cmd: cmd.startswith('ENCODER_'), handle_encoder),
    (lambda cmd: cmd.startswith('SELECT'), handle_select),
    (lambda cmd: cmd in FLOW_COMMANDS, handle_flow),
    (lambda cmd: cmd == 'RECORD_START', handle_record_start),
    (lambda cmd: cmd == 'RECORD_STOP', handle_record_stop),
    (lambda cmd: cmd == 'WAIT', handle_wait),
    (lambda cmd: cmd == 'INCLUDE', handle_include),
]


def dispatch(filtered: list, i: int) -> tuple[int, Section]:
    """Dispatch one command to its handler using registry; return (new_i, section)."""
    cmd = filtered[i][0]

    for predicate, handler in _REGISTRY:
        if predicate(cmd):
            return handler(filtered, i)

    return handle_unknown(filtered, i)

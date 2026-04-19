"""FLOW command handler."""

from ..models import Section
from ..parsers import parse_target_from_args, parse_meta_from_args

# Flow (semantic lifecycle) commands
FLOW_COMMANDS: frozenset[str] = frozenset({
    'START_TEST', 'PROTOCOL_CREATED', 'PROTOCOL_FINALIZE',
    'STEP_COMPLETE', 'SESSION_START', 'SESSION_END',
    'APP_START', 'APP_INIT', 'APP_READY', 'APP_ERROR',
    'MODULE_LOAD', 'MODULE_READY', 'MODULE_ERROR',
    'PAGE_SETUP', 'PAGE_ERROR', 'PAGE_RENDER',
    'REPORT_AUTOOPEN', 'REPORT_FETCH', 'REPORT_OPEN',
    'REPORT_ERROR', 'REPORT_PRINT', 'REPORT_LIST',
    'PROTOCOL_FETCH', 'PROTOCOL_LOAD', 'PROTOCOL_PARSE',
    'PROTOCOL_NORMALIZE', 'PROTOCOL_FILTER', 'PROTOCOL_ERROR',
    'TEST_RUN_PARAMS', 'OPEN_INTERVAL_DIALOG', 'EMIT',
})


def handle_flow(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive FLOW (semantic lifecycle) commands."""
    flow_rows: list[dict] = []

    while i < len(filtered) and filtered[i][0] in FLOW_COMMANDS:
        cmd, args = filtered[i]
        flow_rows.append({
            'command': cmd.lower(),
            'target': parse_target_from_args(args),
            'meta': parse_meta_from_args(args),
        })
        i += 1

    return i, Section(
        type='FLOW',
        columns=['command', 'target', 'meta'],
        rows=flow_rows,
        comment='Kroki semantyczne',
    )

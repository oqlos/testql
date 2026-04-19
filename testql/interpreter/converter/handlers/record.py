"""RECORD_START/STOP command handler."""

from ..models import Section
from ..parsers import parse_target_from_args


def handle_record_start(filtered: list, i: int) -> tuple[int, Section]:
    """Handle RECORD_START command."""
    _, args = filtered[i]
    return i + 1, Section(
        type='RECORD_START',
        columns=['session_id'],
        rows=[{'session_id': parse_target_from_args(args)}],
        comment='Nagrywanie sesji',
    )


def handle_record_stop(filtered: list, i: int) -> tuple[int, Section]:
    """Handle RECORD_STOP command."""
    return i + 1, Section(
        type='RECORD_STOP',
        columns=[],
        rows=[{}],
    )

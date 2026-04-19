"""SELECT* command handler."""

from ..models import Section
from ..parsers import parse_target_from_args, parse_meta_from_args


def handle_select(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive SELECT* rows."""
    sel_rows: list[dict] = []

    while i < len(filtered) and filtered[i][0].startswith('SELECT'):
        cmd, args = filtered[i]
        action = cmd.replace('SELECT_', '').lower()
        sel_rows.append({
            'action': action,
            'id': parse_target_from_args(args),
            'meta': parse_meta_from_args(args),
        })
        i += 1

    return i, Section(
        type='SELECT',
        columns=['action', 'id', 'meta'],
        rows=sel_rows,
        comment='Wybory domenowe',
    )

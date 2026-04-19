"""NAVIGATE command handler."""

from ..models import Section
from ..parsers import parse_target_from_args


def handle_navigate(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive NAVIGATE (+ optional WAIT) rows."""
    nav_rows: list[dict] = []

    while i < len(filtered) and filtered[i][0] == 'NAVIGATE':
        _, args = filtered[i]
        path = parse_target_from_args(args)
        wait_ms = 300

        if i + 1 < len(filtered) and filtered[i + 1][0] == 'WAIT':
            try:
                wait_ms = int(filtered[i + 1][1].strip())
            except ValueError:
                pass
            i += 2
        else:
            i += 1

        nav_rows.append({'path': path, 'wait_ms': str(wait_ms)})

    return i, Section(
        type='NAVIGATE',
        columns=['path', 'wait_ms'],
        rows=nav_rows,
        comment='Nawigacja UI'
    )

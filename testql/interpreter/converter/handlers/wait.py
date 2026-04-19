"""WAIT command handler."""

from ..models import Section


def handle_wait(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive standalone WAIT rows."""
    wait_rows: list[dict] = []

    while i < len(filtered) and filtered[i][0] == 'WAIT':
        try:
            ms = int(filtered[i][1].strip())
        except ValueError:
            ms = 100
        wait_rows.append({'ms': str(ms)})
        i += 1

    return i, Section(
        type='WAIT',
        columns=['ms'],
        rows=wait_rows,
    )

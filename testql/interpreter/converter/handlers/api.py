"""API command handler."""

from ..models import Section
from ..parsers import parse_api_args
from .assertions import collect_assert


def handle_api(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive API + ASSERT* rows into one API Section."""
    api_rows: list[dict] = []
    has_assert_key = False

    while i < len(filtered) and filtered[i][0] == 'API':
        cmd, args = filtered[i]
        method, endpoint = parse_api_args(args)
        j, status, assert_key, assert_value = collect_assert(filtered, i + 1)

        row: dict = {'method': method, 'endpoint': endpoint, 'status': str(status)}
        if assert_key:
            row['assert_key'] = assert_key
            row['assert_value'] = assert_value or '-'
            has_assert_key = True

        api_rows.append(row)
        i = j

    cols = ['method', 'endpoint', 'status']
    if has_assert_key:
        cols.extend(['assert_key', 'assert_value'])

    return i, Section(type='API', columns=cols, rows=api_rows, comment='Wywołania API')

"""Assertion collection helper for API handlers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..models import Section


def collect_assert(filtered: list, j: int) -> tuple[int, int, str | None, str | None]:
    """Scan ahead past ASSERT* commands; return (new_j, status, key, value)."""
    status = 200
    assert_key = None
    assert_value = None

    while j < len(filtered) and filtered[j][0].startswith('ASSERT'):
        acmd, aargs = filtered[j]
        if acmd == 'ASSERT_STATUS':
            try:
                status = int(aargs.strip())
            except ValueError:
                status = 200
        elif acmd == 'ASSERT_OK':
            status = 200
        elif acmd in ('ASSERT_JSON', 'ASSERT_CONTAINS'):
            parts = aargs.strip().split(None, 2)
            if len(parts) >= 3:
                assert_key = parts[0]
                assert_value = parts[2].strip('"\'')
            elif len(parts) >= 1:
                assert_key = parts[0]
                assert_value = '-'
        j += 1

    return j, status, assert_key, assert_value

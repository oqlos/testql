"""INCLUDE command handler."""

from ..models import Section
from ..parsers import parse_target_from_args


def handle_include(filtered: list, i: int) -> tuple[int, Section]:
    """Handle INCLUDE command."""
    _, args = filtered[i]
    return i + 1, Section(
        type='INCLUDE',
        columns=['file'],
        rows=[{'file': parse_target_from_args(args)}],
    )

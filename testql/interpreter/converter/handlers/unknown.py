"""Unknown command handler (fallback)."""

from ..models import Section
from ..parsers import parse_target_from_args, parse_meta_from_args


def handle_unknown(filtered: list, i: int) -> tuple[int, Section]:
    """Handle unknown commands as generic FLOW entries."""
    cmd, args = filtered[i]
    return i + 1, Section(
        type='FLOW',
        columns=['command', 'target', 'meta'],
        rows=[{
            'command': cmd.lower(),
            'target': parse_target_from_args(args) if args else '-',
            'meta': parse_meta_from_args(args) if args else '-',
        }],
    )

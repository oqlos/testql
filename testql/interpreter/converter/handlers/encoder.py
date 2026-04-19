"""ENCODER_* command handler."""

from ..models import Section
from ..parsers import parse_target_from_args


def handle_encoder(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive ENCODER_* (+ optional WAIT) rows."""
    enc_rows: list[dict] = []

    while i < len(filtered) and filtered[i][0].startswith('ENCODER_'):
        cmd, args = filtered[i]
        action = cmd.replace('ENCODER_', '').lower()
        target, value, wait_ms = '-', '-', '-'

        if action == 'focus':
            target = parse_target_from_args(args) or '-'
        elif action == 'scroll':
            try:
                value = str(int(args.strip()))
            except ValueError:
                value = '1'

        if i + 1 < len(filtered) and filtered[i + 1][0] == 'WAIT':
            try:
                wait_ms = filtered[i + 1][1].strip()
            except (ValueError, IndexError):
                pass
            i += 2
        else:
            i += 1

        enc_rows.append({
            'action': action,
            'target': target,
            'value': value,
            'wait_ms': wait_ms
        })

    return i, Section(
        type='ENCODER',
        columns=['action', 'target', 'value', 'wait_ms'],
        rows=enc_rows,
        comment='Encoder HW',
    )

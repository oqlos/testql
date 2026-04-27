"""Rendering utilities for OQL/TQL converter."""

from .models import Section

# Commands to skip when building sections (already handled or metadata)
SKIP_COMMANDS: frozenset[str] = frozenset(
    {'SET', 'COMMENT', 'BLANK', 'LOG', 'PRINT', 'GET'}
)


def build_config_section(commands: list[tuple[str, str]]) -> Section | None:
    """Collect SET commands into a CONFIG section (or None if empty)."""
    rows = []
    for cmd, args in commands:
        if cmd == 'SET':
            parts = args.split(None, 1)
            key = parts[0] if parts else ''
            value = parts[1].strip().strip('"\'') if len(parts) > 1 else ''
            rows.append({'key': key, 'value': value})

    if rows:
        return Section(
            type='CONFIG',
            columns=['key', 'value'],
            rows=rows,
            comment='Konfiguracja'
        )
    return None


def _render_section_header(sec) -> str:
    """Return the SECTION[N]{col,...}: header line for *sec*."""
    count = len(sec.rows)
    cols_str = ', '.join(sec.columns)
    if sec.columns:
        return f'{sec.type}[{count}]{{{cols_str}}}:' if count > 0 else f'{sec.type}:'
    return f'{sec.type}:'


def render_sections(sections: list[Section]) -> str:
    """Phase 4: render collected sections to TestTOON text."""
    out: list[str] = []

    for sec in sections:
        if sec.comment:
            out.append(f'# ── {sec.comment} {"─" * max(1, 50 - len(sec.comment))}')

        out.append(_render_section_header(sec))

        for row in sec.rows:
            vals = [
                str(row.get(col, '-')) if row.get(col) is not None else '-'
                for col in sec.columns
            ]
            out.append('  ' + ',  '.join(vals) if vals else '  ')

        out.append('')

    return '\n'.join(out)


def build_header(scenario_name: str, scenario_type: str) -> str:
    """Build scenario header."""
    return f'# SCENARIO: {scenario_name}\n# TYPE: {scenario_type}\n# VERSION: 1.0\n\n'

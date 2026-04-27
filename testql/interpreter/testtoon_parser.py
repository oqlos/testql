"""Parser for TestTOON tabular format."""

from __future__ import annotations

import re

from .testtoon_models import ToonSection, ToonScript

HEADER_RE = re.compile(r'^([A-Z_]+)(?:\[(\d+)\])?\{([^}]*)\}:\s*$')
META_RE = re.compile(r'^#\s*([A-Z_]+):\s*(.+)$')
MAPPING_HEADER_RE = re.compile(r'^([A-Z_]+):\s*$')


def _detect_separator(line: str) -> str:
    """Detect column separator in a line."""
    return '|' if '|' in line else ','


def _parse_inline_array(v: str) -> list:
    """Parse a '[a,b,c]' string into a list of parsed values."""
    return [_parse_value(x) for x in v[1:-1].split(',')]


def _parse_inline_dict(v: str) -> dict:
    """Parse a '{k:v,k:v}' string into a dict of parsed values."""
    result = {}
    for pair in v[1:-1].split(','):
        if ':' in pair:
            k, val = pair.split(':', 1)
            key = k.strip().strip('"').strip("'")
            result[key] = _parse_value(val)
    return result


def _parse_value(v: str):
    """Parse values: -, numbers, {json}, arrays [1,2], strings."""
    v = v.strip()
    if v == '-':
        return None
    if v.startswith('[') and v.endswith(']'):
        return _parse_inline_array(v)
    if v.startswith('{') and v.endswith('}'):
        return _parse_inline_dict(v)
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v.strip('"')


def _make_section(m: re.Match) -> ToonSection:
    """Build a ToonSection from a HEADER_RE match."""
    cols = [c.strip() for c in m.group(3).split(',') if c.strip()]
    return ToonSection(
        type=m.group(1),
        columns=cols,
        rows=[],
        expected_count=int(m.group(2)) if m.group(2) else None,
    )


def _make_mapping_section(m: re.Match) -> ToonSection:
    """Build a ToonSection from a MAPPING_HEADER_RE match (YAML key-value format)."""
    return ToonSection(
        type=m.group(1),
        columns=[],  # No columns in mapping format
        rows=[],
        expected_count=None,
        is_mapping=True,
    )


def _make_data_row(raw: str, section: ToonSection) -> dict:
    """Parse one indented data line into a column→value dict."""
    line = raw.strip()
    sep = _detect_separator(line)
    parts = line.split(sep, len(section.columns) - 1)
    return {col: _parse_value(val) for col, val in zip(section.columns, parts)}


def _make_mapping_row(raw: str) -> dict:
    """Parse a YAML key-value line (key: value) into a dict.
    
    Supports formats:
    - key: value
    - key1 key2: value (for keys with spaces)
    """
    line = raw.strip()
    if ':' not in line:
        return {}
    
    # Split on first colon only
    key_part, value = line.split(':', 1)
    key = key_part.strip()
    if key.startswith('- '):
        key = key[2:].strip()
    elif key.startswith('-'):
        key = key[1:].strip()
    
    return {key: _parse_value(value.strip())}


def parse_testtoon(text: str, filename: str = "<string>") -> ToonScript:
    """Parse TestTOON source into structured ToonScript."""
    script = ToonScript()
    current: ToonSection | None = None
    bare_commands: list[str] = []

    for raw in text.splitlines():
        current = _process_line(raw, current, script, bare_commands)

    _add_bare_commands_section(script, bare_commands)
    return script


def _process_line(raw: str, current: ToonSection | None, script: ToonScript, bare_commands: list[str]) -> ToonSection | None:
    """Process a single line of TestTOON source."""
    stripped = raw.strip()
    
    if not stripped:
        return None
    
    if _is_meta_line(stripped):
        return _process_meta_line(stripped, script)
    
    if _is_comment(stripped):
        return None
    
    section = _try_parse_section_header(stripped)
    if section:
        script.sections.append(section)
        return section
    
    if _should_end_section(raw, current):
        current = None
    
    if _is_bare_command(raw, current):
        bare_commands.append(raw)
        return None
    
    if current and raw.startswith('  '):
        _add_row_to_section(raw, current)
    
    return current


def _is_meta_line(line: str) -> bool:
    """Check if line is a meta line."""
    return META_RE.match(line) is not None


def _process_meta_line(line: str, script: ToonScript) -> None:
    """Process a meta line and add to script metadata."""
    m = META_RE.match(line)
    if m:
        script.meta[m.group(1).lower()] = m.group(2).strip()
    return None


def _is_comment(line: str) -> bool:
    """Check if line is a comment."""
    return line.startswith('#')


def _try_parse_section_header(line: str) -> ToonSection | None:
    """Try to parse a section header from line."""
    m = HEADER_RE.match(line)
    if m:
        return _make_section(m)
    
    m = MAPPING_HEADER_RE.match(line)
    if m and '{' not in line:
        return _make_mapping_section(m)
    
    return None


def _should_end_section(raw: str, current: ToonSection | None) -> bool:
    """Check if current section should end."""
    return current is not None and not raw.startswith('  ')


def _is_bare_command(raw: str, current: ToonSection | None) -> bool:
    """Check if line is a bare imperative command."""
    return not raw.startswith('  ') and current is None


def _add_row_to_section(raw: str, current: ToonSection) -> None:
    """Add a data row to current section."""
    if current.is_mapping:
        mapping_row = _make_mapping_row(raw)
        if mapping_row and current.rows:
            current.rows[0].update(mapping_row)
        elif mapping_row:
            current.rows.append(mapping_row)
    else:
        current.rows.append(_make_data_row(raw, current))


def _add_bare_commands_section(script: ToonScript, bare_commands: list[str]) -> None:
    """Add bare commands as a special COMMANDS section."""
    if not bare_commands:
        return
    
    cmd_section = ToonSection(
        type='COMMANDS',
        columns=['command'],
        rows=[{'command': cmd} for cmd in bare_commands],
        expected_count=len(bare_commands),
    )
    
    insert_pos = _find_commands_insert_position(script.sections)
    script.sections.insert(insert_pos, cmd_section)


def _find_commands_insert_position(sections: list[ToonSection]) -> int:
    """Find position to insert COMMANDS section (after CONFIG if exists)."""
    for i, section in enumerate(sections):
        if section.type == 'CONFIG':
            return i + 1
    return 0

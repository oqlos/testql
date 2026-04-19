#!/usr/bin/env python3
"""
Convert IQL/TQL scripts to TestTOON format (*.testql.toon.yaml).

Usage:
    python -m testql.interpreter._converter path/to/file.tql
    python -m testql.interpreter._converter --batch testql/scenarios/
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Row:
    values: dict[str, str]


@dataclass
class Section:
    type: str
    columns: list[str]
    rows: list[dict] = field(default_factory=list)
    comment: str = ""


def _parse_api_args(args: str) -> tuple[str, str]:
    """Parse 'GET "/url"' or 'GET /url' → (method, endpoint)."""
    parts = args.strip().split(None, 1)
    method = parts[0].upper() if parts else "GET"
    endpoint = parts[1].strip().strip('"\'') if len(parts) > 1 else "/"
    # Remove trailing JSON body for now
    if endpoint and '{' in endpoint:
        endpoint = endpoint[:endpoint.index('{')].strip().rstrip()
    return method, endpoint


def _parse_meta_from_args(args: str) -> str:
    """Extract JSON-like metadata from command args."""
    # Find {...} in args
    m = re.search(r'\{[^}]+\}', args)
    if m:
        raw = m.group(0)
        # Convert from JSON to TOON inline format: {key:value, key:value}
        try:
            d = json.loads(raw.replace("'", '"'))
            return '{' + ', '.join(f'{k}:{v}' for k, v in d.items()) + '}'
        except (json.JSONDecodeError, ValueError):
            return raw
    return '-'


def _parse_target_from_args(args: str) -> str:
    """Extract quoted target from args."""
    m = re.match(r'"([^"]*)"', args.strip())
    if m:
        return m.group(1)
    m = re.match(r"'([^']*)'", args.strip())
    if m:
        return m.group(1)
    # No quotes — take first token
    return args.strip().split()[0] if args.strip() else ''


def _detect_scenario_type(commands: list[tuple[str, str]]) -> str:
    """Heuristic to detect test type from commands."""
    has_api = any(c == 'API' for c, _ in commands)
    has_navigate = any(c == 'NAVIGATE' for c, _ in commands)
    has_encoder = any(c.startswith('ENCODER_') for c, _ in commands)
    has_select = any(c.startswith('SELECT_') for c, _ in commands)
    has_record = any(c in ('RECORD_START', 'RECORD_STOP') for c, _ in commands)

    if has_record:
        return 'interaction'
    if has_navigate and has_api and has_select:
        return 'e2e'
    if has_encoder or has_navigate:
        return 'gui'
    return 'api'


def _extract_scenario_name(comments: list[str], filename: str) -> str:
    """Extract scenario name from first meaningful comment or filename."""
    for c in comments:
        text = c.lstrip('#').strip()
        if text and not text.startswith(('Run with', 'Usage:', 'Run:', 'Requires:', 'Tests:')):
            # Skip lines that look like configuration hints
            if '://' not in text and not text.startswith(('or:', 'DSL Format')):
                return text
    # Fallback: filename
    stem = Path(filename).stem.replace('-', ' ').replace('_', ' ').title()
    return stem


# ── Command handlers ────────────────────────────────────────────────────────

_FLOW_COMMANDS: frozenset[str] = frozenset({
    'START_TEST', 'PROTOCOL_CREATED', 'PROTOCOL_FINALIZE',
    'STEP_COMPLETE', 'SESSION_START', 'SESSION_END',
    'APP_START', 'APP_INIT', 'APP_READY', 'APP_ERROR',
    'MODULE_LOAD', 'MODULE_READY', 'MODULE_ERROR',
    'PAGE_SETUP', 'PAGE_ERROR', 'PAGE_RENDER',
    'REPORT_AUTOOPEN', 'REPORT_FETCH', 'REPORT_OPEN',
    'REPORT_ERROR', 'REPORT_PRINT', 'REPORT_LIST',
    'PROTOCOL_FETCH', 'PROTOCOL_LOAD', 'PROTOCOL_PARSE',
    'PROTOCOL_NORMALIZE', 'PROTOCOL_FILTER', 'PROTOCOL_ERROR',
    'TEST_RUN_PARAMS', 'OPEN_INTERVAL_DIALOG', 'EMIT',
})

_SKIP_COMMANDS: frozenset[str] = frozenset(
    {'SET', 'COMMENT', 'BLANK', 'LOG', 'PRINT', 'GET'}
)


def _collect_assert(filtered: list, j: int) -> tuple[int, int, str | None, str | None]:
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


def _handle_api(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive API + ASSERT* rows into one API Section."""
    api_rows: list[dict] = []
    has_assert_key = False
    while i < len(filtered) and filtered[i][0] == 'API':
        cmd, args = filtered[i]
        method, endpoint = _parse_api_args(args)
        j, status, assert_key, assert_value = _collect_assert(filtered, i + 1)
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


def _handle_navigate(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive NAVIGATE (+ optional WAIT) rows."""
    nav_rows: list[dict] = []
    while i < len(filtered) and filtered[i][0] == 'NAVIGATE':
        _, args = filtered[i]
        path = _parse_target_from_args(args)
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
    return i, Section(type='NAVIGATE', columns=['path', 'wait_ms'], rows=nav_rows, comment='Nawigacja UI')


def _handle_encoder(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive ENCODER_* (+ optional WAIT) rows."""
    enc_rows: list[dict] = []
    while i < len(filtered) and filtered[i][0].startswith('ENCODER_'):
        cmd, args = filtered[i]
        action = cmd.replace('ENCODER_', '').lower()
        target, value, wait_ms = '-', '-', '-'
        if action == 'focus':
            target = args.strip().strip('"\'') or '-'
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
        enc_rows.append({'action': action, 'target': target, 'value': value, 'wait_ms': wait_ms})
    return i, Section(
        type='ENCODER', columns=['action', 'target', 'value', 'wait_ms'],
        rows=enc_rows, comment='Encoder HW',
    )


def _handle_select(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive SELECT* rows."""
    sel_rows: list[dict] = []
    while i < len(filtered) and filtered[i][0].startswith('SELECT'):
        cmd, args = filtered[i]
        action = cmd.replace('SELECT_', '').lower()
        sel_rows.append({'action': action, 'id': _parse_target_from_args(args), 'meta': _parse_meta_from_args(args)})
        i += 1
    return i, Section(type='SELECT', columns=['action', 'id', 'meta'], rows=sel_rows, comment='Wybory domenowe')


def _handle_flow(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive FLOW (semantic lifecycle) commands."""
    flow_rows: list[dict] = []
    while i < len(filtered) and filtered[i][0] in _FLOW_COMMANDS:
        cmd, args = filtered[i]
        flow_rows.append({
            'command': cmd.lower(),
            'target': _parse_target_from_args(args),
            'meta': _parse_meta_from_args(args),
        })
        i += 1
    return i, Section(type='FLOW', columns=['command', 'target', 'meta'], rows=flow_rows, comment='Kroki semantyczne')


def _handle_record_start(filtered: list, i: int) -> tuple[int, Section]:
    _, args = filtered[i]
    return i + 1, Section(
        type='RECORD_START', columns=['session_id'],
        rows=[{'session_id': _parse_target_from_args(args)}], comment='Nagrywanie sesji',
    )


def _handle_record_stop(filtered: list, i: int) -> tuple[int, Section]:
    return i + 1, Section(type='RECORD_STOP', columns=[], rows=[{}])


def _handle_wait(filtered: list, i: int) -> tuple[int, Section]:
    """Collect consecutive standalone WAIT rows."""
    wait_rows: list[dict] = []
    while i < len(filtered) and filtered[i][0] == 'WAIT':
        try:
            ms = int(filtered[i][1].strip())
        except ValueError:
            ms = 100
        wait_rows.append({'ms': str(ms)})
        i += 1
    return i, Section(type='WAIT', columns=['ms'], rows=wait_rows)


def _handle_include(filtered: list, i: int) -> tuple[int, Section]:
    _, args = filtered[i]
    return i + 1, Section(
        type='INCLUDE', columns=['file'],
        rows=[{'file': _parse_target_from_args(args)}],
    )


def _handle_unknown(filtered: list, i: int) -> tuple[int, Section]:
    cmd, args = filtered[i]
    return i + 1, Section(
        type='FLOW', columns=['command', 'target', 'meta'],
        rows=[{'command': cmd.lower(),
               'target': _parse_target_from_args(args) if args else '-',
               'meta': _parse_meta_from_args(args) if args else '-'}],
    )


def _dispatch(filtered: list, i: int) -> tuple[int, Section]:
    """Dispatch one command to its handler; return (new_i, section)."""
    cmd = filtered[i][0]
    if cmd == 'API':
        return _handle_api(filtered, i)
    if cmd == 'NAVIGATE':
        return _handle_navigate(filtered, i)
    if cmd.startswith('ENCODER_'):
        return _handle_encoder(filtered, i)
    if cmd.startswith('SELECT'):
        return _handle_select(filtered, i)
    if cmd in _FLOW_COMMANDS:
        return _handle_flow(filtered, i)
    if cmd == 'RECORD_START':
        return _handle_record_start(filtered, i)
    if cmd == 'RECORD_STOP':
        return _handle_record_stop(filtered, i)
    if cmd == 'WAIT':
        return _handle_wait(filtered, i)
    if cmd == 'INCLUDE':
        return _handle_include(filtered, i)
    return _handle_unknown(filtered, i)


def _parse_commands(source: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Phase 1: tokenise source into (cmd, args) tuples and collect comments."""
    commands: list[tuple[str, str]] = []
    comments: list[str] = []
    for raw in source.splitlines():
        stripped = raw.strip()
        if not stripped:
            commands.append(('BLANK', ''))
            continue
        if stripped.startswith('#'):
            comments.append(stripped)
            commands.append(('COMMENT', stripped))
            continue
        parts = stripped.split(None, 1)
        cmd = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ''
        commands.append((cmd, args))
    return commands, comments


def _build_config_section(commands: list[tuple[str, str]]) -> Section | None:
    """Collect SET commands into a CONFIG section (or None if empty)."""
    rows = []
    for cmd, args in commands:
        if cmd == 'SET':
            parts = args.split(None, 1)
            key = parts[0] if parts else ''
            value = parts[1].strip().strip('"\'') if len(parts) > 1 else ''
            rows.append({'key': key, 'value': value})
    if rows:
        return Section(type='CONFIG', columns=['key', 'value'], rows=rows, comment='Konfiguracja')
    return None


def _render_sections(sections: list[Section]) -> str:
    """Phase 4: render collected sections to TestTOON text."""
    out: list[str] = []
    for sec in sections:
        if sec.comment:
            out.append(f'# ── {sec.comment} {"─" * max(1, 50 - len(sec.comment))}')
        count = len(sec.rows)
        cols_str = ', '.join(sec.columns)
        out.append(f'{sec.type}[{count}]{{{cols_str}}}:' if sec.columns else f'{sec.type}:')
        for row in sec.rows:
            vals = [str(row.get(col, '-')) if row.get(col) is not None else '-' for col in sec.columns]
            out.append('  ' + ',  '.join(vals) if vals else '  ')
        out.append('')
    return '\n'.join(out)


# ── Public API ───────────────────────────────────────────────────────────────

def convert_iql_to_testtoon(source: str, filename: str = "<string>") -> str:
    """Convert IQL/TQL source text to TestTOON format."""
    # Phase 1: tokenise
    commands, comments = _parse_commands(source)

    # Phase 2: detect metadata
    scenario_name = _extract_scenario_name(comments, filename)
    scenario_type = _detect_scenario_type(commands)

    # Phase 3: group into sections
    sections: list[Section] = []
    config = _build_config_section(commands)
    if config:
        sections.append(config)

    filtered = [(c, a) for c, a in commands if c not in _SKIP_COMMANDS]
    i = 0
    while i < len(filtered):
        i, section = _dispatch(filtered, i)
        sections.append(section)

    # Phase 4: render
    header = f'# SCENARIO: {scenario_name}\n# TYPE: {scenario_type}\n# VERSION: 1.0\n\n'
    return header + _render_sections(sections)


def convert_file(src: Path) -> Path:
    """Convert a single .tql/.iql file to .testql.toon.yaml."""
    source = src.read_text(encoding='utf-8')
    stem = src.stem  # e.g. "backend-diagnostic"
    dest = src.parent / f'{stem}.testql.toon.yaml'
    result = convert_iql_to_testtoon(source, src.name)
    dest.write_text(result, encoding='utf-8')
    return dest


def convert_directory(dir_path: Path) -> list[Path]:
    """Recursively convert all .tql and .iql files in a directory."""
    converted = []
    for pattern in ('**/*.tql', '**/*.iql'):
        for f in sorted(dir_path.rglob(pattern.split('/')[-1])):
            if f.suffix in ('.tql', '.iql'):
                dest = convert_file(f)
                converted.append(dest)
                print(f'  {f.relative_to(dir_path)} → {dest.name}')
    return converted


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert IQL/TQL to TestTOON format')
    parser.add_argument('path', help='File or directory to convert')
    parser.add_argument('--batch', action='store_true', help='Recursively convert directory')
    parser.add_argument('--delete-originals', action='store_true', help='Delete .tql/.iql after conversion')
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_file():
        dest = convert_file(target)
        print(f'Converted: {target} → {dest}')
    elif target.is_dir() or args.batch:
        print(f'Converting directory: {target}')
        converted = convert_directory(target)
        print(f'\nConverted {len(converted)} files')
        if args.delete_originals:
            count = 0
            for f in target.rglob('*'):
                if f.suffix in ('.tql', '.iql'):
                    f.unlink()
                    count += 1
            print(f'Deleted {count} original files')
    else:
        print(f'Error: {target} is not a file or directory', file=sys.stderr)
        sys.exit(1)

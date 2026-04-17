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


def convert_iql_to_testtoon(source: str, filename: str = "<string>") -> str:
    """Convert IQL/TQL source text to TestTOON format."""

    # Phase 1: Parse into command tuples
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

    # Phase 2: Detect metadata
    scenario_name = _extract_scenario_name(comments, filename)
    scenario_type = _detect_scenario_type(commands)

    # Phase 3: Group commands into sections
    sections: list[Section] = []

    # Collect SET commands → CONFIG section
    config_rows = []
    for cmd, args in commands:
        if cmd == 'SET':
            parts = args.split(None, 1)
            key = parts[0] if parts else ''
            value = parts[1].strip().strip('"\'') if len(parts) > 1 else ''
            config_rows.append({'key': key, 'value': value})

    if config_rows:
        sections.append(Section(
            type='CONFIG',
            columns=['key', 'value'],
            rows=config_rows,
            comment='Konfiguracja',
        ))

    # Now process non-SET commands sequentially and group them
    # LOG and PRINT are converted to comments, so filter them out too
    i = 0
    filtered = [(c, a) for c, a in commands if c not in ('SET', 'COMMENT', 'BLANK', 'LOG', 'PRINT', 'GET')]

    while i < len(filtered):
        cmd, args = filtered[i]

        if cmd == 'API':
            # Collect consecutive API + ASSERT_STATUS pairs
            api_rows = []
            has_assert_key = False
            while i < len(filtered):
                cmd, args = filtered[i]
                if cmd != 'API':
                    break
                method, endpoint = _parse_api_args(args)
                status = 200
                assert_key = None
                assert_value = None
                # Look ahead for ASSERT_STATUS, ASSERT_OK, ASSERT_JSON
                j = i + 1
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
                        # Parse: field == value or field op value
                        parts = aargs.strip().split(None, 2)
                        if len(parts) >= 3:
                            assert_key = parts[0]
                            assert_value = parts[2].strip('"\'')
                            has_assert_key = True
                        elif len(parts) >= 1:
                            assert_key = parts[0]
                            assert_value = '-'
                            has_assert_key = True
                    j += 1

                row = {'method': method, 'endpoint': endpoint, 'status': str(status)}
                if has_assert_key and assert_key:
                    row['assert_key'] = assert_key
                    row['assert_value'] = assert_value or '-'
                api_rows.append(row)
                i = j
                continue

            cols = ['method', 'endpoint', 'status']
            if has_assert_key:
                cols.extend(['assert_key', 'assert_value'])
            sections.append(Section(
                type='API',
                columns=cols,
                rows=api_rows,
                comment='Wywołania API',
            ))
            continue

        if cmd == 'NAVIGATE':
            nav_rows = []
            while i < len(filtered):
                cmd, args = filtered[i]
                if cmd != 'NAVIGATE':
                    break
                path = _parse_target_from_args(args)
                wait_ms = 300  # default
                if i + 1 < len(filtered) and filtered[i + 1][0] == 'WAIT':
                    try:
                        wait_ms = int(filtered[i + 1][1].strip())
                    except ValueError:
                        pass
                    i += 2
                else:
                    i += 1
                nav_rows.append({'path': path, 'wait_ms': str(wait_ms)})

            sections.append(Section(
                type='NAVIGATE',
                columns=['path', 'wait_ms'],
                rows=nav_rows,
                comment='Nawigacja UI',
            ))
            continue

        if cmd.startswith('ENCODER_'):
            enc_rows = []
            while i < len(filtered):
                cmd, args = filtered[i]
                if not cmd.startswith('ENCODER_'):
                    break

                action = cmd.replace('ENCODER_', '').lower()
                target = '-'
                value = '-'
                wait_ms = '-'

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

                enc_rows.append({
                    'action': action,
                    'target': target,
                    'value': value,
                    'wait_ms': wait_ms,
                })

            sections.append(Section(
                type='ENCODER',
                columns=['action', 'target', 'value', 'wait_ms'],
                rows=enc_rows,
                comment='Encoder HW',
            ))
            continue

        if cmd in ('SELECT_DEVICE', 'SELECT_INTERVAL', 'SELECT'):
            sel_rows = []
            while i < len(filtered):
                cmd, args = filtered[i]
                if not cmd.startswith('SELECT'):
                    break
                action = cmd.replace('SELECT_', '').lower()
                target_id = _parse_target_from_args(args)
                meta = _parse_meta_from_args(args)
                sel_rows.append({'action': action, 'id': target_id, 'meta': meta})
                i += 1

            sections.append(Section(
                type='SELECT',
                columns=['action', 'id', 'meta'],
                rows=sel_rows,
                comment='Wybory domenowe',
            ))
            continue

        if cmd in ('START_TEST', 'PROTOCOL_CREATED', 'PROTOCOL_FINALIZE',
                    'STEP_COMPLETE', 'SESSION_START', 'SESSION_END',
                    'APP_START', 'APP_INIT', 'APP_READY', 'APP_ERROR',
                    'MODULE_LOAD', 'MODULE_READY', 'MODULE_ERROR',
                    'PAGE_SETUP', 'PAGE_ERROR', 'PAGE_RENDER',
                    'REPORT_AUTOOPEN', 'REPORT_FETCH', 'REPORT_OPEN',
                    'REPORT_ERROR', 'REPORT_PRINT', 'REPORT_LIST',
                    'PROTOCOL_FETCH', 'PROTOCOL_LOAD', 'PROTOCOL_PARSE',
                    'PROTOCOL_NORMALIZE', 'PROTOCOL_FILTER', 'PROTOCOL_ERROR',
                    'TEST_RUN_PARAMS', 'OPEN_INTERVAL_DIALOG', 'EMIT'):
            flow_rows = []
            semantic_set = {
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
            }
            while i < len(filtered) and filtered[i][0] in semantic_set:
                cmd, args = filtered[i]
                target = _parse_target_from_args(args)
                meta = _parse_meta_from_args(args)
                flow_rows.append({'command': cmd.lower(), 'target': target, 'meta': meta})
                i += 1

            sections.append(Section(
                type='FLOW',
                columns=['command', 'target', 'meta'],
                rows=flow_rows,
                comment='Kroki semantyczne',
            ))
            continue

        if cmd == 'RECORD_START':
            target = _parse_target_from_args(args)
            sections.append(Section(
                type='RECORD_START',
                columns=['session_id'],
                rows=[{'session_id': target}],
                comment='Nagrywanie sesji',
            ))
            i += 1
            continue

        if cmd == 'RECORD_STOP':
            sections.append(Section(
                type='RECORD_STOP',
                columns=[],
                rows=[{}],
            ))
            i += 1
            continue

        if cmd == 'WAIT':
            # Standalone WAIT (not absorbed by NAVIGATE/ENCODER)
            wait_rows = []
            while i < len(filtered) and filtered[i][0] == 'WAIT':
                try:
                    ms = int(filtered[i][1].strip())
                except ValueError:
                    ms = 100
                wait_rows.append({'ms': str(ms)})
                i += 1
            sections.append(Section(
                type='WAIT',
                columns=['ms'],
                rows=wait_rows,
            ))
            continue

        if cmd == 'INCLUDE':
            target = _parse_target_from_args(args)
            sections.append(Section(
                type='INCLUDE',
                columns=['file'],
                rows=[{'file': target}],
            ))
            i += 1
            continue

        # Unknown command — wrap as generic FLOW
        target = _parse_target_from_args(args) if args else '-'
        meta = _parse_meta_from_args(args) if args else '-'
        sections.append(Section(
            type='FLOW',
            columns=['command', 'target', 'meta'],
            rows=[{'command': cmd.lower(), 'target': target, 'meta': meta}],
        ))
        i += 1

    # Phase 4: Render TestTOON output
    out: list[str] = []
    out.append(f'# SCENARIO: {scenario_name}')
    out.append(f'# TYPE: {scenario_type}')
    out.append('# VERSION: 1.0')
    out.append('')

    for sec in sections:
        if sec.comment:
            out.append(f'# ── {sec.comment} {"─" * max(1, 50 - len(sec.comment))}')
        count = len(sec.rows)
        cols_str = ', '.join(sec.columns)
        if sec.columns:
            out.append(f'{sec.type}[{count}]{{{cols_str}}}:')
        else:
            out.append(f'{sec.type}:')
        for row in sec.rows:
            vals = []
            for col in sec.columns:
                v = row.get(col)
                if v is None:
                    vals.append('-')
                else:
                    vals.append(str(v))
            if vals:
                # Pad values for alignment
                out.append('  ' + ',  '.join(vals))
            else:
                out.append('  ')
        out.append('')

    return '\n'.join(out)


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

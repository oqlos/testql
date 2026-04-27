"""
TestTOON Parser — tabular test format inspired by TOON.

Parses *.testql.toon.yaml files into OqlScript (flat command list)
so the existing OqlInterpreter can execute them without changes.

Format spec:
    # SCENARIO: Name
    # TYPE: api | e2e | gui | interaction

    SECTION[count]{col1, col2, col3}:
      val1, val2, val3
      val1, val2, val3
"""

from __future__ import annotations

import json

from ._parser import OqlLine, OqlScript
from .testtoon_models import ToonSection, ToonScript
from .testtoon_parser import parse_testtoon

# Backward compatibility: re-export classes that were moved
from .testtoon_models import ToonSection, ToonScript  # noqa: F401
from .testtoon_parser import parse_testtoon  # noqa: F401


def validate_testtoon(script: ToonScript) -> list[str]:
    """Validate row counts against declared counts."""
    errors = []
    for s in script.sections:
        errors.extend(s.validate())
    return errors


# ── Expansion to OqlScript ────────────────────────────────────────────────────

_ENCODER_ACTION_MAP = {
    'on': 'ENCODER_ON',
    'off': 'ENCODER_OFF',
    'click': 'ENCODER_CLICK',
    'dblclick': 'ENCODER_DBLCLICK',
    'status': 'ENCODER_STATUS',
    'page_next': 'ENCODER_PAGE_NEXT',
    'page_prev': 'ENCODER_PAGE_PREV',
    'scroll': 'ENCODER_SCROLL',
    'focus': 'ENCODER_FOCUS',
}


def _expand_config(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand CONFIG section → SET commands."""

    def _append_set(key: str, value: object, current_line: int) -> int:
        if not key or value is None:
            return current_line
        key_quoted = f'"{key}"' if ' ' in str(key) else key
        if '${' in str(value) and '}' in str(value):
            raw = f'SET {key_quoted} {value}'
            lines.append(OqlLine(number=current_line, command='SET', args=f'{key_quoted} {value}', raw=raw))
        else:
            raw = f'SET {key_quoted} "{value}"'
            lines.append(OqlLine(number=current_line, command='SET', args=f'{key_quoted} "{value}"', raw=raw))
        return current_line + 1

    for row in section.rows:
        # Tabular format: CONFIG[n]{key, value} rows.
        if 'key' in row:
            key = str(row.get('key', '')).strip()
            value = row.get('value')
            line_num = _append_set(key, value, line_num)
            continue

        # Mapping format: CONFIG: key: value
        for key, value in row.items():
            line_num = _append_set(str(key).strip(), value, line_num)
    return line_num


def _append_api_asserts(row: dict, lines: list[OqlLine], line_num: int) -> int:
    """Append optional ASSERT_STATUS and ASSERT_JSON lines for an API row."""
    status = row.get('status') or row.get('expect_status') or row.get('expected_status')
    if status is not None:
        raw_a = f'ASSERT_STATUS {status}'
        lines.append(OqlLine(number=line_num, command='ASSERT_STATUS', args=str(status), raw=raw_a))
        line_num += 1

    assert_key = row.get('assert_key')
    assert_value = row.get('assert_value') or row.get('assert_val')
    if assert_key and assert_key is not None and assert_value and assert_value is not None:
        raw_j = f'ASSERT_JSON {assert_key} == "{assert_value}"'
        lines.append(OqlLine(
            number=line_num, command='ASSERT_JSON',
            args=f'{assert_key} == "{assert_value}"', raw=raw_j,
        ))
        line_num += 1
    return line_num


def _expand_api(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand API section → API + ASSERT_STATUS commands."""
    for row in section.rows:
        method = row.get('method', 'GET')
        endpoint = row.get('endpoint', '/')
        body = row.get('body')
        
        body_str = ''
        if isinstance(body, dict):
            # Encode dict to JSON string for the OQL command
            body_str = ' ' + json.dumps(body)
        elif body:
            body_str = ' ' + str(body)

        raw = f'API {method} "{endpoint}"{body_str}'
        lines.append(OqlLine(number=line_num, command='API', args=f'{method} "{endpoint}"{body_str}', raw=raw))
        line_num = _append_api_asserts(row, lines, line_num + 1)
    return line_num


def _expand_navigate(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand NAVIGATE section → NAVIGATE + WAIT commands."""
    for row in section.rows:
        path = row.get('path', '/')
        raw = f'NAVIGATE "{path}"'
        lines.append(OqlLine(number=line_num, command='NAVIGATE', args=f'"{path}"', raw=raw))
        line_num += 1

        wait_ms = row.get('wait_ms')
        if wait_ms is not None:
            raw_w = f'WAIT {wait_ms}'
            lines.append(OqlLine(number=line_num, command='WAIT', args=str(wait_ms), raw=raw_w))
            line_num += 1
    return line_num


def _expand_encoder(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand ENCODER section → ENCODER_* + WAIT commands."""
    for row in section.rows:
        action = str(row.get('action', '')).lower()
        target = row.get('target')
        value = row.get('value')
        wait_ms = row.get('wait_ms')

        oql_cmd = _ENCODER_ACTION_MAP.get(action, f'ENCODER_{action.upper()}')

        if action == 'scroll' and value is not None:
            args = str(value)
        elif action == 'focus' and target:
            args = f'"{target}"'
        else:
            args = ''

        raw = f'{oql_cmd} {args}'.strip()
        lines.append(OqlLine(number=line_num, command=oql_cmd, args=args, raw=raw))
        line_num += 1

        if wait_ms is not None:
            raw_w = f'WAIT {wait_ms}'
            lines.append(OqlLine(number=line_num, command='WAIT', args=str(wait_ms), raw=raw_w))
            line_num += 1
    return line_num


def _expand_select(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand SELECT section → SELECT_DEVICE / SELECT_INTERVAL commands."""
    for row in section.rows:
        action = str(row.get('action', '')).upper()
        target_id = row.get('id', '')
        meta = row.get('meta')

        cmd = f'SELECT_{action}'
        meta_str = ''
        if isinstance(meta, dict):
            pairs = ', '.join(f'"{k}": "{v}"' for k, v in meta.items())
            meta_str = f' {{{pairs}}}'
        elif meta:
            meta_str = f' {meta}'

        args = f'"{target_id}"{meta_str}'
        raw = f'{cmd} {args}'
        lines.append(OqlLine(number=line_num, command=cmd, args=args, raw=raw))
        line_num += 1
    return line_num


def _expand_assert(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand ASSERT section → ASSERT_* commands.

    Supports two formats:
    - {field, op, expected} → ASSERT_JSON (for API/JSON assertions)
    - {selector, expected} → ASSERT_VISIBLE (for GUI assertions)
    """
    for row in section.rows:
        # GUI format: {selector, expected}
        if 'selector' in section.columns:
            selector = row.get('selector', '')
            expected = row.get('expected', '')
            if expected == 'visible':
                raw = f'ASSERT_VISIBLE "{selector}"'
                lines.append(OqlLine(
                    number=line_num, command='ASSERT_VISIBLE',
                    args=f'"{selector}"', raw=raw,
                ))
            else:
                raw = f'ASSERT_TEXT "{selector}" "{expected}"'
                lines.append(OqlLine(
                    number=line_num, command='ASSERT_TEXT',
                    args=f'"{selector}" "{expected}"', raw=raw,
                ))
            line_num += 1
            continue

        # JSON format: {field, op, expected}
        field_name = row.get('field', '')
        op = row.get('op') or row.get('operator') or '=='
        expected = row.get('expected', '')
        if not field_name:
            continue  # Skip empty assertions

        # Special handling for status assertions
        if field_name in ('_status', 'status', 'status_code') and op in ('==', '=', '!='):
            cmd = 'ASSERT_STATUS'
            raw = f'{cmd} {expected}'
            lines.append(OqlLine(
                number=line_num, command=cmd,
                args=str(expected), raw=raw,
            ))
        else:
            raw = f'ASSERT_JSON {field_name} {op} {expected}'
            lines.append(OqlLine(
                number=line_num, command='ASSERT_JSON',
                args=f'{field_name} {op} {expected}', raw=raw,
            ))
        line_num += 1
    return line_num


def _expand_steps(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand STEPS section → STEP_COMPLETE commands."""
    for i, row in enumerate(section.rows, 1):
        name = row.get('name', f'step-{i}')
        status = row.get('status', 'passed')
        value = row.get('value')

        meta_parts = [f'"name": "{name}"', f'"status": "{status}"']
        if value is not None:
            meta_parts.append(f'"value": "{value}"')
        meta_str = '{' + ', '.join(meta_parts) + '}'

        cmd = 'STEP_COMPLETE'
        args = f'"step-{i}" {meta_str}'
        raw = f'{cmd} {args}'
        lines.append(OqlLine(number=line_num, command=cmd, args=args, raw=raw))
        line_num += 1
    return line_num


def _expand_flow(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand FLOW section → semantic commands (CLICK, INPUT, START_TEST, …).

    Supported third columns (any one):
        - ``meta``  → legacy raw passthrough (supports inline ``{k:v}`` dicts).
        - ``value`` / ``text`` → quoted positional argument (e.g. for INPUT).

    A ``-`` / null placeholder yields no extra argument so commands like CLICK
    still emit ``CLICK "selector"`` cleanly.
    """
    for row in section.rows:
        command = str(row.get('command', '')).upper()
        target = row.get('target', '')

        extra = ''
        # Prefer explicit value/text columns (typed text input)
        if 'value' in row or 'text' in row:
            v = row.get('value') if 'value' in row else row.get('text')
            if isinstance(v, dict):
                pairs = ', '.join(f'"{k}": "{val}"' for k, val in v.items())
                extra = f' {{{pairs}}}'
            elif v is not None and v != '' and v != '-' and str(v).lower() != 'null':
                extra = f' "{v}"'
        else:
            meta = row.get('meta')
            if isinstance(meta, dict):
                pairs = ', '.join(f'"{k}": "{v}"' for k, v in meta.items())
                extra = f' {{{pairs}}}'
            elif meta:
                extra = f' {meta}'

        args = f'"{target}"{extra}'
        raw = f'{command} {args}'
        lines.append(OqlLine(number=line_num, command=command, args=args, raw=raw))
        line_num += 1
    return line_num


def _expand_oql(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand OQL section → OQL_RUN commands."""
    for row in section.rows:
        file_path = row.get('file', '')
        device = row.get('device', '')
        mode = row.get('mode', 'execute')
        args = f'"{file_path}" device="{device}" mode="{mode}"'
        raw = f'OQL_RUN {args}'
        lines.append(OqlLine(number=line_num, command='OQL_RUN', args=args, raw=raw))
        line_num += 1
    return line_num


def _expand_wait(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand WAIT section → WAIT commands."""
    for row in section.rows:
        ms = row.get('ms', 100)
        raw = f'WAIT {ms}'
        lines.append(OqlLine(number=line_num, command='WAIT', args=str(ms), raw=raw))
        line_num += 1
    return line_num


def _expand_include(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand INCLUDE section → INCLUDE commands."""
    for row in section.rows:
        file_path = row.get('file', '')
        raw = f'INCLUDE "{file_path}"'
        lines.append(OqlLine(number=line_num, command='INCLUDE', args=f'"{file_path}"', raw=raw))
        line_num += 1
    return line_num


def _expand_record(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand RECORD_START / RECORD_STOP sections."""
    for row in section.rows:
        session_id = row.get('session_id', '')
        if session_id:
            raw = f'RECORD_START "{session_id}"'
            lines.append(OqlLine(number=line_num, command='RECORD_START', args=f'"{session_id}"', raw=raw))
        else:
            raw = 'RECORD_STOP'
            lines.append(OqlLine(number=line_num, command='RECORD_STOP', args='', raw=raw))
        line_num += 1
    return line_num


def _expand_commands(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand COMMANDS section (bare imperative commands) → emit as-is."""
    for row in section.rows:
        cmd = row.get('command', '').strip()
        if not cmd:
            continue
        
        # Parse command and args
        parts = cmd.split(None, 1)
        command_name = parts[0] if parts else ''
        args = parts[1] if len(parts) > 1 else ''
        
        if command_name:
            lines.append(OqlLine(number=line_num, command=command_name, args=args, raw=cmd))
            line_num += 1
    
    return line_num


def _expand_dom_audit_buttons(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand DOM_AUDIT_BUTTONS section (mapping format) → DOM_AUDIT_BUTTONS command."""
    if not section.rows:
        # No arguments, just emit the command
        raw = 'DOM_AUDIT_BUTTONS'
        lines.append(OqlLine(number=line_num, command='DOM_AUDIT_BUTTONS', args='', raw=raw))
        return line_num + 1

    # Extract mapping data
    data = section.rows[0] if section.rows else {}
    selector = data.get('selector', '')
    ignore = data.get('ignore', '')
    report_file = data.get('report_file', '')

    # Build command args
    args_parts = []
    if selector:
        args_parts.append(f'--selector "{selector}"')
    if ignore:
        args_parts.append(f'--ignore "{ignore}"')
    if report_file:
        args_parts.append(f'--report-file "{report_file}"')

    args = ' '.join(args_parts)
    raw = f'DOM_AUDIT_BUTTONS {args}'.strip()

    lines.append(OqlLine(number=line_num, command='DOM_AUDIT_BUTTONS', args=args, raw=raw))
    return line_num + 1


def _expand_generic(section: ToonSection, lines: list[OqlLine], line_num: int) -> int:
    """Expand unknown section types as generic commands."""
    for row in section.rows:
        values = [str(v) if v is not None else '-' for v in row.values()]
        cmd = section.type
        args = ' '.join(values)
        raw = f'{cmd} {args}'
        lines.append(OqlLine(number=line_num, command=cmd, args=args, raw=raw))
        line_num += 1
    return line_num


_SECTION_EXPANDERS = {
    'CONFIG': _expand_config,
    'API': _expand_api,
    'NAVIGATE': _expand_navigate,
    'ENCODER': _expand_encoder,
    'SELECT': _expand_select,
    'ASSERT': _expand_assert,
    'STEPS': _expand_steps,
    'FLOW': _expand_flow,
    'OQL': _expand_oql,
    'WAIT': _expand_wait,
    'INCLUDE': _expand_include,
    'RECORD_START': _expand_record,
    'RECORD_STOP': _expand_record,
    'DOM_AUDIT_BUTTONS': _expand_dom_audit_buttons,
    'COMMANDS': _expand_commands,
}


def testtoon_to_oql(text: str, filename: str = "<string>") -> OqlScript:
    """Parse TestTOON source and expand to OqlScript for execution."""
    toon = parse_testtoon(text, filename)
    lines: list[OqlLine] = []
    line_num = 1

    for section in toon.sections:
        expander = _SECTION_EXPANDERS.get(section.type, _expand_generic)
        line_num = expander(section, lines, line_num)

    return OqlScript(filename=filename, lines=lines)

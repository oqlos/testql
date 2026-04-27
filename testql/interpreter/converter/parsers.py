"""Parsing utilities for OQL/TQL converter."""

from __future__ import annotations

import json
import re
from pathlib import Path


def parse_api_args(args: str) -> tuple[str, str]:
    """Parse 'GET "/url"' or 'GET /url' → (method, endpoint)."""
    parts = args.strip().split(None, 1)
    method = parts[0].upper() if parts else "GET"
    endpoint = parts[1].strip().strip('"\'') if len(parts) > 1 else "/"
    # Remove trailing JSON body for now
    if endpoint and '{' in endpoint:
        endpoint = endpoint[:endpoint.index('{')].strip().rstrip()
    return method, endpoint


def parse_meta_from_args(args: str) -> str:
    """Extract JSON-like metadata from command args."""
    m = re.search(r'\{[^}]+\}', args)
    if m:
        raw = m.group(0)
        try:
            d = json.loads(raw.replace("'", '"'))
            return '{' + ', '.join(f'{k}:{v}' for k, v in d.items()) + '}'
        except (json.JSONDecodeError, ValueError):
            return raw
    return '-'


def parse_target_from_args(args: str) -> str:
    """Extract quoted target from args."""
    m = re.match(r'"([^"]*)"', args.strip())
    if m:
        return m.group(1)
    m = re.match(r"'([^']*)'", args.strip())
    if m:
        return m.group(1)
    # No quotes — take first token
    return args.strip().split()[0] if args.strip() else ''


def parse_commands(source: str) -> tuple[list[tuple[str, str]], list[str]]:
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


def detect_scenario_type(commands: list[tuple[str, str]]) -> str:
    """Heuristic to detect test type from commands."""
    cmd_set = {c for c, _ in commands}
    has_record = bool(cmd_set & {'RECORD_START', 'RECORD_STOP'})
    has_navigate = any(c == 'NAVIGATE' for c in cmd_set)
    has_api = 'API' in cmd_set
    has_encoder = any(c.startswith('ENCODER_') for c in cmd_set)
    has_select = any(c.startswith('SELECT_') for c in cmd_set)

    if has_record:
        return 'interaction'
    if has_navigate and has_api and has_select:
        return 'e2e'
    if has_encoder or has_navigate:
        return 'gui'
    return 'api'


def extract_scenario_name(comments: list[str], filename: str) -> str:
    """Extract scenario name from first meaningful comment or filename."""
    for c in comments:
        text = c.lstrip('#').strip()
        if text and not text.startswith(('Run with', 'Usage:', 'Run:', 'Requires:', 'Tests:')):
            if '://' not in text and not text.startswith(('or:', 'DSL Format')):
                return text
    # Fallback: filename
    stem = Path(filename).stem.replace('-', ' ').replace('_', ' ').title()
    return stem

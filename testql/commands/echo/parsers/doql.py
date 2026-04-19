"""DOQL LESS file parser for echo command."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


# Annotation prefixes recognized in entity blocks
_ANNOTATION_PREFIXES = ('intent:', 'domain:', 'lifetime:')


def _parse_kv_block(body: str) -> dict[str, str]:
    """Parse a simple key: value; block body into a dict."""
    result: dict[str, str] = {}
    for line in body.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            result[key.strip()] = val.strip().rstrip(';')
    return result


def _parse_app_block(content: str) -> dict[str, str]:
    """Parse app { ... } block."""
    m = re.search(r'app\s*\{([^}]+)\}', content)
    return _parse_kv_block(m.group(1)) if m else {}


def _parse_entities(content: str) -> list[dict]:
    """Parse entity[name="..."] { ... } blocks."""
    entities = []
    for match in re.finditer(r'entity\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        entity: dict = {"name": name, "fields": [], "annotations": {}}
        for line in body.strip().split('\n'):
            line = line.strip()
            if any(line.startswith(p) for p in _ANNOTATION_PREFIXES):
                key, val = line.split(':', 1)
                entity["annotations"][key.strip()] = val.strip().rstrip(';').strip('"')
            elif ':' in line and not line.startswith('#'):
                entity["fields"].append(line.rstrip(';'))
        entities.append(entity)
    return entities


def _parse_interfaces(content: str) -> list[dict]:
    """Parse interface[type="..."] { ... } blocks."""
    result = []
    for match in re.finditer(r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        iface_type, body = match.groups()
        iface = {"type": iface_type, **_parse_kv_block(body)}
        result.append(iface)
    return result


def _parse_workflows(content: str) -> list[dict]:
    """Parse workflow[name="..."] { ... } blocks."""
    workflows = []
    for match in re.finditer(r'workflow\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        wf: dict = {"name": name, "steps": [], "annotations": {}}
        for line in body.strip().split('\n'):
            line = line.strip()
            if any(line.startswith(p) for p in ('intent:', 'domain:')):
                key, val = line.split(':', 1)
                wf["annotations"][key.strip()] = val.strip().rstrip(';').strip('"')
            elif line.startswith('trigger:'):
                wf["trigger"] = line.split(':', 1)[1].strip().rstrip(';')
            elif line.startswith('step-'):
                wf["steps"].append(line.split(':', 1)[1].strip().rstrip(';'))
        workflows.append(wf)
    return workflows


def _parse_deploy(content: str) -> dict[str, str]:
    """Parse deploy { ... } block."""
    m = re.search(r'deploy\s*\{([^}]+)\}', content)
    return _parse_kv_block(m.group(1)) if m else {}


def _parse_environment(content: str) -> dict:
    """Parse environment[name="..."] { ... } blocks."""
    for match in re.finditer(r'environment\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        return {"name": name, **_parse_kv_block(body)}
    return {}


def _parse_integrations(content: str) -> list[dict]:
    """Parse integration[name="..."] { ... } blocks."""
    integrations = []
    for match in re.finditer(r'integration\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        types = [
            line.split(':', 1)[1].strip().rstrip(';')
            for line in body.strip().split('\n')
            if line.strip().startswith('type:')
        ]
        integrations.append({"name": name, "types": list(set(types))})
    return integrations


def parse_doql_less(filepath: Path) -> dict[str, Any]:
    """Parse .doql.less file into structured system model."""
    content = filepath.read_text()
    return {
        "app": _parse_app_block(content),
        "entities": _parse_entities(content),
        "interfaces": _parse_interfaces(content),
        "workflows": _parse_workflows(content),
        "deploy": _parse_deploy(content),
        "environment": _parse_environment(content),
        "integrations": _parse_integrations(content),
    }

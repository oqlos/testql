"""Text output formatter for echo command."""

from __future__ import annotations

from typing import Any


def _fmt_interfaces(context: dict) -> list[str]:
    """Format interfaces section."""
    interfaces = context.get("system_model", {}).get("interfaces", [])
    if not interfaces:
        return []
    lines = ["🧠 Type:"]
    for iface in interfaces:
        lines.append(f"  • {iface['type']} ({iface.get('framework', 'unknown')})")
    lines.append("")
    return lines


def _fmt_workflows(context: dict) -> list[str]:
    """Format workflows section."""
    workflows = context.get("system_model", {}).get("workflows", [])
    if not workflows:
        return []
    lines = ["🛠️ Workflows:"]
    for wf in workflows:
        steps = len(wf.get("steps", []))
        lines.append(f"  • {wf['name']}: {steps} step(s)")
    lines.append("")
    return lines


def _fmt_contracts(context: dict) -> list[str]:
    """Format API contracts section."""
    contracts = context.get("api_contracts", [])
    if not contracts:
        return []
    lines = ["🌐 API scenarios (from toon tests):"]
    for contract in contracts:
        lines.append(f"  • {contract['name']} ({contract['type']}) - {len(contract['endpoints'])} endpoint(s)")
        for ep in contract["endpoints"][:3]:
            lines.append(f"    - {ep['method']} {ep['path'][:50]}")
        if len(contract["endpoints"]) > 3:
            lines.append(f"    ... and {len(contract['endpoints']) - 3} more")
    lines.append("")
    return lines


def _fmt_entities(context: dict) -> list[str]:
    """Format entities section."""
    entities = context.get("system_model", {}).get("entities", [])
    if not entities:
        return []
    lines = [f"📊 Entities: {len(entities)}"]
    for e in entities[:5]:
        lines.append(f"  • {e['name']} ({len(e.get('fields', []))} fields)")
    if len(entities) > 5:
        lines.append(f"  ... and {len(entities) - 5} more")
    lines.append("")
    return lines


def _fmt_suggestions(context: dict) -> list[str]:
    """Format LLM suggestions section."""
    workflows = context.get("system_model", {}).get("workflows", [])
    contracts = context.get("api_contracts", [])
    lines = ["💡 LLM suggestions:"]
    if any(w['name'] == 'install' for w in workflows):
        lines.append("  • Setup: task install")
    if contracts:
        lines.append("  • Run tests: testql suite")
    if any(w['name'] == 'run' for w in workflows):
        lines.append("  • Start server: task run")
    return lines


def _build_header(context: dict) -> list[str]:
    """Build output header."""
    app = context.get("system_model", {}).get("app", {})
    name = app.get('name', context['project']['name'])
    version = app.get('version', '?.?.?')
    return [f"📦 Project: {name} ({version})", ""]


def format_text_output(context: dict[str, Any]) -> str:
    """Format context as human-readable text."""
    sections = (
        _build_header(context)
        + _fmt_interfaces(context)
        + _fmt_workflows(context)
        + _fmt_contracts(context)
        + _fmt_entities(context)
        + _fmt_suggestions(context)
    )
    return "\n".join(sections)

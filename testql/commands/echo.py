"""Echo command - Generate AI-friendly project context from toon + doql."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import click
import yaml


def _parse_kv_block(body: str) -> dict[str, str]:
    """Parse a simple key: value; block body into a dict."""
    result: dict[str, str] = {}
    for line in body.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            result[key.strip()] = val.strip().rstrip(';')
    return result


_ANNOTATION_PREFIXES = ('intent:', 'domain:', 'lifetime:')


def _parse_app_block(content: str) -> dict[str, str]:
    m = re.search(r'app\s*\{([^}]+)\}', content)
    return _parse_kv_block(m.group(1)) if m else {}


def _parse_entities(content: str) -> list[dict]:
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
    result = []
    for match in re.finditer(r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        iface_type, body = match.groups()
        iface = {"type": iface_type, **_parse_kv_block(body)}
        result.append(iface)
    return result


def _parse_workflows(content: str) -> list[dict]:
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
    m = re.search(r'deploy\s*\{([^}]+)\}', content)
    return _parse_kv_block(m.group(1)) if m else {}


def _parse_environment(content: str) -> dict:
    for match in re.finditer(r'environment\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        return {"name": name, **_parse_kv_block(body)}
    return {}


def _parse_integrations(content: str) -> list[dict]:
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


def parse_toon_scenarios(path: Path) -> list[dict[str, Any]]:
    """Parse .testql.toon.yaml files into API contract structure."""
    contracts = []
    
    for file in path.rglob("*.testql.toon.yaml"):
        content = yaml.safe_load(file.read_text())
        if not content:
            continue
            
        contract = {
            "file": str(file.relative_to(path)),
            "name": content.get("meta", {}).get("name", file.stem),
            "type": content.get("meta", {}).get("type", "api"),
            "tags": content.get("meta", {}).get("tags", []),
            "endpoints": [],
            "asserts": [],
        }
        
        # Parse scenario steps
        for key, value in content.items():
            if key in ("meta", "config", "variables"):
                continue
            
            # Detect HTTP methods
            if key.upper() in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                contract["endpoints"].append({
                    "method": key.upper(),
                    "path": str(value) if not isinstance(value, dict) else value.get("url", ""),
                    "status": None,
                })
            
            # Detect asserts
            if key.startswith("ASSERT"):
                contract["asserts"].append({
                    "type": key,
                    "condition": value,
                })
        
        contracts.append(contract)
    
    return contracts


def generate_context(path: Path, include_toon: bool = True, include_doql: bool = True) -> dict[str, Any]:
    """Generate unified project context."""
    context = {
        "project": {
            "path": str(path),
            "name": path.name,
        },
        "generated_at": None,
    }
    
    # Parse doql
    if include_doql:
        doql_files = list(path.rglob("*.doql.less")) + list(path.rglob("app.doql.css"))
        if doql_files:
            # Prefer .less over .css
            doql_file = next((f for f in doql_files if f.suffix == ".less"), doql_files[0])
            context["system_model"] = parse_doql_less(doql_file)
    
    # Parse toon
    if include_toon:
        toon_path = path / "testql-scenarios" if (path / "testql-scenarios").exists() else path
        context["api_contracts"] = parse_toon_scenarios(toon_path)
    
    return context


def _fmt_interfaces(context: dict) -> list[str]:
    interfaces = context.get("system_model", {}).get("interfaces", [])
    if not interfaces:
        return []
    lines = ["🧠 Type:"]
    for iface in interfaces:
        lines.append(f"  • {iface['type']} ({iface.get('framework', 'unknown')})")
    lines.append("")
    return lines


def _fmt_workflows(context: dict) -> list[str]:
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


def format_text_output(context: dict[str, Any]) -> str:
    """Format context as human-readable text."""
    app = context.get("system_model", {}).get("app", {})
    header = [f"📦 Project: {app.get('name', context['project']['name'])} ({app.get('version', '?.?.?')})", ""]
    sections = (
        header
        + _fmt_interfaces(context)
        + _fmt_workflows(context)
        + _fmt_contracts(context)
        + _fmt_entities(context)
        + _fmt_suggestions(context)
    )
    return "\n".join(sections)


@click.command()
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="text")
@click.option("--no-toon", is_flag=True, help="Exclude toon/API layer")
@click.option("--no-doql", is_flag=True, help="Exclude doql/system layer")
@click.option("--output", "-o", type=click.Path(), help="Output file")
def echo(path: str, fmt: str, no_toon: bool, no_doql: bool, output: str | None):
    """Generate AI-friendly project context (echo) from toon + doql."""
    target = Path(path)
    
    context = generate_context(
        target,
        include_toon=not no_toon,
        include_doql=not no_doql,
    )
    
    if fmt == "json":
        output_str = json.dumps(context, indent=2, default=str)
    else:
        output_str = format_text_output(context)
    
    if output:
        Path(output).write_text(output_str)
        click.echo(f"✅ Project context saved: {output}")
    else:
        click.echo(output_str)

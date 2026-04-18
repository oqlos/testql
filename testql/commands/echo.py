"""Echo command - Generate AI-friendly project context from toon + doql."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import click
import yaml


def parse_doql_less(filepath: Path) -> dict[str, Any]:
    """Parse .doql.less file into structured system model."""
    content = filepath.read_text()
    
    model = {
        "app": {},
        "entities": [],
        "interfaces": [],
        "workflows": [],
        "deploy": {},
        "environment": {},
        "integrations": [],
    }
    
    # Parse app block
    app_match = re.search(r'app\s*\{([^}]+)\}', content)
    if app_match:
        for line in app_match.group(1).strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                model["app"][key.strip()] = val.strip().rstrip(';')
    
    # Parse entities
    for match in re.finditer(r'entity\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        entity = {"name": name, "fields": [], "annotations": {}}
        for line in body.strip().split('\n'):
            line = line.strip()
            if line.startswith('intent:') or line.startswith('domain:') or line.startswith('lifetime:'):
                key, val = line.split(':', 1)
                entity["annotations"][key.strip()] = val.strip().rstrip(';').strip('"')
            elif ':' in line and not line.startswith('#'):
                entity["fields"].append(line.rstrip(';'))
        model["entities"].append(entity)
    
    # Parse interfaces
    for match in re.finditer(r'interface\[type="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        iface_type, body = match.groups()
        iface = {"type": iface_type}
        for line in body.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                iface[key.strip()] = val.strip().rstrip(';')
        model["interfaces"].append(iface)
    
    # Parse workflows
    for match in re.finditer(r'workflow\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        workflow = {"name": name, "steps": [], "annotations": {}}
        for line in body.strip().split('\n'):
            line = line.strip()
            if line.startswith('intent:') or line.startswith('domain:'):
                key, val = line.split(':', 1)
                workflow["annotations"][key.strip()] = val.strip().rstrip(';').strip('"')
            elif line.startswith('trigger:'):
                workflow["trigger"] = line.split(':', 1)[1].strip().rstrip(';')
            elif line.startswith('step-'):
                workflow["steps"].append(line.split(':', 1)[1].strip().rstrip(';'))
        model["workflows"].append(workflow)
    
    # Parse deploy
    deploy_match = re.search(r'deploy\s*\{([^}]+)\}', content)
    if deploy_match:
        for line in deploy_match.group(1).strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                model["deploy"][key.strip()] = val.strip().rstrip(';')
    
    # Parse environment
    for match in re.finditer(r'environment\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        env = {"name": name}
        for line in body.strip().split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                env[key.strip()] = val.strip().rstrip(';')
        model["environment"] = env
    
    # Parse integrations
    for match in re.finditer(r'integration\[name="([^"]+)"\]\s*\{([^}]+)\}', content, re.DOTALL):
        name, body = match.groups()
        integration = {"name": name}
        types = []
        for line in body.strip().split('\n'):
            if line.startswith('type:'):
                types.append(line.split(':', 1)[1].strip().rstrip(';'))
        integration["types"] = list(set(types))
        model["integrations"].append(integration)
    
    return model


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


def format_text_output(context: dict[str, Any]) -> str:
    """Format context as human-readable text."""
    lines = []
    
    app = context.get("system_model", {}).get("app", {})
    lines.append(f"📦 Project: {app.get('name', context['project']['name'])} ({app.get('version', '?.?.?')})")
    lines.append("")
    
    # Interfaces
    interfaces = context.get("system_model", {}).get("interfaces", [])
    if interfaces:
        lines.append("🧠 Type:")
        for iface in interfaces:
            lines.append(f"  • {iface['type']} ({iface.get('framework', 'unknown')})")
        lines.append("")
    
    # Workflows
    workflows = context.get("system_model", {}).get("workflows", [])
    if workflows:
        lines.append("🛠️ Workflows:")
        for wf in workflows:
            steps = len(wf.get("steps", []))
            lines.append(f"  • {wf['name']}: {steps} step(s)")
        lines.append("")
    
    # API endpoints from toon
    contracts = context.get("api_contracts", [])
    if contracts:
        lines.append("🌐 API scenarios (from toon tests):")
        for contract in contracts:
            lines.append(f"  • {contract['name']} ({contract['type']}) - {len(contract['endpoints'])} endpoint(s)")
            for ep in contract["endpoints"][:3]:
                lines.append(f"    - {ep['method']} {ep['path'][:50]}")
            if len(contract["endpoints"]) > 3:
                lines.append(f"    ... and {len(contract['endpoints']) - 3} more")
        lines.append("")
    
    # Entities
    entities = context.get("system_model", {}).get("entities", [])
    if entities:
        lines.append(f"📊 Entities: {len(entities)}")
        for e in entities[:5]:
            field_count = len(e.get("fields", []))
            lines.append(f"  • {e['name']} ({field_count} fields)")
        if len(entities) > 5:
            lines.append(f"  ... and {len(entities) - 5} more")
        lines.append("")
    
    # LLM suggestions
    lines.append("💡 LLM suggestions:")
    if workflows:
        install_wf = next((w for w in workflows if w['name'] == 'install'), None)
        if install_wf:
            lines.append(f"  • Setup: task install")
    if contracts:
        lines.append(f"  • Run tests: testql suite")
    if any(w['name'] == 'run' for w in workflows):
        lines.append(f"  • Start server: task run")
    
    return "\n".join(lines)


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

"""Resolve testql://block paths to data and partial .less renders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class BlockRef:
    kind: str
    name: str | None = None


def parse_block_ref(parts: list[str]) -> BlockRef:
    if not parts or parts[0] == "app":
        return BlockRef("app")
    if parts[0] == "deploy":
        return BlockRef("deploy")
    if parts[0] in {"entity", "workflow", "interface"} and len(parts) >= 2:
        return BlockRef(parts[0], parts[1])
    raise ValueError(f"unsupported block path: {'/'.join(parts)}")


def selector_from_ref(ref: BlockRef) -> str:
    if ref.kind == "app":
        return "app"
    if ref.kind == "deploy":
        return "deploy"
    if ref.kind == "entity" and ref.name:
        return f'entity[name="{ref.name}"]'
    if ref.kind == "workflow" and ref.name:
        return f'workflow[name="{ref.name}"]'
    if ref.kind == "interface" and ref.name:
        return f'interface[type="{ref.name}"]'
    return ref.name or ref.kind


def _find_named(items: list[Any], *, attr: str, name: str) -> Any | None:
    return next((item for item in items if getattr(item, attr, None) == name), None)


def extract_block_data(spec: Any, ref: BlockRef, to_plain: Callable[[Any], Any]) -> Any:
    if ref.kind == "app":
        return {"name": spec.project_name, "version": spec.version}
    if ref.kind == "deploy":
        return {"target": spec.deploy_target, "environment": spec.environment}
    if ref.kind == "entity":
        entity = _find_named(spec.entities, attr="name", name=ref.name or "")
        if entity is None:
            raise ValueError(f"entity not found: {ref.name}")
        return to_plain(entity)
    if ref.kind == "workflow":
        workflow = _find_named(spec.workflows, attr="name", name=ref.name or "")
        if workflow is None:
            raise ValueError(f"workflow not found: {ref.name}")
        return to_plain(workflow)
    if ref.kind == "interface":
        iface = _find_named(spec.interfaces, attr="type", name=ref.name or "")
        if iface is None:
            raise ValueError(f"interface not found: {ref.name}")
        return to_plain(iface)
    raise ValueError(f"unsupported block path: {ref.kind}")


def render_block_partial(spec: Any, ref: BlockRef) -> str:
    if ref.kind == "app":
        return f"app {{\n  name: {spec.project_name};\n  version: {spec.version};\n}}\n"
    if ref.kind == "deploy":
        return f"deploy {{\n  target: {spec.deploy_target};\n  environment: {spec.environment};\n}}\n"
    if ref.kind == "entity":
        entity = _find_named(spec.entities, attr="name", name=ref.name or "")
        if entity is None:
            raise ValueError(f"entity not found: {ref.name}")
        fields_str = "\n".join(f"  {field};" for field in entity.fields)
        return f'entity[name="{entity.name}"] {{\n{fields_str}\n}}\n'
    if ref.kind == "workflow":
        workflow = _find_named(spec.workflows, attr="name", name=ref.name or "")
        if workflow is None:
            raise ValueError(f"workflow not found: {ref.name}")
        return (
            f'workflow[name="{workflow.name}"] {{\n'
            f"  trigger: {workflow.trigger};\n  cmd = {workflow.cmd};\n}}\n"
        )
    if ref.kind == "interface":
        iface = _find_named(spec.interfaces, attr="type", name=ref.name or "")
        if iface is None:
            raise ValueError(f"interface not found: {ref.name}")
        framework_str = f"  framework: {iface.framework};\n" if iface.framework else ""
        return f'interface[type="{iface.type}"] {{\n{framework_str}}}\n'
    raise ValueError(f"unsupported block path: {ref.kind}")

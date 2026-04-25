from __future__ import annotations

import json
from typing import Literal

import yaml

from testql.topology.models import TopologyManifest

TopologyFormat = Literal["json", "yaml", "toon"]


def render_topology(topology: TopologyManifest, fmt: TopologyFormat = "toon", include_manifest: bool = False) -> str:
    data = topology.to_dict(include_manifest=include_manifest)
    if fmt == "json":
        return json.dumps(data, indent=2, sort_keys=True) + "\n"
    if fmt == "yaml":
        return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
    if fmt == "toon":
        return _render_toon(data)
    raise ValueError(f"unsupported topology format: {fmt}")


def _render_toon(data: dict) -> str:
    lines = ["TOPOLOGY{key, value}:"]
    lines.append(f"  root, {data['root']['location']}")
    lines.append(f"  confidence, {data['confidence']}")
    lines.append(f"  nodes, {len(data['nodes'])}")
    lines.append(f"  edges, {len(data['edges'])}")
    lines.append("")
    lines.append(f"NODES[{len(data['nodes'])}]{{id, kind, source}}:")
    for node in data["nodes"]:
        source = _source_location(node.get("source"))
        lines.append(f"  {node['id']}, {node['kind']}, {source}")
    lines.append("")
    lines.append(f"EDGES[{len(data['edges'])}]{{source_id, relation, target_id, protocol}}:")
    for edge in data["edges"]:
        protocol = edge.get("protocol", "")
        lines.append(f"  {edge['source_id']}, {edge['relation']}, {edge['target_id']}, {protocol}")
    if data.get("traces"):
        lines.append("")
        lines.append(f"TRACES[{len(data['traces'])}]{{id, status, nodes, edges}}:")
        for trace in data["traces"]:
            lines.append(f"  {trace['id']}, {trace['status']}, {len(trace['node_ids'])}, {len(trace['edge_ids'])}")
    return "\n".join(lines) + "\n"


def _source_location(source: object) -> str:
    if isinstance(source, dict):
        return str(source.get("location", ""))
    return str(source)

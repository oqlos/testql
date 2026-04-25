from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testql.discovery.manifest import Evidence, ManifestConfidence
from testql.discovery.source import ArtifactSource


@dataclass
class Condition:
    kind: str
    value: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        data = {"kind": self.kind, "value": self.value}
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data


@dataclass
class TopologyNode:
    id: str
    kind: str
    source: ArtifactSource | str
    manifest: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self, include_manifest: bool = False) -> dict:
        data = {
            "id": self.id,
            "kind": self.kind,
            "source": self.source.to_dict() if hasattr(self.source, "to_dict") else str(self.source),
            "metadata": dict(self.metadata),
            "evidence": [item.to_dict() for item in self.evidence],
        }
        if include_manifest and self.manifest is not None and hasattr(self.manifest, "to_dict"):
            data["manifest"] = self.manifest.to_dict()
        return data


@dataclass
class TopologyEdge:
    source_id: str
    target_id: str
    relation: str
    protocol: str | None = None
    conditions: list[Condition] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "conditions": [item.to_dict() for item in self.conditions],
            "evidence": [item.to_dict() for item in self.evidence],
        }
        if self.protocol:
            data["protocol"] = self.protocol
        return data


@dataclass
class TraversalTrace:
    id: str
    node_ids: list[str] = field(default_factory=list)
    edge_ids: list[str] = field(default_factory=list)
    status: str = "planned"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "node_ids": list(self.node_ids),
            "edge_ids": list(self.edge_ids),
            "status": self.status,
            "metadata": dict(self.metadata),
        }


@dataclass
class TopologyManifest:
    root: ArtifactSource
    nodes: list[TopologyNode] = field(default_factory=list)
    edges: list[TopologyEdge] = field(default_factory=list)
    confidence: ManifestConfidence = ManifestConfidence.INFERRED
    traces: list[TraversalTrace] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self, include_manifest: bool = False) -> dict:
        return {
            "root": self.root.to_dict(),
            "confidence": self.confidence.value,
            "metadata": dict(self.metadata),
            "nodes": [item.to_dict(include_manifest=include_manifest) for item in self.nodes],
            "edges": [item.to_dict() for item in self.edges],
            "traces": [item.to_dict() for item in self.traces],
        }

    def node(self, node_id: str) -> TopologyNode | None:
        return next((item for item in self.nodes if item.id == node_id), None)

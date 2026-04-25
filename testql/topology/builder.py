from __future__ import annotations

from pathlib import Path

from testql.discovery import ArtifactManifest, discover_path
from testql.discovery.manifest import Evidence, ManifestConfidence
from testql.discovery.source import ArtifactSource
from testql.topology.models import Condition, TopologyEdge, TopologyManifest, TopologyNode, TraversalTrace


class TopologyBuilder:
    def __init__(self, scan_network: bool = False):
        self.scan_network = scan_network

    def build(self, source: str | Path | ArtifactSource | ArtifactManifest) -> TopologyManifest:
        manifest = source if isinstance(source, ArtifactManifest) else discover_path(_source_location(source), scan_network=self.scan_network)
        root_source = manifest.source if isinstance(manifest.source, ArtifactSource) else ArtifactSource.from_value(str(manifest.source))
        topology = TopologyManifest(
            root=root_source,
            confidence=manifest.confidence,
            metadata={"generator": "testql.topology", "source_types": list(manifest.types)},
        )
        root_id = "artifact.root"
        topology.nodes.append(TopologyNode(root_id, "artifact", root_source, manifest, _root_metadata(manifest), manifest.evidence))
        self._add_type_nodes(topology, root_id, manifest)
        self._add_interface_nodes(topology, root_id, manifest)
        self._add_dependency_nodes(topology, root_id, manifest)
        self._add_evidence_nodes(topology, root_id, manifest)
        self._add_page_schema_nodes(topology, root_id, manifest)
        topology.traces.append(_default_trace(topology))
        return topology

    def _add_type_nodes(self, topology: TopologyManifest, root_id: str, manifest: ArtifactManifest) -> None:
        for artifact_type in manifest.types:
            node_id = f"type.{_safe_id(artifact_type)}"
            topology.nodes.append(TopologyNode(node_id, "artifact_type", manifest.source, metadata={"type": artifact_type}))
            topology.edges.append(TopologyEdge(root_id, node_id, "classified_as", "manifest", evidence=manifest.evidence[:3]))

    def _add_interface_nodes(self, topology: TopologyManifest, root_id: str, manifest: ArtifactManifest) -> None:
        for index, interface in enumerate(manifest.interfaces):
            node_id = f"interface.{_safe_id(interface.type)}.{index + 1}"
            protocol = _protocol_for_interface(interface.type)
            topology.nodes.append(TopologyNode(node_id, "interface", interface.location, metadata=interface.to_dict()))
            topology.edges.append(TopologyEdge(root_id, node_id, "exposes", protocol, evidence=manifest.evidence[:3]))

    def _add_dependency_nodes(self, topology: TopologyManifest, root_id: str, manifest: ArtifactManifest) -> None:
        for dep in manifest.dependencies[:100]:
            node_id = f"dependency.{_safe_id(dep.name)}"
            topology.nodes.append(TopologyNode(node_id, "dependency", dep.name, metadata=dep.to_dict()))
            topology.edges.append(
                TopologyEdge(
                    root_id,
                    node_id,
                    "depends_on",
                    "package",
                    conditions=[Condition("scope", dep.scope)],
                    evidence=manifest.evidence[:2],
                )
            )

    def _add_evidence_nodes(self, topology: TopologyManifest, root_id: str, manifest: ArtifactManifest) -> None:
        for index, evidence in enumerate(manifest.evidence[:50]):
            node_id = f"evidence.{index + 1}"
            topology.nodes.append(TopologyNode(node_id, "evidence", evidence.location, metadata=evidence.to_dict(), evidence=[evidence]))
            topology.edges.append(TopologyEdge(root_id, node_id, "supported_by", _protocol_for_evidence(evidence), evidence=[evidence]))

    def _add_page_schema_nodes(self, topology: TopologyManifest, root_id: str, manifest: ArtifactManifest) -> None:
        schema = manifest.metadata.get("page_schema")
        if not isinstance(schema, dict):
            return
        page_id = "page.root"
        topology.nodes.append(TopologyNode(page_id, "page", schema.get("url", manifest.source.location), metadata=schema, evidence=manifest.evidence[:3]))
        topology.edges.append(TopologyEdge(root_id, page_id, "renders", "browser", evidence=manifest.evidence[:3]))
        for index, link in enumerate(schema.get("links", [])[:50], start=1):
            node_id = f"link.{index}"
            topology.nodes.append(TopologyNode(node_id, "link", link.get("url", ""), metadata=dict(link), evidence=manifest.evidence[:1]))
            topology.edges.append(TopologyEdge(page_id, node_id, "links_to", "http", conditions=[Condition("kind", link.get("kind", "unknown"))], evidence=manifest.evidence[:1]))
        for index, asset in enumerate(schema.get("assets", [])[:50], start=1):
            node_id = f"asset.{index}"
            topology.nodes.append(TopologyNode(node_id, "asset", asset.get("url", ""), metadata=dict(asset), evidence=manifest.evidence[:1]))
            topology.edges.append(TopologyEdge(page_id, node_id, "loads", "http", evidence=manifest.evidence[:1]))
        for index, form in enumerate(schema.get("forms", [])[:25], start=1):
            node_id = f"form.{index}"
            topology.nodes.append(TopologyNode(node_id, "form", form.get("action", ""), metadata=dict(form), evidence=manifest.evidence[:1]))
            topology.edges.append(TopologyEdge(page_id, node_id, "submits_to", "http", conditions=[Condition("method", form.get("method", "get"))], evidence=manifest.evidence[:1]))


def build_topology(source: str | Path | ArtifactSource | ArtifactManifest, scan_network: bool = False) -> TopologyManifest:
    return TopologyBuilder(scan_network=scan_network).build(source)


def _source_location(source: str | Path | ArtifactSource) -> str | Path:
    if isinstance(source, ArtifactSource):
        return source.location
    return source


def _root_metadata(manifest: ArtifactManifest) -> dict:
    metadata = {
        "types": list(manifest.types),
        "confidence": manifest.confidence.value,
        "dependency_count": len(manifest.dependencies),
        "interface_count": len(manifest.interfaces),
        "evidence_count": len(manifest.evidence),
    }
    for key in ("name", "version", "description", "license"):
        if key in manifest.metadata:
            metadata[key] = manifest.metadata[key]
    return metadata


def _default_trace(topology: TopologyManifest) -> TraversalTrace:
    edge_ids = [f"{edge.source_id}->{edge.target_id}:{edge.relation}" for edge in topology.edges]
    return TraversalTrace(
        id="trace.discovery.topology",
        node_ids=[node.id for node in topology.nodes],
        edge_ids=edge_ids,
        status="planned",
        metadata={"purpose": "discovery-derived traversal plan"},
    )


def _safe_id(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else "_")
    return "".join(cleaned).strip("_") or "unknown"


def _protocol_for_interface(interface_type: str) -> str:
    mapping = {"rest": "http", "web_page": "browser", "graphql": "graphql", "grpc": "grpc", "websocket": "ws", "cli": "process"}
    return mapping.get(interface_type, interface_type)


def _protocol_for_evidence(evidence: Evidence) -> str:
    if evidence.kind.startswith("file"):
        return "file"
    return evidence.kind

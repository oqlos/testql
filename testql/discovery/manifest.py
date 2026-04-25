from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ManifestConfidence(Enum):
    FULL = "full"
    PARTIAL = "partial"
    INFERRED = "inferred"


@dataclass
class Evidence:
    probe: str
    kind: str
    location: str
    detail: str = ""

    def to_dict(self) -> dict:
        data = {"probe": self.probe, "kind": self.kind, "location": self.location}
        if self.detail:
            data["detail"] = self.detail
        return data


@dataclass
class Dependency:
    name: str
    version: str | None = None
    scope: str = "runtime"

    def to_dict(self) -> dict:
        data = {"name": self.name, "scope": self.scope}
        if self.version:
            data["version"] = self.version
        return data


@dataclass
class Interface:
    type: str
    location: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "location": self.location, "metadata": dict(self.metadata)}


@dataclass
class BuildArtifact:
    type: str
    location: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"type": self.type, "location": self.location, "metadata": dict(self.metadata)}


@dataclass
class ArtifactManifest:
    source: Any
    types: list[str] = field(default_factory=list)
    confidence: ManifestConfidence = ManifestConfidence.INFERRED
    metadata: dict[str, Any] = field(default_factory=dict)
    interfaces: list[Interface] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    artifacts: list[BuildArtifact] = field(default_factory=list)
    children: list["ArtifactManifest"] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    raw_probes: list[Any] = field(default_factory=list)

    @classmethod
    def from_probe_results(cls, source: Any, results: list[Any]) -> "ArtifactManifest":
        matched = [result for result in results if result.matched]
        types = _unique(item for result in matched for item in result.artifact_types)
        metadata = _merge_metadata([result.metadata for result in matched])
        evidence = [item for result in matched for item in result.evidence]
        dependencies = _dependencies_from_metadata(metadata)
        interfaces = _interfaces_from_metadata(metadata)
        confidence = _score_confidence(matched)
        return cls(
            source=source,
            types=types,
            confidence=confidence,
            metadata=metadata,
            interfaces=interfaces,
            dependencies=dependencies,
            evidence=evidence,
            raw_probes=results,
        )

    def to_dict(self, include_raw: bool = False) -> dict:
        data = {
            "source": self.source.to_dict() if hasattr(self.source, "to_dict") else str(self.source),
            "types": list(self.types),
            "confidence": self.confidence.value,
            "metadata": dict(self.metadata),
            "interfaces": [item.to_dict() for item in self.interfaces],
            "dependencies": [item.to_dict() for item in self.dependencies],
            "artifacts": [item.to_dict() for item in self.artifacts],
            "children": [item.to_dict(include_raw=include_raw) for item in self.children],
            "evidence": [item.to_dict() for item in self.evidence],
        }
        if include_raw:
            data["raw_probes"] = [item.to_dict() for item in self.raw_probes]
        return data


def _score_confidence(results: list[Any]) -> ManifestConfidence:
    if not results:
        return ManifestConfidence.INFERRED
    best = max(result.confidence for result in results)
    if best >= 80:
        return ManifestConfidence.FULL
    if best >= 30:
        return ManifestConfidence.PARTIAL
    return ManifestConfidence.INFERRED


def _merge_metadata(items: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in items:
        for key, value in item.items():
            if key in {"dependencies", "interfaces"}:
                merged.setdefault(key, [])
                merged[key].extend(value)
            elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
                merged[key].extend(value)
            elif value not in (None, "", [], {}):
                merged[key] = value
    for key in {"dependencies", "interfaces"}:
        if key in merged:
            merged[key] = _dedupe_dicts(merged[key])
    return merged


def _dependencies_from_metadata(metadata: dict[str, Any]) -> list[Dependency]:
    deps = []
    for item in metadata.get("dependencies", []):
        if isinstance(item, dict) and item.get("name"):
            deps.append(Dependency(item["name"], item.get("version"), item.get("scope", "runtime")))
    return deps


def _interfaces_from_metadata(metadata: dict[str, Any]) -> list[Interface]:
    interfaces = []
    for item in metadata.get("interfaces", []):
        if isinstance(item, dict) and item.get("type") and item.get("location"):
            interfaces.append(Interface(item["type"], item["location"], item.get("metadata", {})))
    return interfaces


def _unique(values) -> list[str]:
    seen = set()
    output = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output


def _dedupe_dicts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for item in items:
        key = tuple(sorted((str(k), str(v)) for k, v in item.items()))
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output

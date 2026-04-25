from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from testql.discovery.manifest import Evidence
from testql.discovery.source import ArtifactSource, SourceKind


@dataclass
class ProbeResult:
    matched: bool
    confidence: int
    artifact_types: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list[ArtifactSource] = field(default_factory=list)
    probe_name: str = ""

    def to_dict(self) -> dict:
        return {
            "probe": self.probe_name,
            "matched": self.matched,
            "confidence": self.confidence,
            "artifact_types": list(self.artifact_types),
            "evidence": [item.to_dict() for item in self.evidence],
            "metadata": dict(self.metadata),
            "children": [item.to_dict() for item in self.children],
        }


class Probe(ABC):
    name: str
    artifact_types: tuple[str, ...]
    cost: Literal["cheap", "medium", "expensive"]

    @abstractmethod
    def applicable(self, source: ArtifactSource) -> bool:
        raise NotImplementedError

    @abstractmethod
    def probe(self, source: ArtifactSource) -> ProbeResult:
        raise NotImplementedError


class BaseProbe(Probe):
    name = "base"
    artifact_types: tuple[str, ...] = ()
    cost: Literal["cheap", "medium", "expensive"] = "cheap"

    def applicable(self, source: ArtifactSource) -> bool:
        return source.kind == SourceKind.PATH

    def no_match(self) -> ProbeResult:
        return ProbeResult(False, 0, probe_name=self.name)

    def result(self, confidence: int, artifact_types: list[str], evidence: list[Evidence], metadata: dict[str, Any] | None = None, children: list[ArtifactSource] | None = None) -> ProbeResult:
        return ProbeResult(True, confidence, artifact_types, evidence, metadata or {}, children or [], self.name)

    def evidence(self, kind: str, location: Path, detail: str = "") -> Evidence:
        return Evidence(self.name, kind, str(location), detail)

    def source_roots(self, source: ArtifactSource) -> list[Path]:
        path = source.path
        roots = [path]
        if path.is_dir() and (path / "__init__.py").exists() and (path.parent / "pyproject.toml").exists():
            roots.append(path.parent)
        return roots

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource


class NodePackageProbe(BaseProbe):
    name = "filesystem.package_node"
    artifact_types = ("node_pkg",)
    cost = "medium"
    markers = ("package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb", "tsconfig.json")

    def probe(self, source: ArtifactSource) -> ProbeResult:
        if not source.path.is_dir():
            return self.no_match()
        files = [source.path / name for name in self.markers if (source.path / name).exists()]
        if not files:
            return self.no_match()
        evidence = [self.evidence("file", path, "node package marker") for path in files]
        metadata = self._metadata(source.path / "package.json")
        types = ["node_pkg"]
        deps = {item.get("name", "") for item in metadata.get("dependencies", [])}
        if "react" in deps or "react-dom" in deps:
            types.append("react")
        if "next" in deps or (source.path / "next.config.js").exists() or (source.path / "next.config.ts").exists():
            types.append("nextjs")
        confidence = 90 if (source.path / "package.json").exists() and metadata.get("name") else 60
        return self.result(confidence, types, evidence, metadata)

    def _metadata(self, package_json: Path) -> dict[str, Any]:
        if not package_json.exists():
            return {}
        try:
            data = json.loads(package_json.read_text())
        except json.JSONDecodeError:
            return {}
        dependencies = []
        for scope in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            for name, version in data.get(scope, {}).items():
                dependencies.append({"name": name, "version": str(version), "scope": scope})
        return {
            key: value for key, value in {
                "name": data.get("name"),
                "version": data.get("version"),
                "description": data.get("description"),
                "license": data.get("license"),
                "scripts": data.get("scripts", {}),
                "dependencies": dependencies,
            }.items() if value not in (None, "", [], {})
        }

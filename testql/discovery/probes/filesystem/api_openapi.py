from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource


class OpenAPIProbe(BaseProbe):
    name = "filesystem.api_openapi"
    artifact_types = ("openapi3",)
    cost = "medium"
    patterns = ("openapi*.yaml", "openapi*.yml", "openapi*.json", "swagger*.yaml", "swagger*.yml", "swagger*.json")

    def probe(self, source: ArtifactSource) -> ProbeResult:
        specs = self._find_specs(source)
        matches = []
        for path in specs:
            data = self._load(path)
            if isinstance(data, dict) and (data.get("openapi") or data.get("swagger")):
                matches.append((path, data))
        if not matches:
            return self.no_match()
        path, spec = matches[0]
        version = str(spec.get("openapi") or spec.get("swagger"))
        artifact_type = "openapi3" if version.startswith("3") else "openapi2"
        metadata = self._metadata(path, spec, version)
        evidence = [self.evidence("file", item[0], f"OpenAPI/Swagger {version}") for item in matches]
        return self.result(95, [artifact_type], evidence, metadata)

    def _find_specs(self, source: ArtifactSource) -> list[Path]:
        specs = []
        roots = self.source_roots(source)
        for root in roots:
            if root.is_file():
                if any(root.match(pattern) for pattern in self.patterns):
                    specs.append(root)
            elif root.is_dir():
                for pattern in self.patterns:
                    specs.extend(path for path in root.rglob(pattern) if not _excluded(path))
        return sorted(set(specs))

    def _load(self, path: Path) -> Any:
        text = path.read_text(errors="ignore")
        if path.suffix == ".json":
            return json.loads(text)
        return yaml.safe_load(text)

    def _metadata(self, path: Path, spec: dict[str, Any], version: str) -> dict[str, Any]:
        info = spec.get("info") or {}
        paths = spec.get("paths") or {}
        return {
            "name": info.get("title"),
            "version": info.get("version"),
            "description": info.get("description"),
            "openapi_version": version,
            "path_count": len(paths),
            "interfaces": [{"type": "rest", "location": str(path), "metadata": {"paths": len(paths)}}],
        }


def _excluded(path: Path) -> bool:
    return any(part in {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"} for part in path.parts)

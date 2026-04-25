from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource


class DockerComposeProbe(BaseProbe):
    name = "filesystem.container_compose"
    artifact_types = ("docker_compose",)
    cost = "medium"
    names = ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml", "docker-compose.override.yml")

    def probe(self, source: ArtifactSource) -> ProbeResult:
        files = self._find_files(source.path)
        if not files:
            return self.no_match()
        evidence = [self.evidence("file", path, "docker compose marker") for path in files]
        metadata = self._metadata(files)
        confidence = 90 if metadata.get("services") else 70
        return self.result(confidence, ["docker_compose"], evidence, metadata)

    def _find_files(self, path: Path) -> list[Path]:
        if path.is_file() and path.name in self.names:
            return [path]
        if not path.is_dir():
            return []
        return [path / name for name in self.names if (path / name).exists()]

    def _metadata(self, files: list[Path]) -> dict[str, Any]:
        services: dict[str, dict[str, Any]] = {}
        for path in files:
            data = yaml.safe_load(path.read_text(errors="ignore")) or {}
            for name, config in (data.get("services") or {}).items():
                services[name] = {
                    "image": config.get("image") if isinstance(config, dict) else None,
                    "build": config.get("build") if isinstance(config, dict) else None,
                    "ports": config.get("ports", []) if isinstance(config, dict) else [],
                }
        return {"compose_files": [str(path) for path in files], "services": services}

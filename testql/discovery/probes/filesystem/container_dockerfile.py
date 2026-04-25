from __future__ import annotations

from pathlib import Path
from typing import Any

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource


class DockerfileProbe(BaseProbe):
    name = "filesystem.container_dockerfile"
    artifact_types = ("dockerfile",)
    cost = "cheap"
    names = ("Dockerfile", "Containerfile", ".dockerignore")

    def probe(self, source: ArtifactSource) -> ProbeResult:
        files = self._find_files(source.path)
        dockerfiles = [path for path in files if path.name in {"Dockerfile", "Containerfile"}]
        if not dockerfiles:
            return self.no_match()
        evidence = [self.evidence("file", path, "container build marker") for path in files]
        metadata = self._metadata(dockerfiles)
        return self.result(90, ["dockerfile"], evidence, metadata)

    def _find_files(self, path: Path) -> list[Path]:
        if path.is_file() and path.name in self.names:
            return [path]
        if not path.is_dir():
            return []
        return [path / name for name in self.names if (path / name).exists()]

    def _metadata(self, dockerfiles: list[Path]) -> dict[str, Any]:
        items = []
        for path in dockerfiles:
            text = path.read_text(errors="ignore")
            items.append({
                "path": str(path),
                "has_healthcheck": "HEALTHCHECK" in text.upper(),
                "has_non_root_user": any(line.strip().upper().startswith("USER ") and "ROOT" not in line.upper() for line in text.splitlines()),
            })
        return {"dockerfiles": items}

from __future__ import annotations

from pathlib import Path

from testql.discovery.manifest import ArtifactManifest
from testql.discovery.probes.base import Probe, ProbeResult
from testql.discovery.probes.filesystem import (
    DockerComposeProbe,
    DockerfileProbe,
    NodePackageProbe,
    OpenAPIProbe,
    PythonPackageProbe,
)
from testql.discovery.probes.network import HTTPPageProbe
from testql.discovery.probes.browser import PlaywrightPageProbe
from testql.discovery.source import ArtifactSource


class ProbeRegistry:
    def __init__(self, probes: list[Probe] | None = None, scan_network: bool = False, use_browser: bool = False):
        self.probes = probes or default_probes(scan_network=scan_network, use_browser=use_browser)

    def run(self, source: ArtifactSource | str | Path) -> list[ProbeResult]:
        artifact_source = source if isinstance(source, ArtifactSource) else ArtifactSource.from_value(source)
        results = []
        for probe in sorted(self.probes, key=_cost_key):
            if probe.applicable(artifact_source):
                try:
                    results.append(probe.probe(artifact_source))
                except Exception:
                    results.append(ProbeResult(False, 0, probe_name=probe.name))
        return results

    def discover(self, source: ArtifactSource | str | Path) -> ArtifactManifest:
        artifact_source = source if isinstance(source, ArtifactSource) else ArtifactSource.from_value(source)
        return ArtifactManifest.from_probe_results(artifact_source, self.run(artifact_source))


def default_probes(scan_network: bool = False, use_browser: bool = False) -> list[Probe]:
    probes: list[Probe] = [
        DockerfileProbe(),
        PythonPackageProbe(),
        NodePackageProbe(),
        OpenAPIProbe(),
        DockerComposeProbe(),
    ]
    if scan_network:
        probes.append(HTTPPageProbe())
    if use_browser:
        probes.append(PlaywrightPageProbe())
    return probes


def discover_path(path: str | Path, scan_network: bool = False, use_browser: bool = False) -> ArtifactManifest:
    return ProbeRegistry(scan_network=scan_network, use_browser=use_browser).discover(path)


def _cost_key(probe: Probe) -> int:
    return {"cheap": 0, "medium": 1, "expensive": 2}.get(probe.cost, 1)

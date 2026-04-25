from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from testql.cli import cli
from testql.discovery import ManifestConfidence, ProbeRegistry, discover_path


FIXTURES = Path(__file__).parent / "fixtures" / "discovery"


class TestDiscoveryCore:
    def test_empty_directory_is_inferred(self, tmp_path):
        manifest = discover_path(tmp_path)
        assert manifest.confidence is ManifestConfidence.INFERRED
        assert manifest.types == []

    def test_python_package_probe_detects_fastapi(self):
        manifest = discover_path(FIXTURES / "python_pkg")
        assert "python_pkg" in manifest.types
        assert "fastapi" in manifest.types
        assert manifest.confidence is ManifestConfidence.FULL
        assert manifest.metadata["name"] == "sample-python-api"
        assert any(dep.name == "fastapi" for dep in manifest.dependencies)

    def test_node_package_probe_detects_node_and_frontend_markers(self):
        manifest = discover_path(FIXTURES / "node_pkg")
        assert "node_pkg" in manifest.types
        assert "react" in manifest.types
        assert "nextjs" in manifest.types
        assert manifest.confidence is ManifestConfidence.FULL
        assert manifest.metadata["name"] == "sample-node-app"

    def test_openapi_probe_detects_openapi3_interface(self):
        manifest = discover_path(FIXTURES / "openapi3")
        assert manifest.types == ["openapi3"]
        assert manifest.confidence is ManifestConfidence.FULL
        assert manifest.interfaces[0].type == "rest"
        assert manifest.metadata["path_count"] == 1

    def test_dockerfile_probe_detects_container_metadata(self):
        manifest = discover_path(FIXTURES / "dockerfile")
        assert "dockerfile" in manifest.types
        dockerfile = manifest.metadata["dockerfiles"][0]
        assert dockerfile["has_healthcheck"] is True
        assert dockerfile["has_non_root_user"] is True

    def test_compose_probe_detects_services(self):
        manifest = discover_path(FIXTURES / "compose")
        assert "docker_compose" in manifest.types
        assert sorted(manifest.metadata["services"]) == ["api", "redis"]

    def test_registry_returns_raw_probe_results(self):
        results = ProbeRegistry().run(FIXTURES / "python_pkg")
        assert results
        assert any(result.probe_name == "filesystem.package_python" and result.matched for result in results)

    def test_self_discovery_detects_current_project_root(self):
        root = Path(__file__).parents[1]
        manifest = discover_path(root)
        assert "python_pkg" in manifest.types
        assert "fastapi" in manifest.types
        assert "openapi3" in manifest.types
        assert manifest.confidence is ManifestConfidence.FULL

    def test_self_discovery_detects_testql_package_directory(self):
        root = Path(__file__).parents[1]
        manifest = discover_path(root / "testql")
        assert "python_pkg" in manifest.types
        assert "fastapi" in manifest.types
        assert "openapi3" in manifest.types
        assert manifest.confidence is ManifestConfidence.FULL


class TestDiscoveryCli:
    def test_discover_summary_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(FIXTURES / "python_pkg")])
        assert result.exit_code == 0
        assert "Confidence: full" in result.output
        assert "python_pkg" in result.output

    def test_discover_json_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(FIXTURES / "openapi3"), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["types"] == ["openapi3"]
        assert data["raw_probes"]

    def test_discover_manifest_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(FIXTURES / "compose"), "--format", "manifest"])
        assert result.exit_code == 0
        assert "confidence: full" in result.output
        assert "docker_compose" in result.output

    def test_discover_missing_path_exits_nonzero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["discover", str(FIXTURES / "missing")])
        assert result.exit_code != 0
        assert "source does not exist" in result.output

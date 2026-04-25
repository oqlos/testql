from __future__ import annotations

import json
from pathlib import Path

import yaml
from click.testing import CliRunner

from testql.cli import cli
from testql.topology import build_topology, render_topology


FIXTURES = Path(__file__).parent / "fixtures" / "discovery"


class TestTopologyBuilder:
    def test_builds_root_type_dependency_and_evidence_nodes(self):
        topology = build_topology(FIXTURES / "python_pkg")
        node_ids = {node.id for node in topology.nodes}
        assert "artifact.root" in node_ids
        assert "type.python_pkg" in node_ids
        assert "type.fastapi" in node_ids
        assert "dependency.fastapi" in node_ids
        assert any(edge.relation == "classified_as" for edge in topology.edges)
        assert any(edge.relation == "depends_on" for edge in topology.edges)
        assert topology.traces[0].status == "planned"

    def test_builds_interface_node_for_openapi(self):
        topology = build_topology(FIXTURES / "openapi3")
        assert any(node.kind == "interface" for node in topology.nodes)
        assert any(edge.relation == "exposes" and edge.protocol == "http" for edge in topology.edges)

    def test_to_dict_can_embed_manifest(self):
        topology = build_topology(FIXTURES / "node_pkg")
        data = topology.to_dict(include_manifest=True)
        root = next(node for node in data["nodes"] if node["id"] == "artifact.root")
        assert root["manifest"]["types"]


class TestTopologySerializers:
    def test_render_json(self):
        topology = build_topology(FIXTURES / "python_pkg")
        data = json.loads(render_topology(topology, "json"))
        assert data["confidence"] == "full"
        assert data["nodes"]

    def test_render_yaml(self):
        topology = build_topology(FIXTURES / "compose")
        data = yaml.safe_load(render_topology(topology, "yaml"))
        assert data["root"]["location"].endswith("compose")
        assert any(node["id"] == "type.docker_compose" for node in data["nodes"])

    def test_render_toon(self):
        topology = build_topology(FIXTURES / "dockerfile")
        output = render_topology(topology, "toon")
        assert "TOPOLOGY{key, value}:" in output
        assert "NODES[" in output
        assert "type.dockerfile" in output


class TestTopologyCli:
    def test_topology_help_is_available(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_topology_default_toon_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", str(FIXTURES / "python_pkg")])
        assert result.exit_code == 0
        assert "TOPOLOGY{key, value}:" in result.output
        assert "dependency.fastapi" in result.output

    def test_topology_json_output(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", str(FIXTURES / "openapi3"), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["confidence"] == "full"
        assert any(edge["relation"] == "exposes" for edge in data["edges"])

    def test_topology_missing_path_exits_nonzero(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["topology", str(FIXTURES / "missing")])
        assert result.exit_code != 0
        assert "source does not exist" in result.output

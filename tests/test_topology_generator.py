"""Tests for testql.topology.generator — topology → TestPlan conversion."""

from __future__ import annotations

import pytest

from testql.ir.steps import ApiStep, GuiStep, ShellStep
from testql.topology.generator import NodeMappingConfig, TopologyScenarioGenerator
from testql.topology.models import (
    Condition,
    TopologyEdge,
    TopologyManifest,
    TopologyNode,
    TraversalTrace,
)
from testql.discovery.source import ArtifactSource


def _manifest() -> TopologyManifest:
    root = ArtifactSource(location="/tmp/project", kind="dir")
    nodes = [
        TopologyNode("artifact.root", "artifact", root),
        TopologyNode("interface.rest.1", "interface", "http://localhost:8000/api", metadata={"type": "rest"}),
        TopologyNode("page.root", "page", "http://localhost:8000/", metadata={"url": "http://localhost:8000/"}),
        TopologyNode("link.1", "link", "http://localhost:8000/about", metadata={"kind": "internal"}),
        TopologyNode("form.1", "form", "http://localhost:8000/contact", metadata={"action": "/contact", "method": "POST"}),
        TopologyNode("dependency.fastapi", "dependency", "fastapi", metadata={"name": "fastapi", "version": "0.100"}),
        TopologyNode("evidence.1", "evidence", "/tmp/project/app.py", metadata={"probe": "file", "kind": "py"}),
    ]
    edges = [
        TopologyEdge("artifact.root", "interface.rest.1", "exposes", "http"),
        TopologyEdge("artifact.root", "page.root", "renders", "browser"),
        TopologyEdge("page.root", "link.1", "links_to", "http", conditions=[Condition("kind", "internal")]),
        TopologyEdge("page.root", "form.1", "submits_to", "http", conditions=[Condition("method", "POST")]),
        TopologyEdge("artifact.root", "dependency.fastapi", "depends_on", "package", conditions=[Condition("scope", "runtime")]),
        TopologyEdge("artifact.root", "evidence.1", "supported_by", "file"),
    ]
    trace = TraversalTrace(
        id="trace.test",
        node_ids=["artifact.root", "interface.rest.1", "page.root", "link.1", "form.1", "dependency.fastapi", "evidence.1"],
        edge_ids=[f"{e.source_id}->{e.target_id}:{e.relation}" for e in edges],
    )
    return TopologyManifest(
        root=root,
        nodes=nodes,
        edges=edges,
        traces=[trace],
    )


class TestNodeToStepMapping:
    def test_interface_http_becomes_api_step(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("interface.rest.1")
        step = gen._node_to_step(node)
        assert isinstance(step, ApiStep)
        assert step.method == "GET"
        assert step.path == "http://localhost:8000/api"
        assert step.expect_status == 200

    def test_page_becomes_gui_navigate(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("page.root")
        step = gen._node_to_step(node)
        assert isinstance(step, GuiStep)
        assert step.action == "navigate"
        assert step.path == "http://localhost:8000/"

    def test_link_becomes_api_get(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("link.1")
        step = gen._node_to_step(node)
        assert isinstance(step, ApiStep)
        assert step.method == "GET"

    def test_form_post_becomes_api_post(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("form.1")
        step = gen._node_to_step(node)
        assert isinstance(step, ApiStep)
        assert step.method == "POST"
        assert step.path == "/contact"
        assert step.expect_status == 200

    def test_dependency_becomes_shell_step(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("dependency.fastapi")
        step = gen._node_to_step(node)
        assert isinstance(step, ShellStep)
        assert "fastapi" in step.command
        assert step.expect_exit_code == 0

    def test_evidence_becomes_shell_file_check(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = topo.node("evidence.1")
        step = gen._node_to_step(node)
        assert isinstance(step, ShellStep)
        assert "test -f" in step.command
        assert step.expect_exit_code == 0

    def test_unsupported_node_returns_none(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        node = TopologyNode("type.unknown", "artifact_type", "somewhere")
        assert gen._node_to_step(node) is None


class TestFromTrace:
    def test_trace_produces_plan_with_steps(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        plan = gen.from_trace(topo.traces[0])
        assert plan.name == "topology-trace.test"
        assert plan.type == "integration"
        kinds = [s.kind for s in plan.steps]
        assert "api" in kinds
        assert "gui" in kinds
        assert "shell" in kinds

    def test_plan_skips_missing_nodes(self):
        topo = _manifest()
        trace = TraversalTrace(id="bad", node_ids=["does.not.exist", "interface.rest.1"])
        gen = TopologyScenarioGenerator(topo)
        plan = gen.from_trace(trace)
        assert len(plan.steps) == 1
        assert plan.steps[0].kind == "api"

    def test_assertions_from_edge_conditions(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        plan = gen.from_trace(topo.traces[0])
        # page.root has outgoing edges with conditions → assertions on its step
        page_step = next(s for s in plan.steps if s.name == "page.root")
        assert any(a.field == "method" and a.expected == "POST" for a in page_step.asserts)


class TestToTesttoon:
    def test_round_trip_contains_expected_sections(self):
        topo = _manifest()
        gen = TopologyScenarioGenerator(topo)
        plan = gen.from_trace(topo.traces[0])
        text = gen.to_testtoon(plan)
        assert "# SCENARIO:" in text
        assert "API" in text or "NAVIGATE" in text


class TestConfigOverride:
    def test_custom_http_method(self):
        topo = _manifest()
        cfg = NodeMappingConfig(http_method="POST")
        gen = TopologyScenarioGenerator(topo, config=cfg)
        node = topo.node("interface.rest.1")
        step = gen._node_to_step(node)
        assert isinstance(step, ApiStep)
        assert step.method == "POST"

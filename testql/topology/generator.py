"""testql.topology.generator — Convert topology paths into executable TestPlans.

Usage:
    from testql.topology import build_topology
    from testql.topology.generator import TopologyScenarioGenerator

    topo = build_topology("/path/to/project")
    gen = TopologyScenarioGenerator(topo)
    plan = gen.from_trace(topo.traces[0])
    toon_text = gen.to_testtoon(plan)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from testql.ir.assertions import Assertion
from testql.ir.plan import TestPlan
from testql.ir.steps import ApiStep, GraphqlStep, GuiStep, ShellStep, SqlStep, Step
from testql.ir.metadata import ScenarioMetadata
from testql.topology.models import (
    Condition,
    TopologyEdge,
    TopologyManifest,
    TopologyNode,
    TraversalTrace,
)


# ── Node → Step mapping ─────────────────────────────────────────────────────


@dataclass
class NodeMappingConfig:
    """Controls how topology nodes are mapped to IR steps."""

    http_method: str = "GET"
    graphql_operation: str = "query"
    shell_health_cmd: str = "echo OK"
    sql_dialect: str = "sqlite"
    default_timeout_ms: int = 5000


class TopologyScenarioGenerator:
    """Generate executable TestPlans from topology traversal traces."""

    def __init__(
        self,
        topology: TopologyManifest,
        config: NodeMappingConfig | None = None,
    ) -> None:
        self.topology = topology
        self.config = config or NodeMappingConfig()
        self._node_map = {node.id: node for node in topology.nodes}

    # ── Public API ────────────────────────────────────────────────────────

    def from_trace(self, trace: TraversalTrace) -> TestPlan:
        """Build a TestPlan that walks the nodes in *trace* in order."""
        steps: list[Step] = []
        step_nodes: list[str] = []
        for node_id in trace.node_ids:
            node = self._node_map.get(node_id)
            if node is None:
                continue
            step = self._node_to_step(node)
            if step is not None:
                steps.append(step)
                step_nodes.append(node_id)

        # Attach edge-derived assertions between consecutive steps
        steps = self._attach_assertions(steps, step_nodes)

        return TestPlan(
            metadata=ScenarioMetadata(
                name=f"topology-{trace.id}",
                type="integration",
                extra={"description": f"Auto-generated from topology trace {trace.id}"},
            ),
            steps=steps,
            config={"source_topology": self.topology.root.location},
        )

    def from_path(self, node_ids: list[str]) -> TestPlan:
        """Build a TestPlan from an explicit list of node IDs."""
        trace = TraversalTrace(
            id="manual.path",
            node_ids=node_ids,
            status="planned",
        )
        return self.from_trace(trace)

    def to_testtoon(self, plan: TestPlan) -> str:
        """Render a TestPlan as TestTOON text."""
        from testql.adapters.testtoon_adapter import render

        return render(plan)

    # ── Node → Step conversion ──────────────────────────────────────────

    def _node_to_step(self, node: TopologyNode) -> Step | None:
        kind = node.kind
        protocol = self._protocol_for_node(node)

        if kind == "interface":
            return self._interface_to_step(node, protocol)
        if kind == "page":
            return self._page_to_step(node)
        if kind == "link":
            return self._link_to_step(node)
        if kind == "form":
            return self._form_to_step(node)
        if kind == "asset":
            return self._asset_to_step(node)
        if kind == "dependency":
            return self._dependency_to_step(node)
        if kind == "evidence":
            return self._evidence_to_step(node)
        return None

    def _interface_to_step(self, node: TopologyNode, protocol: str | None) -> Step:
        location = self._location(node)
        name = node.metadata.get("name") or node.id

        if protocol == "graphql":
            return GraphqlStep(
                name=name,
                operation=self.config.graphql_operation,
                body=node.metadata.get("query", "{ __typename }"),
                endpoint=location,
            )

        if protocol in ("http", "https", "rest"):
            return ApiStep(
                name=name,
                method=node.metadata.get("method", self.config.http_method),
                path=location or "/",
                expect_status=node.metadata.get("expect_status", 200),
            )

        if protocol in ("browser", "web"):
            return GuiStep(
                name=name,
                action="navigate",
                path=location,
                wait_ms=self.config.default_timeout_ms,
            )

        return ShellStep(name=name, command=f"echo 'unhandled interface {protocol}'")

    def _page_to_step(self, node: TopologyNode) -> Step:
        return GuiStep(
            name=node.id,
            action="navigate",
            path=self._location(node) or "/",
            wait_ms=self.config.default_timeout_ms,
        )

    def _link_to_step(self, node: TopologyNode) -> Step:
        url = self._location(node)
        return ApiStep(name=node.id, method="GET", path=url or "/", expect_status=200)

    def _form_to_step(self, node: TopologyNode) -> Step:
        action = node.metadata.get("action", "")
        method = node.metadata.get("method", "POST").upper()
        if method == "GET":
            return ApiStep(name=node.id, method="GET", path=action or "/", expect_status=200)
        return ApiStep(name=node.id, method="POST", path=action or "/", expect_status=200)

    def _asset_to_step(self, node: TopologyNode) -> Step:
        url = self._location(node)
        return ApiStep(name=node.id, method="HEAD", path=url or "/", expect_status=200)

    def _dependency_to_step(self, node: TopologyNode) -> Step:
        name = node.metadata.get("name", node.id)
        return ShellStep(
            name=node.id,
            command=f"pip show {name} || npm list {name} || echo 'dependency {name} not found'",
            expect_exit_code=0,
        )

    def _evidence_to_step(self, node: TopologyNode) -> Step:
        loc = self._location(node)
        return ShellStep(
            name=node.id,
            command=f"test -f {loc}" if loc else "echo 'no evidence location'",
            expect_exit_code=0,
        )

    # ── Assertions from edges ───────────────────────────────────────────

    def _attach_assertions(self, steps: list[Step], step_nodes: list[str]) -> list[Step]:
        """Add assertions to steps based on outgoing edge conditions."""
        if not steps:
            return steps

        for idx, step in enumerate(steps):
            node_id = step_nodes[idx] if idx < len(step_nodes) else None
            if node_id is None:
                continue
            edges = self._outgoing_edges(node_id)
            for edge in edges:
                for condition in edge.conditions:
                    assertion = self._condition_to_assertion(condition)
                    if assertion is not None:
                        step.asserts.append(assertion)
        return steps

    def _outgoing_edges(self, node_id: str) -> list[TopologyEdge]:
        return [edge for edge in self.topology.edges if edge.source_id == node_id]

    @staticmethod
    def _condition_to_assertion(condition: Condition) -> Assertion | None:
        kind = condition.kind
        value = condition.value
        mapping = {
            "scope": ("status", "eq", value),
            "method": ("method", "eq", value),
            "status": ("status", "eq", value),
        }
        if kind in mapping:
            field, op, expected = mapping[kind]
            return Assertion(field=field, op=op, expected=expected)
        return None

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _location(node: TopologyNode) -> str:
        src = node.source
        if hasattr(src, "location"):
            return str(src.location)
        return str(src)

    @staticmethod
    def _protocol_for_node(node: TopologyNode) -> str | None:
        return node.metadata.get("protocol") or node.metadata.get("type")


__all__ = ["TopologyScenarioGenerator", "NodeMappingConfig"]

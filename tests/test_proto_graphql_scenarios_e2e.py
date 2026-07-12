"""End-to-end tests for the bundled `*.proto.testql.yaml` and
`*.graphql.testql.yaml` scenarios."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters import registry
from testql.ir import GraphqlStep, ProtoStep


def _plugin_adapter(name: str):
    """Contract adapters ship in `packages/<name>2testql` and register
    themselves through the `testql.plugins` entry point."""
    adapter = registry.get(name)
    if adapter is None:
        pytest.skip(f"{name}2testql plugin not installed")
    return adapter


def _graphql_adapter():
    return _plugin_adapter("graphql")


def _proto_adapter():
    return _plugin_adapter("proto")


SCENARIO_ROOT = Path(__file__).resolve().parents[1] / "testql-scenarios"
PROTO_DIR = SCENARIO_ROOT / "proto"
GRAPHQL_DIR = SCENARIO_ROOT / "graphql"


def _proto_scenarios() -> list[Path]:
    return sorted(PROTO_DIR.glob("*.proto.testql.yaml"))


def _graphql_scenarios() -> list[Path]:
    return sorted(GRAPHQL_DIR.glob("*.graphql.testql.yaml"))


@pytest.fixture(params=_proto_scenarios(), ids=lambda p: p.name)
def proto_scenario(request) -> Path:
    return request.param


@pytest.fixture(params=_graphql_scenarios(), ids=lambda p: p.name)
def graphql_scenario(request) -> Path:
    return request.param


class TestProtoScenarios:
    def test_dir_not_empty(self):
        assert _proto_scenarios()

    def test_parse(self, proto_scenario: Path):
        plan = _proto_adapter().parse(proto_scenario)
        assert plan.metadata.type == "proto"
        steps = [s for s in plan.steps if isinstance(s, ProtoStep)]
        assert steps

    def test_round_trip_step_count(self, proto_scenario: Path):
        adapter = _proto_adapter()
        plan1 = adapter.parse(proto_scenario)
        plan2 = adapter.parse(adapter.render(plan1))
        n1 = sum(1 for s in plan1.steps if isinstance(s, ProtoStep))
        n2 = sum(1 for s in plan2.steps if isinstance(s, ProtoStep))
        assert n1 == n2


class TestGraphQLScenarios:
    def test_dir_not_empty(self):
        assert _graphql_scenarios()

    def test_parse(self, graphql_scenario: Path):
        plan = _graphql_adapter().parse(graphql_scenario)
        assert plan.metadata.type == "graphql"
        steps = [s for s in plan.steps if isinstance(s, GraphqlStep)]
        assert steps

    def test_endpoint_propagated(self, graphql_scenario: Path):
        plan = _graphql_adapter().parse(graphql_scenario)
        endpoint = plan.config.get("endpoint")
        assert endpoint
        for s in plan.steps:
            if isinstance(s, GraphqlStep):
                assert s.endpoint == endpoint

    def test_round_trip_step_count(self, graphql_scenario: Path):
        adapter = _graphql_adapter()
        plan1 = adapter.parse(graphql_scenario)
        plan2 = adapter.parse(adapter.render(plan1))
        n1 = sum(1 for s in plan1.steps if isinstance(s, GraphqlStep))
        n2 = sum(1 for s in plan2.steps if isinstance(s, GraphqlStep))
        assert n1 == n2

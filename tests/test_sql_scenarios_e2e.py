"""End-to-end tests for the bundled `*.sql.testql.yaml` scenarios."""

from __future__ import annotations

from pathlib import Path

import pytest

from testql.adapters.sql import SqlDSLAdapter
from testql.ir import SqlStep, TestPlan


SCENARIO_DIR = Path(__file__).resolve().parents[1] / "testql-scenarios" / "sql"


def _scenarios() -> list[Path]:
    return sorted(SCENARIO_DIR.glob("*.sql.testql.yaml"))


@pytest.fixture(params=_scenarios(), ids=lambda p: p.name)
def scenario(request) -> Path:
    return request.param


class TestScenarios:
    def test_dir_not_empty(self):
        assert _scenarios()

    def test_parse_succeeds(self, scenario: Path):
        plan = SqlDSLAdapter().parse(scenario)
        assert isinstance(plan, TestPlan)
        assert plan.metadata.name
        assert plan.metadata.type == "sql"
        assert plan.metadata.extra.get("dialect")

    def test_has_sql_steps(self, scenario: Path):
        plan = SqlDSLAdapter().parse(scenario)
        sql_steps = [s for s in plan.steps if isinstance(s, SqlStep)]
        assert sql_steps, f"{scenario.name} has no SQL queries"

    def test_round_trip_preserves_step_count(self, scenario: Path):
        adapter = SqlDSLAdapter()
        plan1 = adapter.parse(scenario)
        rendered = adapter.render(plan1)
        plan2 = adapter.parse(rendered)
        n1 = sum(1 for s in plan1.steps if isinstance(s, SqlStep))
        n2 = sum(1 for s in plan2.steps if isinstance(s, SqlStep))
        assert n1 == n2

    def test_dialect_propagates_to_steps(self, scenario: Path):
        plan = SqlDSLAdapter().parse(scenario)
        dialect = plan.metadata.extra["dialect"]
        for s in plan.steps:
            if isinstance(s, SqlStep):
                assert s.dialect == dialect


class TestSpecificScenarios:
    def test_users_contract_postgres(self):
        plan = SqlDSLAdapter().parse(SCENARIO_DIR / "users-contract.sql.testql.yaml")
        assert plan.metadata.extra["dialect"] == "postgres"
        sql_names = [s.name for s in plan.steps if isinstance(s, SqlStep)]
        assert "count_users" in sql_names
        assert "active_users" in sql_names

    def test_orders_sqlite(self):
        plan = SqlDSLAdapter().parse(SCENARIO_DIR / "orders-sqlite.sql.testql.yaml")
        assert plan.metadata.extra["dialect"] == "sqlite"
        sql_names = [s.name for s in plan.steps if isinstance(s, SqlStep)]
        assert {"total_orders", "by_user", "recent"} <= set(sql_names)

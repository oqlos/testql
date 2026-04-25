"""TestPlan — the root of the Unified Intermediate Representation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .fixtures import Fixture
from .metadata import ScenarioMetadata
from .steps import Step


@dataclass
class TestPlan:
    """Adapter-neutral representation of a single test scenario.

    All DSL adapters (TestTOON, NL, SQL, Proto, GraphQL, ...) parse their input
    into a `TestPlan`; all executors consume `TestPlan`s. Adapters can also
    *render* a `TestPlan` back into their own DSL (round-trip / generation).
    """

    metadata: ScenarioMetadata = field(default_factory=ScenarioMetadata)
    fixtures: list[Fixture] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metadata": self.metadata.to_dict(),
            "config": dict(self.config),
            "fixtures": [f.to_dict() for f in self.fixtures],
            "steps": [s.to_dict() for s in self.steps],
        }

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def type(self) -> str:
        return self.metadata.type

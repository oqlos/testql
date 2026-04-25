"""testql.ir — Unified Intermediate Representation for all DSL adapters.

Every DSL adapter parses its source into a `TestPlan`; every executor consumes
`TestPlan` instances. This package contains *only* dataclasses — no I/O, no
parsing, no execution.

See `articles/testql-multi-dsl-refactor-plan.md` (Phase 0) for design rationale.
"""

from __future__ import annotations

from .assertions import Assertion
from .fixtures import Fixture
from .metadata import ScenarioMetadata
from .plan import TestPlan
from .steps import (
    ApiStep,
    EncoderStep,
    GraphqlStep,
    GuiStep,
    NlStep,
    ProtoStep,
    ShellStep,
    SqlStep,
    Step,
    UnitStep,
)

__all__ = [
    "Assertion",
    "Fixture",
    "ScenarioMetadata",
    "TestPlan",
    "Step",
    "ApiStep",
    "GuiStep",
    "EncoderStep",
    "ShellStep",
    "UnitStep",
    "NlStep",
    "SqlStep",
    "ProtoStep",
    "GraphqlStep",
]

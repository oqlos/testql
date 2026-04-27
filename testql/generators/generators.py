"""Test generation mixins for different test types.

This module provides specialized generators for:
- API tests (smoke tests, integration tests)
- Tests derived from existing Python tests
- Tests derived from OQL/CQL scenarios
- CLI, library, frontend, and hardware tests

DEPRECATED: This module now re-exports mixins from split files for backward compatibility.
Import directly from:
- api_generator: APIGeneratorMixin
- pytest_generator: PythonTestGeneratorMixin
- scenario_generator: ScenarioGeneratorMixin
- specialized_generator: SpecializedGeneratorMixin
"""

from __future__ import annotations

from .api_generator import APIGeneratorMixin
from .pytest_generator import PythonTestGeneratorMixin
from .scenario_generator import ScenarioGeneratorMixin
from .specialized_generator import SpecializedGeneratorMixin


__all__ = [
    'APIGeneratorMixin',
    'PythonTestGeneratorMixin',
    'ScenarioGeneratorMixin',
    'SpecializedGeneratorMixin',
]

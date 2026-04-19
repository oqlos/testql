"""TestQL Generators — Automated test generation from project structures.

This package provides intelligent test generation capabilities:
- Base classes and data models
- Project analysis (structure, tests, config, routes, scenarios)
- API test generation (smoke tests, integration tests)
- Specialized generators (CLI, lib, frontend, hardware)
- Multi-project workspace support

Quickstart:
    from testql.generators import TestGenerator, generate_for_project
    
    # Generate tests for a single project
    generated = generate_for_project("/path/to/project")
    
    # Or use the class interface for more control
    generator = TestGenerator("/path/to/project")
    generator.analyze()
    files = generator.generate_tests("./output")
"""

from .base import TestPattern, ProjectProfile, BaseAnalyzer
from .analyzers import ProjectAnalyzer
from .generators import (
    APIGeneratorMixin,
    PythonTestGeneratorMixin,
    ScenarioGeneratorMixin,
    SpecializedGeneratorMixin,
)
from .multi import MultiProjectTestGenerator
from .test_generator import TestGenerator
from .convenience import generate_for_project, generate_for_workspace

__all__ = [
    # Data classes
    "TestPattern",
    "ProjectProfile",
    # Base classes
    "BaseAnalyzer",
    "ProjectAnalyzer",
    # Generator mixins
    "APIGeneratorMixin",
    "PythonTestGeneratorMixin",
    "ScenarioGeneratorMixin",
    "SpecializedGeneratorMixin",
    # Main classes
    "TestGenerator",
    "MultiProjectTestGenerator",
    # Convenience functions
    "generate_for_project",
    "generate_for_workspace",
]

"""TestQL Generator — Backward-compatible re-export.

This module re-exports all generator functionality from the new
structured generators package for backward compatibility.

New code should import directly from `testql.generators`:
    from testql.generators import TestGenerator, generate_for_project

Legacy imports still work:
    from testql.generator import TestGenerator, generate_for_project
"""

# Re-export everything from the new structured package
from .generators import (
    # Data classes
    TestPattern,
    ProjectProfile,
    # Base classes
    BaseAnalyzer,
    ProjectAnalyzer,
    # Generator mixins
    APIGeneratorMixin,
    PythonTestGeneratorMixin,
    ScenarioGeneratorMixin,
    SpecializedGeneratorMixin,
    # Main classes
    TestGenerator,
    MultiProjectTestGenerator,
    # Convenience functions
    generate_for_project,
    generate_for_workspace,
)

__all__ = [
    "TestPattern",
    "ProjectProfile",
    "BaseAnalyzer",
    "ProjectAnalyzer",
    "APIGeneratorMixin",
    "PythonTestGeneratorMixin",
    "ScenarioGeneratorMixin",
    "SpecializedGeneratorMixin",
    "TestGenerator",
    "MultiProjectTestGenerator",
    "generate_for_project",
    "generate_for_workspace",
]


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "."

    print(f"Generating tests for: {path}")
    generated = generate_for_project(path)
    print(f"Generated {len(generated)} test files:")
    for f in generated:
        print(f"  - {f}")

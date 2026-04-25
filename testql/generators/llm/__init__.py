"""testql.generators.llm — optional LLM enrichment of generated `TestPlan`s.

Phase 4 ships pluggable no-op enrichers; production wiring (via `costs` /
`pfix`) belongs in a higher layer. The pipeline always honours `--no-llm` by
not invoking any enricher.
"""

from __future__ import annotations

from .coverage_optimizer import CoverageOptimizer, NoOpCoverageOptimizer
from .edge_case_generator import EdgeCaseGenerator, NoOpEdgeCaseGenerator

__all__ = [
    "EdgeCaseGenerator", "NoOpEdgeCaseGenerator",
    "CoverageOptimizer", "NoOpCoverageOptimizer",
]

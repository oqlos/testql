"""IR-pipeline orchestration: source → IR → (LLM?) → target.

Public entry-points are intentionally tiny so per-stage CC stays low and the
pipeline is easy to call from CLI or programmatic clients.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from testql.ir import TestPlan

from .llm.coverage_optimizer import CoverageOptimizer, NoOpCoverageOptimizer
from .llm.edge_case_generator import EdgeCaseGenerator, NoOpEdgeCaseGenerator
from .sources import BaseSource, SourceLike, get_source
from .targets import BaseTarget, get_target


@dataclass
class PipelineResult:
    plan: TestPlan
    output: str
    source_name: str
    target_name: str


def _resolve_source(spec: BaseSource | str) -> BaseSource:
    if isinstance(spec, BaseSource):
        return spec
    src = get_source(spec)
    if src is None:
        raise ValueError(f"unknown source {spec!r}; available: {sorted_sources()}")
    return src


def _resolve_target(spec: BaseTarget | str) -> BaseTarget:
    if isinstance(spec, BaseTarget):
        return spec
    tgt = get_target(spec)
    if tgt is None:
        raise ValueError(f"unknown target {spec!r}; available: {sorted_targets()}")
    return tgt


def sorted_sources() -> list[str]:
    from .sources import available_sources
    return available_sources()


def sorted_targets() -> list[str]:
    from .targets import available_targets
    return available_targets()


def run(
    *,
    source: BaseSource | str,
    target: BaseTarget | str,
    artifact: SourceLike,
    edge_case_generator: Optional[EdgeCaseGenerator] = None,
    coverage_optimizer: Optional[CoverageOptimizer] = None,
) -> PipelineResult:
    """End-to-end run: load `artifact` via `source`, optionally enrich, render via `target`."""
    src = _resolve_source(source)
    tgt = _resolve_target(target)
    plan = src.load(artifact)
    plan = (edge_case_generator or NoOpEdgeCaseGenerator()).enrich(plan)
    # CoverageOptimizer is read-only — its report is exposed via TestPlan.metadata.extra.
    report = (coverage_optimizer or NoOpCoverageOptimizer()).analyse(plan)
    if report.missing or report.suggestions:
        plan.metadata.extra.setdefault("coverage", {}).update({  # type: ignore[union-attr]
            "missing": list(report.missing),
            "suggestions": list(report.suggestions),
        })
    return PipelineResult(plan=plan, output=tgt.render(plan),
                          source_name=src.name, target_name=tgt.name)


def write(result: PipelineResult, out: str | Path) -> Path:
    """Write `result.output` to `out`. If `out` is a directory, derive the filename."""
    p = Path(out)
    if p.is_dir() or str(out).endswith("/"):
        from .targets import get_target
        tgt = get_target(result.target_name)
        ext = tgt.file_extension if tgt else ".txt"
        slug = (result.plan.metadata.name or "scenario").replace(" ", "-").lower()
        p = p / f"{slug}{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(result.output, encoding="utf-8")
    return p


__all__ = ["PipelineResult", "run", "write", "sorted_sources", "sorted_targets"]

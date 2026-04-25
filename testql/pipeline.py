"""testql.pipeline — Project analysis → test generation pipeline.

Mirrors the SUMD RenderPipeline pattern: collect → build → emit.
Wraps the existing TestGenerator so all discovery logic is preserved while
providing a clean, single-call entry-point for the CLI and programmatic
callers.

Example:
    from testql.pipeline import GenerationPipeline

    pipeline = GenerationPipeline("/path/to/project")
    files = pipeline.run(output_dir="./out", analyze_only=False)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testql.generators import MultiProjectTestGenerator, TestGenerator


# ── Pipeline context ────────────────────────────────────────────────────────


@dataclass
class GenerationContext:
    """Data collected during the _collect phase."""

    project_path: Path
    is_workspace: bool = False
    profile: Any = None  # ProjectProfile (duck-typed to avoid circular import)
    workspace_profiles: dict[str, Any] = field(default_factory=dict)


# ── Pipeline ─────────────────────────────────────────────────────────────────


class GenerationPipeline:
    """Orchestrate project analysis and scenario generation.

    Usage:
        pipeline = GenerationPipeline("/path/to/project")
        files = pipeline.run(output_dir="./scenarios")
    """

    def __init__(self, project_path: str | Path) -> None:
        self.project_path = Path(project_path).resolve()

    # ── Phase 1: collect ──────────────────────────────────────────────

    def _collect(self) -> GenerationContext:
        """Detect workspace vs. single project and run analysis."""
        is_workspace = self._is_workspace(self.project_path)
        ctx = GenerationContext(
            project_path=self.project_path,
            is_workspace=is_workspace,
        )
        if is_workspace:
            gen = MultiProjectTestGenerator(self.project_path)
            ctx.workspace_profiles = gen.analyze_all()
        else:
            gen = TestGenerator(self.project_path)
            ctx.profile = gen.analyze()
        return ctx

    # ── Phase 2: build / emit ───────────────────────────────────────────

    def _emit(self, ctx: GenerationContext, output_dir: Path | None) -> list[Path]:
        """Generate scenario files from the collected context."""
        if ctx.is_workspace:
            return self._emit_workspace(ctx, output_dir)
        return self._emit_single(ctx, output_dir)

    def _emit_workspace(self, ctx: GenerationContext, output_dir: Path | None) -> list[Path]:
        gen = MultiProjectTestGenerator(ctx.project_path)
        # Re-populate internal state with already-collected profiles
        gen.project_profiles = ctx.workspace_profiles
        results = gen.generate_all()
        files: list[Path] = []
        for project_files in results.values():
            files.extend(project_files)
        # Cross-project tests
        cross_dir = output_dir or (ctx.project_path / "testql-scenarios")
        cross_file = gen.generate_cross_project_tests(cross_dir)
        if cross_file:
            files.append(cross_file)
        return files

    def _emit_single(self, ctx: GenerationContext, output_dir: Path | None) -> list[Path]:
        gen = TestGenerator(ctx.project_path)
        # Re-populate internal state with already-collected profile
        gen.profile = ctx.profile
        return gen.generate_tests(output_dir)

    # ── Public API ──────────────────────────────────────────────────────

    def run(
        self,
        *,
        output_dir: str | Path | None = None,
        analyze_only: bool = False,
    ) -> list[Path]:
        """Run the full pipeline.

        Args:
            output_dir: Directory for generated files. Defaults to
                       project_path / 'testql-scenarios' for single projects.
            analyze_only: If True, only analyze and return an empty list.

        Returns:
            List of paths to generated scenario files.
        """
        ctx = self._collect()
        if analyze_only:
            return []
        out = Path(output_dir) if output_dir else None
        return self._emit(ctx, out)

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _is_workspace(target_path: Path) -> bool:
        """True when target_path is a monorepo workspace, not a single project."""
        if (target_path / "pyproject.toml").exists() or (target_path / "setup.py").exists():
            return False
        workspace_dirs = ["doql", "oql", "oqlos", "testql", "weboql", "www"]
        return any(
            (target_path / d).exists() and not (target_path / d / "__init__.py").exists()
            for d in workspace_dirs
        )


__all__ = ["GenerationPipeline", "GenerationContext"]

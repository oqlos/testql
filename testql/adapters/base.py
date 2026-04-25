"""BaseDSLAdapter — the abstract contract every DSL adapter implements.

Every adapter (TestTOON, NL, SQL, Proto, GraphQL, ...) implements this
interface so the rest of TestQL can treat them uniformly. See
`articles/testql-multi-dsl-refactor-plan.md` (Phase 0) for the full design.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

from testql.ir import TestPlan

SourceLike = Union[str, Path]


@dataclass(frozen=True)
class DSLDetectionResult:
    """Outcome of `BaseDSLAdapter.detect()`.

    Attributes:
        matches: Whether the adapter recognises the source as its DSL.
        confidence: 0.0 — 1.0 score (higher = stronger match).
        reason: Human-readable explanation (e.g. "extension matches").
    """

    matches: bool
    confidence: float = 0.0
    reason: str = ""


@dataclass
class ValidationIssue:
    """Single validation issue produced by `BaseDSLAdapter.validate()`."""

    severity: str  # "error" | "warning" | "info"
    message: str
    location: Optional[str] = None  # e.g. "section[2].row[3]"
    code: Optional[str] = None      # machine-readable identifier


@dataclass
class BaseDSLAdapter(ABC):
    """Adapter contract.

    Subclasses MUST set `name` and `file_extensions` and implement
    `detect`, `parse` and `render`. `validate` defaults to no-op.
    """

    name: str = ""
    file_extensions: tuple[str, ...] = field(default_factory=tuple)
    mime_types: tuple[str, ...] = field(default_factory=tuple)

    # ── Detection ────────────────────────────────────────────────────────────

    @abstractmethod
    def detect(self, source: SourceLike) -> DSLDetectionResult:
        """Return whether `source` looks like this adapter's DSL.

        `source` may be a `Path` (file on disk) or a `str` (raw content). Adapters
        should accept both — use `_read_source` from this module as a helper.
        """

    # ── Parse / render ───────────────────────────────────────────────────────

    @abstractmethod
    def parse(self, source: SourceLike) -> TestPlan:
        """Parse `source` into a Unified IR `TestPlan`."""

    @abstractmethod
    def render(self, plan: TestPlan) -> str:
        """Render a `TestPlan` back into this adapter's DSL (round-trip)."""

    # ── Validation (optional) ────────────────────────────────────────────────

    def validate(self, plan: TestPlan) -> list[ValidationIssue]:
        """Static validation of a plan. Default: no issues."""
        return []


def read_source(source: SourceLike) -> tuple[str, str]:
    """Normalise a `SourceLike` into `(text, filename)`.

    Path-like inputs are read from disk; strings are passed through. The
    second element is the originating filename (or "<string>" when unknown).
    """

    if isinstance(source, Path):
        return source.read_text(encoding="utf-8"), str(source)
    if isinstance(source, str) and ("\n" not in source) and Path(source).is_file():
        # Treat a single-line string that points to an existing file as a path.
        p = Path(source)
        return p.read_text(encoding="utf-8"), str(p)
    return source, "<string>"

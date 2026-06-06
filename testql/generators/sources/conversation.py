"""Conversation scenario source → Unified IR TestPlan."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from testql.adapters.nlp2dsl import Nlp2DslAdapter
from testql.adapters.testtoon_adapter import TestToonAdapter
from testql.ir import TestPlan

from .base import BaseSource, SourceLike


@dataclass
class ConversationTestSource(BaseSource):
    """Load `.testql.toon.yaml` conversation scenarios into TestPlan IR."""

    name: str = "conversation"
    file_extensions: tuple[str, ...] = field(
        default_factory=lambda: (".conversation.testql.toon.yaml", ".testql.toon.yaml")
    )
    _toon: TestToonAdapter = field(default_factory=TestToonAdapter, repr=False)
    _nlp2dsl: Nlp2DslAdapter = field(default_factory=Nlp2DslAdapter, repr=False)

    def load(self, source: SourceLike) -> TestPlan:
        raw: SourceLike = str(source.get("text", "")) if isinstance(source, dict) else source
        plan = self._toon.parse(raw)
        if plan.metadata.type.lower() in {"conversation", "nlp2dsl", "dialog"}:
            return self._nlp2dsl.parse(raw)
        if isinstance(raw, (str, Path)):
            path = Path(raw)
            if path.exists() and "conversations" in path.parts:
                return self._nlp2dsl.parse(raw)
        return plan

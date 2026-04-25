"""Natural-language `.nl.md` source → TestPlan (delegates to `NLDSLAdapter`)."""

from __future__ import annotations

from dataclasses import dataclass, field

from testql.adapters.nl import NLDSLAdapter
from testql.ir import TestPlan

from .base import BaseSource, SourceLike


@dataclass
class NLSource(BaseSource):
    """Thin wrapper over `NLDSLAdapter.parse()`."""

    name: str = "nl"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".nl.md", ".nl.markdown"))

    def load(self, source: SourceLike) -> TestPlan:
        if isinstance(source, dict):
            text = str(source.get("text", ""))
            return NLDSLAdapter().parse(text)
        return NLDSLAdapter().parse(source)


__all__ = ["NLSource"]

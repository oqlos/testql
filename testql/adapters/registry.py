"""AdapterRegistry — singleton keeping track of registered DSL adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source


class AdapterRegistry:
    """In-process registry of `BaseDSLAdapter` instances.

    Adapters register themselves on import (or are registered explicitly).
    Lookup happens by name, by file extension, or by content sniffing.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, BaseDSLAdapter] = {}

    # ── Registration ─────────────────────────────────────────────────────────

    def register(self, adapter: BaseDSLAdapter) -> None:
        if not adapter.name:
            raise ValueError("Adapter must have a non-empty `name`.")
        self._by_name[adapter.name] = adapter

    def unregister(self, name: str) -> None:
        self._by_name.pop(name, None)

    def clear(self) -> None:
        self._by_name.clear()

    # ── Lookup ───────────────────────────────────────────────────────────────

    def get(self, name: str) -> Optional[BaseDSLAdapter]:
        return self._by_name.get(name)

    def all(self) -> list[BaseDSLAdapter]:
        return list(self._by_name.values())

    def by_extension(self, path: SourceLike) -> Optional[BaseDSLAdapter]:
        s = str(path).lower()
        # Iterate adapters preferring the longest extension match (so
        # ".testql.toon.yaml" beats a generic ".yaml").
        candidates: list[tuple[int, BaseDSLAdapter]] = []
        for adapter in self._by_name.values():
            for ext in adapter.file_extensions:
                if s.endswith(ext.lower()):
                    candidates.append((len(ext), adapter))
        if not candidates:
            return None
        candidates.sort(key=lambda kv: kv[0], reverse=True)
        return candidates[0][1]

    def detect(self, source: SourceLike) -> Optional[BaseDSLAdapter]:
        """Pick the highest-confidence adapter for `source`.

        Tries extension match first (cheap), then falls back to running each
        adapter's `detect()` on the raw text.
        """
        # 1) extension shortcut for path-like input
        if isinstance(source, Path) or (
            isinstance(source, str) and "\n" not in source and Path(source).is_file()
        ):
            ext_hit = self.by_extension(source)
            if ext_hit is not None:
                return ext_hit

        # 2) content sniffing
        text, _ = read_source(source)
        best: Optional[BaseDSLAdapter] = None
        best_score: float = 0.0
        for adapter in self._by_name.values():
            result: DSLDetectionResult = adapter.detect(text)
            if result.matches and result.confidence > best_score:
                best = adapter
                best_score = result.confidence
        return best


# Module-level singleton — usable as `from testql.adapters import registry`.
_registry = AdapterRegistry()


def get_registry() -> AdapterRegistry:
    return _registry

"""AdapterRegistry — singleton keeping track of registered DSL adapters."""

from __future__ import annotations

import importlib
import os
from importlib import metadata as importlib_metadata
from pathlib import Path
from types import ModuleType
from typing import Optional

from .base import BaseDSLAdapter, DSLDetectionResult, SourceLike, read_source


class AdapterRegistry:
    """In-process registry of `BaseDSLAdapter` instances.

    Adapters register themselves on import (or are registered explicitly).
    Lookup happens by name, by file extension, or by content sniffing.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, BaseDSLAdapter] = {}
        self._plugins_loaded = False

    # ── Registration ─────────────────────────────────────────────────────────

    def register(self, adapter: BaseDSLAdapter) -> None:
        if not adapter.name:
            raise ValueError("Adapter must have a non-empty `name`.")
        self._by_name[adapter.name] = adapter

    def register_plugin(self, plugin: object) -> None:
        if isinstance(plugin, BaseDSLAdapter):
            self.register(plugin)
            return
        if isinstance(plugin, (list, tuple, set)):
            for item in plugin:
                self.register_plugin(item)
            return
        hook = getattr(plugin, "register_testql_plugin", None) or getattr(plugin, "register", None)
        if callable(hook):
            result = hook(self)
            if result is not None:
                self.register_plugin(result)
            return
        adapters = getattr(plugin, "adapters", None)
        if adapters is not None:
            self.register_plugin(adapters)
            return
        adapter = getattr(plugin, "adapter", None)
        if adapter is not None:
            self.register_plugin(adapter)
            return
        raise TypeError(f"unsupported TestQL plugin object: {plugin!r}")

    def register_module(self, module_name: str) -> ModuleType:
        module = importlib.import_module(module_name)
        self.register_plugin(module)
        return module

    def load_plugins(
        self,
        *,
        entry_point_group: str = "testql.plugins",
        env_var: str = "TESTQL_PLUGIN_MODULES",
    ) -> list[str]:
        loaded: list[str] = []
        modules = [m.strip() for m in os.environ.get(env_var, "").split(",") if m.strip()]
        for module_name in modules:
            self.register_module(module_name)
            loaded.append(module_name)
        entry_points = importlib_metadata.entry_points()
        if hasattr(entry_points, "select"):
            selected = entry_points.select(group=entry_point_group)
        else:
            selected = entry_points.get(entry_point_group, [])
        for entry_point in selected:
            plugin = entry_point.load()
            self.register_plugin(plugin)
            loaded.append(entry_point.name)
        return loaded

    def ensure_plugins_loaded(self) -> list[str]:
        if self._plugins_loaded:
            return []
        loaded = self.load_plugins()
        self._plugins_loaded = True
        return loaded

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

"""Tests for plugin loading mechanisms in `AdapterRegistry`."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field

import pytest

from testql.adapters import (
    AdapterRegistry,
    BaseDSLAdapter,
    DSLDetectionResult,
    SourceLike,
    read_source,
)
from testql.ir import ScenarioMetadata, TestPlan


@dataclass
class _StubAdapter(BaseDSLAdapter):
    name: str = "stub"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".stub",))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, _ = read_source(source)
        return DSLDetectionResult(matches=text.startswith("STUB"), confidence=0.9)

    def parse(self, source: SourceLike) -> TestPlan:
        text, _ = read_source(source)
        return TestPlan(metadata=ScenarioMetadata(name=text.strip(), type="stub"))

    def render(self, plan: TestPlan) -> str:
        return f"STUB {plan.metadata.name}"


def _install_module(name: str, body: dict[str, object]) -> types.ModuleType:
    module = types.ModuleType(name)
    for key, value in body.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class TestRegisterPlugin:
    def test_register_adapter_instance(self) -> None:
        reg = AdapterRegistry()
        reg.register_plugin(_StubAdapter())
        assert reg.get("stub") is not None

    def test_register_iterable(self) -> None:
        reg = AdapterRegistry()
        reg.register_plugin([_StubAdapter(name="a"), _StubAdapter(name="b")])
        assert {a.name for a in reg.all()} == {"a", "b"}

    def test_register_module_with_register_hook(self) -> None:
        captured = {}

        def register(target: AdapterRegistry) -> _StubAdapter:
            captured["registry"] = target
            return _StubAdapter(name="hooked")

        module = _install_module("testql_test_plugin_hook", {"register_testql_plugin": register})
        try:
            reg = AdapterRegistry()
            reg.register_plugin(module)
            assert reg.get("hooked") is not None
            assert captured["registry"] is reg
        finally:
            sys.modules.pop(module.__name__, None)

    def test_register_module_with_adapters_attribute(self) -> None:
        module = _install_module(
            "testql_test_plugin_adapters",
            {"adapters": [_StubAdapter(name="from_attr")]},
        )
        try:
            reg = AdapterRegistry()
            reg.register_plugin(module)
            assert reg.get("from_attr") is not None
        finally:
            sys.modules.pop(module.__name__, None)

    def test_register_unsupported_raises(self) -> None:
        reg = AdapterRegistry()
        with pytest.raises(TypeError):
            reg.register_plugin(object())


class TestLoadPlugins:
    def test_env_var_loading(self, monkeypatch: pytest.MonkeyPatch) -> None:
        module = _install_module(
            "testql_test_plugin_env",
            {"adapter": _StubAdapter(name="env_loaded")},
        )
        monkeypatch.setenv("TESTQL_PLUGIN_MODULES", module.__name__)
        try:
            reg = AdapterRegistry()
            loaded = reg.load_plugins()
            assert module.__name__ in loaded
            assert reg.get("env_loaded") is not None
        finally:
            sys.modules.pop(module.__name__, None)

    def test_ensure_plugins_loaded_runs_once(self, monkeypatch: pytest.MonkeyPatch) -> None:
        reg = AdapterRegistry()
        calls = {"count": 0}

        def fake_load_plugins(**kwargs: object) -> list[str]:
            calls["count"] += 1
            return ["fake"]

        monkeypatch.setattr(reg, "load_plugins", fake_load_plugins)
        first = reg.ensure_plugins_loaded()
        second = reg.ensure_plugins_loaded()
        assert first == ["fake"]
        assert second == []
        assert calls["count"] == 1

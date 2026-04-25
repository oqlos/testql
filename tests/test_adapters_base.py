"""Tests for `testql.adapters` base classes and registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from testql.adapters import (
    AdapterRegistry,
    BaseDSLAdapter,
    DSLDetectionResult,
    SourceLike,
    ValidationIssue,
    get_registry,
    read_source,
    registry as default_registry,
)
from testql.ir import ScenarioMetadata, Step, TestPlan


@dataclass
class _DummyAdapter(BaseDSLAdapter):
    name: str = "dummy"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".dummy",))

    def detect(self, source: SourceLike) -> DSLDetectionResult:
        text, _ = read_source(source)
        return DSLDetectionResult(matches=text.startswith("DUMMY"), confidence=0.5)

    def parse(self, source: SourceLike) -> TestPlan:
        text, _ = read_source(source)
        return TestPlan(metadata=ScenarioMetadata(name=text.strip(), type="dummy"))

    def render(self, plan: TestPlan) -> str:
        return f"DUMMY {plan.metadata.name}"


class TestDSLDetectionResult:
    def test_defaults(self):
        r = DSLDetectionResult(matches=False)
        assert r.matches is False
        assert r.confidence == 0.0
        assert r.reason == ""


class TestValidationIssue:
    def test_minimal(self):
        v = ValidationIssue(severity="error", message="bad")
        assert v.severity == "error"
        assert v.location is None


class TestReadSource:
    def test_string_passthrough(self):
        text, name = read_source("DUMMY x")
        assert text == "DUMMY x"
        assert name == "<string>"

    def test_path_reads_file(self, tmp_path: Path):
        p = tmp_path / "x.txt"
        p.write_text("hello", encoding="utf-8")
        text, name = read_source(p)
        assert text == "hello"
        assert name == str(p)

    def test_string_pointing_to_file(self, tmp_path: Path):
        p = tmp_path / "x.txt"
        p.write_text("hello", encoding="utf-8")
        text, name = read_source(str(p))
        assert text == "hello"
        assert name == str(p)


class TestAdapterRegistry:
    def test_register_and_get(self):
        reg = AdapterRegistry()
        a = _DummyAdapter()
        reg.register(a)
        assert reg.get("dummy") is a
        assert reg.all() == [a]

    def test_register_requires_name(self):
        reg = AdapterRegistry()
        bad = _DummyAdapter(name="")
        with pytest.raises(ValueError):
            reg.register(bad)

    def test_unregister_and_clear(self):
        reg = AdapterRegistry()
        reg.register(_DummyAdapter())
        reg.unregister("dummy")
        assert reg.get("dummy") is None
        reg.register(_DummyAdapter())
        reg.clear()
        assert reg.all() == []

    def test_by_extension(self, tmp_path: Path):
        reg = AdapterRegistry()
        reg.register(_DummyAdapter())
        p = tmp_path / "x.dummy"
        p.write_text("DUMMY", encoding="utf-8")
        hit = reg.by_extension(p)
        assert hit is not None
        assert hit.name == "dummy"

    def test_by_extension_prefers_longest_match(self):
        @dataclass
        class A1(BaseDSLAdapter):
            name: str = "a1"
            file_extensions: tuple[str, ...] = field(default_factory=lambda: (".yaml",))
            def detect(self, source): return DSLDetectionResult(matches=False)
            def parse(self, source): return TestPlan()
            def render(self, plan): return ""

        @dataclass
        class A2(BaseDSLAdapter):
            name: str = "a2"
            file_extensions: tuple[str, ...] = field(default_factory=lambda: (".testql.yaml",))
            def detect(self, source): return DSLDetectionResult(matches=False)
            def parse(self, source): return TestPlan()
            def render(self, plan): return ""

        reg = AdapterRegistry()
        reg.register(A1())
        reg.register(A2())
        hit = reg.by_extension(Path("x.testql.yaml"))
        assert hit is not None
        assert hit.name == "a2"

    def test_detect_falls_back_to_content(self):
        reg = AdapterRegistry()
        reg.register(_DummyAdapter())
        hit = reg.detect("DUMMY hello")
        assert hit is not None
        assert hit.name == "dummy"

    def test_detect_returns_none_when_no_match(self):
        reg = AdapterRegistry()
        reg.register(_DummyAdapter())
        assert reg.detect("nope") is None


class TestDefaultRegistry:
    def test_singleton(self):
        assert get_registry() is default_registry

    def test_testtoon_preregistered(self):
        a = default_registry.get("testtoon")
        assert a is not None
        assert "testtoon" in a.name


class TestBaseAdapterDefaultValidate:
    def test_validate_default_empty(self):
        a = _DummyAdapter()
        assert a.validate(TestPlan()) == []

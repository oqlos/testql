"""Regression tests for DESKTOP_ASSERT_ELEMENTS capture metadata fallback."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from testql.interpreter import OqlInterpreter
from testql.interpreter._parser import OqlLine

pytest.importorskip("desktop2testql", reason="desktop2testql plugin not installed")


def test_assert_elements_passes_on_mirrored_windows(monkeypatch, tmp_path) -> None:
    image = tmp_path / "shot.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    meta = tmp_path / "shot.png.vdisplay.json"
    meta.write_text('{"window_count": 2, "method": "vdisplay_mirror_virtual"}', encoding="utf-8")

    interpreter = OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=False)
    monkeypatch.setattr(
        interpreter,
        "_ensure_capture",
        lambda image_arg, default="": str(image),
    )
    monkeypatch.setattr(
        "desktop2testql.vision.analyze_layout",
        lambda path, **kw: {"ok": True, "element_count": 0, "window_count": 1},
    )

    line = OqlLine(
        number=1,
        command="DESKTOP_ASSERT_ELEMENTS",
        args='1 "shot.png"',
        raw='DESKTOP_ASSERT_ELEMENTS 1 "shot.png"',
    )
    interpreter._cmd_desktop_assert_elements(line.args, line)
    assert interpreter.results[-1].status.value == "passed"
    assert "mirrored_windows=2" in (interpreter.results[-1].message or "")


def test_assert_elements_fails_on_empty_capture(monkeypatch, tmp_path) -> None:
    image = tmp_path / "empty.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 64)
    meta = tmp_path / "empty.png.vdisplay.json"
    meta.write_text('{"window_count": 0, "scene_class": "flat_monochrome"}', encoding="utf-8")

    interpreter = OqlInterpreter(api_url="http://localhost:8101", quiet=True, dry_run=False)
    monkeypatch.setattr(
        interpreter,
        "_ensure_capture",
        lambda image_arg, default="": str(image),
    )
    monkeypatch.setattr(
        "desktop2testql.vision.analyze_layout",
        lambda path, **kw: {"ok": True, "element_count": 0, "window_count": 1},
    )
    interpreter.out = MagicMock()

    line = OqlLine(
        number=1,
        command="DESKTOP_ASSERT_ELEMENTS",
        args='1 "empty.png"',
        raw='DESKTOP_ASSERT_ELEMENTS 1 "empty.png"',
    )
    interpreter._cmd_desktop_assert_elements(line.args, line)
    assert interpreter.results[-1].status.value == "failed"
    assert "mirrored_windows=0" in (interpreter.results[-1].message or "")

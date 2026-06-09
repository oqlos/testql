"""Unit tests for desktop element assert helper."""

from __future__ import annotations

from testql.desktop.element_assert import evaluate_element_assert


def test_element_assert_passes_on_imgl_count() -> None:
    outcome = evaluate_element_assert(minimum=2, element_count=3, mirrored_windows=0)
    assert outcome.passed
    assert outcome.message == "elements=3"


def test_element_assert_passes_on_mirrored_windows() -> None:
    outcome = evaluate_element_assert(minimum=1, element_count=0, mirrored_windows=2)
    assert outcome.passed
    assert "mirrored_windows=2" in outcome.message


def test_element_assert_fails_on_empty_capture() -> None:
    outcome = evaluate_element_assert(minimum=1, element_count=0, mirrored_windows=0)
    assert not outcome.passed
    assert "mirrored_windows=0" in outcome.message

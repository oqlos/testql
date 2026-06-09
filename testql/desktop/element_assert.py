"""Helpers for DESKTOP_ASSERT_ELEMENTS evaluation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElementAssertOutcome:
    passed: bool
    status: str
    message: str
    step_text: str


def evaluate_element_assert(
    *,
    minimum: int,
    element_count: int,
    mirrored_windows: int,
) -> ElementAssertOutcome:
    if element_count >= minimum:
        return ElementAssertOutcome(
            passed=True,
            status="passed",
            message=f"elements={element_count}",
            step_text=f"DESKTOP_ASSERT_ELEMENTS {element_count} >= {minimum}",
        )

    if mirrored_windows >= minimum:
        return ElementAssertOutcome(
            passed=True,
            status="passed",
            message=f"elements={element_count} mirrored_windows={mirrored_windows}",
            step_text=(
                f"DESKTOP_ASSERT_ELEMENTS {element_count} imgl / "
                f"{mirrored_windows} mirrored >= {minimum}"
            ),
        )

    detail = f"elements={element_count}"
    if mirrored_windows == 0:
        detail += ", mirrored_windows=0 (empty monitor capture)"
    elif mirrored_windows < minimum:
        detail += f", mirrored_windows={mirrored_windows}"

    return ElementAssertOutcome(
        passed=False,
        status="failed",
        message=detail,
        step_text=f"DESKTOP_ASSERT_ELEMENTS {element_count} < {minimum}",
    )

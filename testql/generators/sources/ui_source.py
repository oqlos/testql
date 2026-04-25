"""UI source — placeholder.

The plan calls for a Playwright/LLM-driven generator that turns a live URL or
HTML snapshot into a `.nl.md`-equivalent `TestPlan`. Phase 4 ships a minimal
deterministic stub that extracts `<a>`, `<button>`, and form input names from
HTML and emits a smoke navigate-and-click scenario.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from testql.ir import Assertion, GuiStep, ScenarioMetadata, TestPlan

from .base import BaseSource, SourceLike


_LINK_RE = re.compile(r'<a[^>]*href="([^"]+)"', re.IGNORECASE)
_BUTTON_RE = re.compile(r'<button[^>]*>([^<]{1,40})</button>', re.IGNORECASE)
_INPUT_NAME_RE = re.compile(r'<input[^>]*name="([^"]+)"', re.IGNORECASE)


def _load_html(source: SourceLike) -> tuple[str, Optional[str]]:
    if isinstance(source, dict):
        return str(source.get("html", "")), source.get("url")
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8"), str(source)
    if "\n" not in source and Path(source).is_file():
        p = Path(source)
        return p.read_text(encoding="utf-8"), str(p)
    return source, None


def _navigate_step(url: Optional[str]) -> GuiStep:
    return GuiStep(action="navigate", path=url or "/", name="navigate")


def _input_steps(html: str) -> list[GuiStep]:
    return [
        GuiStep(action="input", selector=f"[name='{name}']",
                value=f"sample_{name}", name=f"input_{name}")
        for name in _INPUT_NAME_RE.findall(html)
    ]


def _button_steps(html: str) -> list[GuiStep]:
    return [
        GuiStep(action="click", selector=f"button:contains('{label.strip()}')",
                name=f"click_{label.strip()[:20]}")
        for label in _BUTTON_RE.findall(html)
    ]


@dataclass
class UISource(BaseSource):
    """HTML snapshot → smoke GUI scenario."""

    name: str = "ui"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".html", ".htm"))

    def load(self, source: SourceLike) -> TestPlan:
        html, url = _load_html(source)
        plan = TestPlan(metadata=ScenarioMetadata(
            name="UI smoke",
            type="gui",
            extra={"source": "ui"},
        ))
        plan.steps.append(_navigate_step(url))
        plan.steps.extend(_input_steps(html))
        plan.steps.extend(_button_steps(html))
        plan.steps.append(GuiStep(
            action="assert_visible", selector="body", name="visible_body",
            asserts=[Assertion(field="body", op="!=", expected=None)],
        ))
        return plan


__all__ = ["UISource"]

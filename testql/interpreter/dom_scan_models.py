"""DOM Scan data models.

This module provides dataclasses for DOM scanning results.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FocusableElement:
    index: int                      # TAB order position (1-based)
    role: str                       # ARIA role: button, link, textbox …
    name: str                       # accessible name (label / aria-label)
    selector: str                   # CSS selector or xpath hint
    tag: str                        # raw HTML tag
    tabindex: int | None            # explicit tabindex value or None
    disabled: bool = False
    expanded: bool | None = None    # for menus / accordions
    checked: bool | None = None     # for checkboxes / radios
    required: bool = False
    value: str | None = None        # current value for inputs
    description: str | None = None  # aria-description / title
    children_count: int = 0


@dataclass
class DomScanResult:
    url: str
    scan_type: str
    total: int
    elements: list[FocusableElement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)   # e.g. duplicate labels
    errors: list[str] = field(default_factory=list)     # broken ARIA


@dataclass
class ButtonAuditResult:
    selector: str
    name: str
    status: str  # "OK", "DEAD", "BROKEN", "SKIPPED"
    details: str


@dataclass
class ButtonAuditReport:
    url: str
    total_tested: int
    ok: int
    dead: int
    broken: int
    results: list[ButtonAuditResult] = field(default_factory=list)

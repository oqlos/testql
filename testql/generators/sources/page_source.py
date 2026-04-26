"""PageSource — drive a real browser (Playwright) and extract a TestPlan.

This is the live-page counterpart of :mod:`testql.generators.sources.ui_source`
(which only handles static HTML snapshots via regex). The browser-side logic
extracts an element descriptor list that is then handed to the pure
:mod:`testql.generators.page_analyzer` for plan construction.

Playwright is an optional dependency: if it isn't installed, instantiating a
:class:`PageSource` works, but :meth:`PageSource.load` raises a clear error.
The :func:`extract_elements_from_page` helper is also exported so callers
that already hold a Playwright ``Page`` (e.g. the heal command) can reuse the
extraction without re-launching a browser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from urllib.parse import urlparse

from testql.ir import TestPlan

from ..page_analyzer import PageSnapshot, snapshot_to_plan
from .base import BaseSource, SourceLike


# JavaScript executed inside the browser context. Returns a JSON-serialisable
# list of element descriptors compatible with page_analyzer.pick_selector.
_EXTRACT_JS = r"""
() => {
    const SELECTOR = (
        "a[href], button, input, select, textarea, " +
        "[role='button'], [role='link'], [role='menuitem'], " +
        "[role='tab'], [role='checkbox'], [role='radio'], " +
        "[role='switch'], h1, h2, h3, [data-testid], [data-test]"
    );
    const els = Array.from(document.querySelectorAll(SELECTOR));
    function isVisible(el) {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none') return false;
        return true;
    }
    function accessibleName(el) {
        return (
            el.getAttribute('aria-label') ||
            el.getAttribute('alt') ||
            el.getAttribute('title') ||
            (el.labels && el.labels[0] && el.labels[0].textContent.trim()) ||
            (el.textContent || '').trim().slice(0, 80)
        );
    }
    return els.map(el => ({
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute('role'),
        name: accessibleName(el),
        id: el.id || null,
        data_testid: el.getAttribute('data-testid'),
        data_test: el.getAttribute('data-test'),
        name_attr: el.getAttribute('name'),
        input_type: el.getAttribute('type'),
        aria_label: el.getAttribute('aria-label'),
        placeholder: el.getAttribute('placeholder'),
        href: el.getAttribute('href'),
        text: (el.textContent || '').trim().slice(0, 80),
        classes: Array.from(el.classList || []),
        disabled: el.disabled === true || el.getAttribute('aria-disabled') === 'true',
        visible: isVisible(el),
    }));
}
"""


def extract_elements_from_page(page: Any) -> list[dict[str, Any]]:
    """Run the extraction script against a Playwright ``Page`` instance.

    Kept as a free function so the heal command can call it without
    instantiating a :class:`PageSource`.
    """
    return page.evaluate(_EXTRACT_JS)


def _path_of(url: str) -> str:
    parsed = urlparse(url)
    return parsed.path or "/"


@dataclass
class PageSource(BaseSource):
    """Live-URL source: drive Playwright once, extract DOM, build TestPlan.

    Use :meth:`load` with a ``str`` URL or a ``dict`` of ``{"url": str}``.
    The dict form additionally accepts pre-extracted ``elements`` (skipping
    the browser entirely — useful for tests).
    """

    name: str = "page"
    file_extensions: tuple[str, ...] = field(default_factory=tuple)
    headless: bool = True
    timeout_ms: int = 30000
    wait_until: str = "networkidle"
    max_steps: int = 50

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, source: SourceLike) -> TestPlan:
        url, elements, title = self._resolve_source(source)
        snap = PageSnapshot(
            url=url,
            title=title,
            path=_path_of(url),
            elements=elements,
        )
        base_url = _origin(url)
        return snapshot_to_plan(snap, base_url=base_url, max_steps=self.max_steps)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_source(
        self, source: SourceLike,
    ) -> tuple[str, list[dict[str, Any]], str]:
        if isinstance(source, dict):
            url = str(source.get("url", ""))
            if not url:
                raise ValueError("PageSource: dict source must include 'url'")
            elements = source.get("elements")
            title = str(source.get("title", ""))
            if elements is not None:
                return url, list(elements), title
            return self._fetch_via_playwright(url, title)

        url = str(source)
        return self._fetch_via_playwright(url, "")

    def _fetch_via_playwright(
        self, url: str, title: str,
    ) -> tuple[str, list[dict[str, Any]], str]:
        try:
            from playwright.sync_api import sync_playwright  # noqa: WPS433
        except ImportError as exc:  # pragma: no cover - exercised only without playwright
            raise RuntimeError(
                "PageSource requires playwright. Install with: "
                "pip install playwright && playwright install chromium"
            ) from exc

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            try:
                page = browser.new_page()
                page.goto(url, wait_until=self.wait_until, timeout=self.timeout_ms)
                title = title or page.title()
                elements = extract_elements_from_page(page)
                # Resolve any redirects to capture the final URL/path
                final_url = page.url or url
            finally:
                browser.close()
        return final_url, elements, title


def _origin(url: str) -> Optional[str]:
    parsed = urlparse(url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return None


__all__ = ["PageSource", "extract_elements_from_page"]

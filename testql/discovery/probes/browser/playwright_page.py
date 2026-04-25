"""Playwright-backed web page probe for JS-rendered content."""

from __future__ import annotations

from typing import Any

try:
    from playwright.sync_api import sync_playwright
    _PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    sync_playwright = None  # type: ignore[assignment]
    _PLAYWRIGHT_AVAILABLE = False

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource, SourceKind


class PlaywrightPageProbe(BaseProbe):
    name = "browser.playwright_page"
    artifact_types = ("web_page", "browser_page")
    cost = "expensive"

    def __init__(self, timeout: float = 30.0, wait_until: str = "networkidle"):
        self.timeout = timeout
        self.wait_until = wait_until

    def applicable(self, source: ArtifactSource) -> bool:
        return source.kind == SourceKind.URL

    def probe(self, source: ArtifactSource) -> ProbeResult:
        if not _PLAYWRIGHT_AVAILABLE:
            exc = ImportError("playwright is not installed")
            return self.result(
                0,
                ["browser_page"],
                [self.evidence("browser_unavailable", source.location, str(exc))],
                {"url": source.location, "error": str(exc), "reachable": False},
            )

        console_errors: list[str] = []
        network_calls: list[dict[str, Any]] = []

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()

            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("request", lambda req: network_calls.append({"url": req.url, "method": req.method, "resource_type": req.resource_type}))

            try:
                response = page.goto(source.location, wait_until=self.wait_until, timeout=self.timeout * 1000)
            except Exception as exc:
                browser.close()
                return self.result(
                    35,
                    ["browser_page"],
                    [self.evidence("browser_error", source.location, str(exc))],
                    {"url": source.location, "error": str(exc), "reachable": False},
                )

            status_code = response.status if response else None
            final_url = page.url
            title = page.title()

            links = page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]')).map(a => ({
                    url: a.href,
                    text: a.textContent.trim(),
                }))
            """)
            assets = page.evaluate("""
                () => [
                    ...Array.from(document.querySelectorAll('script[src]')).map(el => ({url: el.src, tag: 'script'})),
                    ...Array.from(document.querySelectorAll('link[href]')).map(el => ({url: el.href, tag: 'link', rel: el.rel})),
                    ...Array.from(document.querySelectorAll('img[src]')).map(el => ({url: el.src, tag: 'img'})),
                ]
            """)
            forms = page.evaluate("""
                () => Array.from(document.querySelectorAll('form')).map(f => ({
                    action: f.action,
                    method: (f.method || 'get').toLowerCase(),
                }))
            """)

            browser.close()

        metadata = {
            "url": source.location,
            "final_url": final_url,
            "status_code": status_code,
            "title": title,
            "links": [{"url": l["url"], "text": l["text"], "kind": _link_kind(final_url, l["url"])} for l in links[:100]],
            "assets": [{"url": a["url"], "tag": a["tag"], "kind": _asset_kind(a)} for a in assets[:100]],
            "forms": forms[:25],
            "console_errors": console_errors[:50],
            "network_calls": [{"url": n["url"], "method": n["method"], "resource_type": n["resource_type"]} for n in network_calls[:200]],
            "page_schema": {
                "url": final_url,
                "status_code": status_code,
                "title": title,
                "links": links[:100],
                "assets": assets[:100],
                "forms": forms[:25],
                "console_errors": console_errors[:50],
                "network_calls": network_calls[:200],
            },
            "interfaces": [{"type": "browser_page", "location": final_url, "metadata": {"status_code": status_code, "title": title}}],
        }

        confidence = 95 if status_code and 200 <= status_code < 400 else 55
        evidence = [self.evidence("browser", source.location, f"Browser rendered {final_url} HTTP {status_code}")]
        return self.result(confidence, ["web_page", "browser_page"], evidence, metadata)

    def evidence(self, kind: str, location, detail: str = ""):
        from testql.discovery.manifest import Evidence
        return Evidence(self.name, kind, str(location), detail)


def _link_kind(base_url: str, href: str) -> str:
    from urllib.parse import urljoin, urlparse
    target = urljoin(base_url, href)
    base_host = urlparse(base_url).netloc
    target_host = urlparse(target).netloc
    if href.startswith("#"):
        return "anchor"
    if target_host and target_host != base_host:
        return "external"
    return "internal"


def _asset_kind(asset: dict[str, Any]) -> str:
    tag = asset.get("tag", "")
    rel = asset.get("rel", "")
    if tag == "script":
        return "script"
    if tag == "img":
        return "image"
    if tag == "link":
        rel_l = str(rel).lower()
        if "stylesheet" in rel_l:
            return "stylesheet"
        if "icon" in rel_l or "shortcut" in rel_l:
            return "icon"
        if "preload" in rel_l:
            return "preload"
        return "link"
    return "unknown"

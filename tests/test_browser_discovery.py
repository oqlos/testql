"""Mocked tests for PlaywrightPageProbe browser inspection."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from testql.discovery.source import ArtifactSource, SourceKind


class FakePlaywright:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    @property
    def chromium(self):
        return FakeBrowserLauncher()


class FakeBrowserLauncher:
    def launch(self, **kwargs):
        return FakeBrowser()


class FakeBrowser:
    def new_page(self):
        return FakePage()

    def close(self):
        pass


class FakePage:
    def __init__(self):
        self._listeners = {}
        self.url = "https://example.test/"

    def on(self, event, handler):
        self._listeners.setdefault(event, []).append(handler)

    def goto(self, url, wait_until=None, timeout=None):
        response = MagicMock()
        response.status = 200
        # Simulate console error listener
        for handler in self._listeners.get("console", []):
            msg = MagicMock()
            msg.type = "error"
            msg.text = "Test console error"
            handler(msg)
        # Simulate request listener
        for handler in self._listeners.get("request", []):
            req = MagicMock()
            req.url = "https://example.test/api"
            req.method = "GET"
            req.resource_type = "xhr"
            handler(req)
        return response

    def title(self):
        return "Test Page"

    def evaluate(self, script):
        if "a[href]" in script:
            return [{"url": "https://example.test/about", "text": "About"}]
        if "script[src]" in script:
            return [{"url": "https://example.test/app.js", "tag": "script"}]
        if "img[src]" in script:
            return []
        if "form" in script:
            return [{"action": "https://example.test/contact", "method": "post"}]
        return []


class FakePlaywrightImport:
    def sync_playwright(self):
        return FakePlaywright()


@pytest.fixture
def mock_playwright():
    """Mock playwright.sync_api before any imports happen."""
    sys.modules["playwright.sync_api"] = FakePlaywrightImport()
    # Remove the module from cache if it was already imported
    sys.modules.pop("testql.discovery.probes.browser.playwright_page", None)
    yield
    # Cleanup
    sys.modules.pop("playwright.sync_api", None)


def test_playwright_probe_collects_console_and_network(mock_playwright):
    # Import the probe after the fixture has set up the mock
    from testql.discovery.probes.browser.playwright_page import PlaywrightPageProbe
    probe = PlaywrightPageProbe()
    source = ArtifactSource("https://example.test/", SourceKind.URL)

    result = probe.probe(source)
    assert result.matched is True
    assert "browser_page" in result.artifact_types
    meta = result.metadata
    assert meta["title"] == "Test Page"
    assert meta["status_code"] == 200
    assert len(meta["console_errors"]) == 1
    assert meta["console_errors"][0] == "Test console error"
    assert len(meta["network_calls"]) == 1
    assert meta["network_calls"][0]["url"] == "https://example.test/api"

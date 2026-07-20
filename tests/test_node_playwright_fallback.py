"""Regression tests for the project-local Node Playwright fallback."""

from __future__ import annotations

from pathlib import Path
import sys

from testql.interpreter import _gui
from testql.interpreter import _node_playwright as node_playwright
from testql.interpreter._node_playwright import NodePlaywrightPage
from testql.interpreter.interpreter import OqlInterpreter


def _isolate_search_environment(monkeypatch, root: Path) -> None:
    monkeypatch.delenv("INIT_CWD", raising=False)
    monkeypatch.delenv("TESTQL_NODE_PLAYWRIGHT_PATH", raising=False)
    monkeypatch.delenv("TESTQL_PLAYWRIGHT_SEARCH_PATHS", raising=False)
    monkeypatch.setenv("PWD", str(root))
    monkeypatch.setattr(
        node_playwright.shutil,
        "which",
        lambda command: "/usr/bin/node" if command == "node" else None,
    )


def test_finds_calling_projects_node_playwright(tmp_path, monkeypatch):
    project = tmp_path / "project"
    nested = project / "tests" / "scenarios"
    package = project / "node_modules" / "playwright"
    nested.mkdir(parents=True)
    package.mkdir(parents=True)
    (package / "package.json").write_text('{"name":"playwright"}', encoding="utf-8")
    _isolate_search_environment(monkeypatch, nested)

    assert node_playwright.find_node_playwright(nested) == package


def test_explicit_node_playwright_path_has_priority(tmp_path, monkeypatch):
    package = tmp_path / "custom-playwright"
    package.mkdir()
    (package / "package.json").write_text('{"name":"playwright"}', encoding="utf-8")
    monkeypatch.setenv("TESTQL_NODE_PLAYWRIGHT_PATH", str(package))

    assert node_playwright.find_node_playwright(tmp_path) == package


def test_explicit_browser_executable_has_priority(tmp_path, monkeypatch):
    browser = tmp_path / "chrome"
    browser.write_text("#!/bin/sh\n", encoding="utf-8")
    browser.chmod(0o755)
    monkeypatch.setenv("TESTQL_BROWSER_EXECUTABLE", str(browser))

    assert node_playwright.find_browser_executable() == str(browser.resolve())


def test_gui_driver_uses_node_fallback_when_python_package_is_missing(tmp_path, monkeypatch):
    package = tmp_path / "node_modules" / "playwright"
    package.mkdir(parents=True)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)
    monkeypatch.setattr(_gui, "find_node_playwright", lambda: package)
    interpreter = OqlInterpreter(
        api_url="http://localhost:8101", quiet=True, dry_run=False
    )
    interpreter.vars.set("gui_driver", "playwright")

    assert interpreter._init_gui_driver() is True
    assert interpreter._gui_playwright_backend == "node"
    assert interpreter._gui_node_playwright_path == package
    assert interpreter._gui_engine_unavailable is False


def test_node_page_preserves_serialized_javascript_functions():
    calls = []

    class Session:
        def call(self, command, **args):
            calls.append((command, args))
            return None

    page = NodePlaywrightPage(Session())
    page.evaluate("async () => { return location.href; }")
    page.locator("form").evaluate("form => form.requestSubmit()")

    assert calls[0] == (
        "evaluate",
        {"expression": "async () => { return location.href; }"},
    )
    assert calls[1][0] == "locator_evaluate"
    assert calls[1][1]["expression"] == "form => form.requestSubmit()"

"""Synchronous Python facade for a project-local Node.js Playwright install."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


_PLAYWRIGHT_PACKAGES = ("playwright", "@playwright/test")
_BROWSER_ENV_VARS = (
    "TESTQL_BROWSER_EXECUTABLE",
    "PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH",
    "CHROME_BIN",
)
_BROWSER_COMMANDS = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
)
_BROWSER_PATHS = (
    "/opt/google/chrome/chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/microsoft-edge",
)


def _search_roots(start: Path | None = None) -> list[Path]:
    roots: list[Path] = []
    configured = os.environ.get("TESTQL_PLAYWRIGHT_SEARCH_PATHS", "")
    for item in configured.split(os.pathsep):
        if item.strip():
            roots.append(Path(item).expanduser())
    for env_name in ("INIT_CWD", "PWD"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value).expanduser())
    roots.append(start or Path.cwd())

    expanded: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        root = root.resolve()
        for candidate in (root, *root.parents):
            if candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded


def find_node_playwright(start: Path | None = None) -> Path | None:
    """Find a Node Playwright package owned by the calling project."""
    explicit = os.environ.get("TESTQL_NODE_PLAYWRIGHT_PATH")
    if explicit:
        path = Path(explicit).expanduser().resolve()
        if (path / "package.json").is_file():
            return path

    if shutil.which("node") is None:
        return None
    for root in _search_roots(start):
        for package in _PLAYWRIGHT_PACKAGES:
            path = root / "node_modules" / package
            if (path / "package.json").is_file():
                if package == "@playwright/test":
                    runtime = root / "node_modules" / "playwright"
                    if (runtime / "package.json").is_file():
                        return runtime
                return path
    return None


def find_browser_executable() -> str | None:
    """Return an explicitly configured or common system Chromium executable."""
    for env_name in _BROWSER_ENV_VARS:
        value = os.environ.get(env_name)
        if value and os.access(Path(value).expanduser(), os.X_OK):
            return str(Path(value).expanduser().resolve())
    for command in _BROWSER_COMMANDS:
        value = shutil.which(command)
        if value:
            return str(Path(value).resolve())
    for value in _BROWSER_PATHS:
        if os.access(value, os.X_OK):
            return value
    return None


class NodePlaywrightError(RuntimeError):
    """The Node Playwright bridge rejected or could not execute a command."""


class NodePlaywrightSession:
    """Own a Node process and expose the small Playwright API used by TestQL."""

    def __init__(self, package_path: Path) -> None:
        node = shutil.which("node")
        if node is None:
            raise NodePlaywrightError("Node.js executable not found")
        bridge = Path(__file__).with_name("_node_playwright_bridge.cjs")
        self._process = subprocess.Popen(
            [node, str(bridge)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._package_path = package_path
        self._request_id = 0
        self.page = NodePlaywrightPage(self)

    @classmethod
    def start(
        cls,
        package_path: Path,
        url: str,
        *,
        headless: bool,
        timeout: int,
        navigation_timeout: int,
        executable_path: str | None,
    ) -> "NodePlaywrightSession":
        session = cls(package_path)
        try:
            session.call(
                "start",
                package_path=str(package_path),
                url=url,
                headless=headless,
                timeout=timeout,
                navigation_timeout=navigation_timeout,
                executable_path=executable_path,
            )
        except Exception:
            session.close(force=True)
            raise
        return session

    def call(self, command: str, **args: Any) -> Any:
        process = self._process
        if process.poll() is not None:
            stderr = process.stderr.read().strip() if process.stderr else ""
            raise NodePlaywrightError(
                f"Node Playwright bridge exited with {process.returncode}: {stderr}"
            )
        self._request_id += 1
        request = {"id": self._request_id, "command": command, "args": args}
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
        process.stdin.flush()
        response_line = process.stdout.readline()
        if not response_line:
            stderr = process.stderr.read().strip() if process.stderr else ""
            raise NodePlaywrightError(f"Node Playwright bridge closed unexpectedly: {stderr}")
        response = json.loads(response_line)
        if response.get("id") != self._request_id:
            raise NodePlaywrightError("Node Playwright bridge response id mismatch")
        if not response.get("ok"):
            raise NodePlaywrightError(response.get("error", "unknown Node Playwright error"))
        return response.get("result")

    def close(self, *, force: bool = False) -> None:
        process = self._process
        if process.poll() is None and not force:
            try:
                self.call("close")
            except Exception:
                force = True
        if process.stdin:
            process.stdin.close()
        if process.poll() is None:
            if force:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)


class NodePlaywrightMouse:
    def __init__(self, session: NodePlaywrightSession) -> None:
        self._session = session

    def wheel(self, delta_x: int, delta_y: int) -> None:
        self._session.call("wheel", x=delta_x, y=delta_y)


class NodePlaywrightLocator:
    def __init__(self, session: NodePlaywrightSession, selector: str, *, first: bool = False) -> None:
        self._session = session
        self._selector = selector
        self._first = first

    @property
    def first(self) -> "NodePlaywrightLocator":
        return NodePlaywrightLocator(self._session, self._selector, first=True)

    def click(self, *, timeout: int) -> None:
        self._session.call(
            "click", selector=self._selector, first=self._first, timeout=timeout
        )

    def evaluate(self, expression: str, arg: Any = None) -> Any:
        return self._session.call(
            "locator_evaluate",
            selector=self._selector,
            first=self._first,
            expression=expression,
            arg=arg,
        )

    def count(self) -> int:
        return int(self._session.call("count", selector=self._selector, first=self._first))

    def input_value(self) -> str:
        return str(
            self._session.call(
                "input_value", selector=self._selector, first=self._first, timeout=5000
            )
        )

    def get_attribute(self, name: str) -> str | None:
        return self._session.call(
            "get_attribute",
            selector=self._selector,
            first=self._first,
            name=name,
            timeout=5000,
        )

    def screenshot(self, *, path: str) -> None:
        self._session.call(
            "screenshot", selector=self._selector, first=self._first, path=path
        )


class NodePlaywrightPage:
    def __init__(self, session: NodePlaywrightSession) -> None:
        self._session = session
        self._timeout = 5000
        self._navigation_timeout = 15000
        self.mouse = NodePlaywrightMouse(session)

    @property
    def url(self) -> str:
        return str(self._session.call("url"))

    def set_default_timeout(self, timeout: int) -> None:
        self._timeout = timeout

    def set_default_navigation_timeout(self, timeout: int) -> None:
        self._navigation_timeout = timeout

    def goto(self, url: str, *, timeout: int | None = None) -> Any:
        return self._session.call("goto", url=url, timeout=timeout or self._navigation_timeout)

    def add_init_script(self, script: str) -> None:
        self._session.call("add_init_script", script=script)

    def performance_metrics(self, expression: str) -> list[dict[str, Any]]:
        return list(self._session.call("performance_metrics", expression=expression))

    def wait_for_url(self, url: str, *, wait_until: str, timeout: int) -> Any:
        return self._session.call(
            "wait_for_url", url=url, wait_until=wait_until, timeout=timeout
        )

    def is_visible(self, selector: str, *, timeout: int | None = None) -> bool:
        return bool(
            self._session.call(
                "is_visible", selector=selector, timeout=timeout or self._timeout
            )
        )

    def locator(self, selector: str) -> NodePlaywrightLocator:
        return NodePlaywrightLocator(self._session, selector)

    def fill(self, selector: str, value: str) -> None:
        self._session.call(
            "fill", selector=selector, value=value, timeout=self._timeout
        )

    def select_option(
        self, selector: str, *, value: str | None = None, label: str | None = None
    ) -> list[str]:
        mode = "label" if label is not None else "value"
        option = label if label is not None else value
        return list(
            self._session.call(
                "select_option",
                selector=selector,
                mode=mode,
                value=option,
                timeout=self._timeout,
            )
        )

    def inner_text(self, selector: str, *, timeout: int | None = None) -> str:
        return str(
            self._session.call(
                "inner_text", selector=selector, timeout=timeout or self._timeout
            )
        )

    def evaluate(self, expression: str) -> Any:
        return self._session.call("evaluate", expression=expression)

    def screenshot(self, *, path: str) -> None:
        self._session.call("screenshot", selector="", first=False, path=path)

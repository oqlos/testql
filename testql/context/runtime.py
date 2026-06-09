"""Detect and apply OS / browser / desktop / app runtime context."""

from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuntimeProfile:
    """Environment snapshot for scenario execution."""

    os_family: str = "unknown"
    os_release: str = ""
    session_type: str = ""
    display_server: str = ""
    browser_engine: str = "chromium"
    browser_headless: bool = True
    app_type: str = "generic"
    app_id: str = ""
    source_runtime: str = ""
    capabilities: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "os_family": self.os_family,
            "os_release": self.os_release,
            "session_type": self.session_type,
            "display_server": self.display_server,
            "browser_engine": self.browser_engine,
            "browser_headless": self.browser_headless,
            "app_type": self.app_type,
            "app_id": self.app_id,
            "source_runtime": self.source_runtime,
            "capabilities": list(self.capabilities),
            "extra": dict(self.extra),
        }


def _desktop_tools() -> list[str]:
    tools: list[str] = []
    for name in ("wmctrl", "xdotool", "wtype", "ydotool", "grim", "scrot", "gnome-screenshot"):
        if shutil.which(name):
            tools.append(name)
    return tools


def detect_runtime_profile(
    *,
    app_type: str = "",
    app_id: str = "",
    source_runtime: str = "",
    browser_engine: str | None = None,
    browser_headless: bool | None = None,
) -> RuntimeProfile:
    """Best-effort profile from process environment."""
    session = os.environ.get("XDG_SESSION_TYPE", "").strip().lower()
    display = "wayland" if session == "wayland" or os.environ.get("WAYLAND_DISPLAY") else "x11"
    if os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        display = "x11"

    caps: list[str] = ["api"]
    if shutil.which("playwright") or _importable("playwright"):
        caps.append("browser")
    desktop = _desktop_tools()
    if desktop:
        caps.extend(["desktop", f"desktop:{','.join(desktop)}"])

    return RuntimeProfile(
        os_family=platform.system().lower(),
        os_release=platform.release(),
        session_type=session or display,
        display_server=display,
        browser_engine=browser_engine or os.environ.get("TESTQL_BROWSER_ENGINE", "chromium"),
        browser_headless=browser_headless if browser_headless is not None else os.environ.get("TESTQL_HEADLESS", "1") != "0",
        app_type=app_type or "generic",
        app_id=app_id,
        source_runtime=source_runtime,
        capabilities=caps,
        extra={
            "python": platform.python_version(),
            "machine": platform.machine(),
        },
    )


def _importable(module: str) -> bool:
    try:
        __import__(module)
        return True
    except ImportError:
        return False


def profile_to_variables(profile: RuntimeProfile) -> dict[str, str]:
    """Flatten profile into interpreter SET variables."""
    vars_map = {
        "environment.os": profile.os_family,
        "environment.os_release": profile.os_release,
        "environment.session": profile.session_type,
        "environment.display": profile.display_server,
        "browser.engine": profile.browser_engine,
        "browser.headless": "true" if profile.browser_headless else "false",
        "app.type": profile.app_type,
        "app.id": profile.app_id or profile.app_type,
        "runtime.source": profile.source_runtime or "testql",
        "runtime.capabilities": ",".join(profile.capabilities),
    }
    for key, value in profile.extra.items():
        vars_map[f"environment.{key}"] = str(value)
    return vars_map


def _profile_str(data: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return str(value)
    return default


def _profile_bool(data: dict[str, Any], *keys: str) -> bool:
    raw = _profile_str(data, *keys, default="true")
    return raw.lower() in {"1", "true", "yes", "on"}


def _profile_capabilities(data: dict[str, Any]) -> list[str]:
    caps = data.get("capabilities")
    if isinstance(caps, str):
        return [item for item in caps.split(",") if item]
    return list(caps or [])


def _coerce_profile_dict(data: dict[str, Any]) -> RuntimeProfile:
    return RuntimeProfile(
        os_family=_profile_str(data, "os_family", "os", default="unknown"),
        os_release=_profile_str(data, "os_release", "os.release"),
        session_type=_profile_str(data, "session_type", "session"),
        display_server=_profile_str(data, "display_server", "display"),
        browser_engine=_profile_str(data, "browser_engine", "browser.engine", default="chromium"),
        browser_headless=_profile_bool(data, "browser_headless", "browser.headless"),
        app_type=_profile_str(data, "app_type", "app.type", default="generic"),
        app_id=_profile_str(data, "app_id", "app.id"),
        source_runtime=_profile_str(data, "source_runtime", "runtime.source"),
        capabilities=_profile_capabilities(data),
        extra={k: v for k, v in data.items() if k.startswith("runtime.") and k not in {"runtime.source"}},
    )


def apply_profile(interpreter: Any, profile: RuntimeProfile | dict[str, Any]) -> None:
    """Apply profile variables and interpreter flags."""
    if isinstance(profile, dict):
        profile = _coerce_profile_dict(profile)

    for key, value in profile_to_variables(profile).items():
        interpreter.vars.set(key, value)

    if hasattr(interpreter, "_runtime_profile"):
        interpreter._runtime_profile = profile

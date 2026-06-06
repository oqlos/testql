"""Tests for desktop catalog metadata."""

from __future__ import annotations

from testql.desktop.catalog import collect_desktop_catalog


def test_collect_desktop_catalog_has_commands() -> None:
    catalog = collect_desktop_catalog()
    names = {item["name"] for item in catalog["commands"]}
    assert "testql_desktop_list" in names
    assert "testql_desktop_focus" in names
    assert catalog["display_server"] in {"wayland", "x11", "unknown"}
    assert isinstance(catalog["host_tools"], list)
    assert len(catalog["recommended_python_libs"]) >= 5

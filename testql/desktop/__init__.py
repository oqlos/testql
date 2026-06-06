"""Native desktop application control (Linux X11 / Wayland)."""

from testql.desktop.backend import DesktopBackend, get_desktop_backend
from testql.desktop.catalog import collect_desktop_catalog
from testql.desktop.models import DesktopWindow

__all__ = [
    "DesktopBackend",
    "DesktopWindow",
    "collect_desktop_catalog",
    "get_desktop_backend",
]

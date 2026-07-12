"""desktop2testql — native desktop control backend for TestQL (Linux X11 / Wayland).

Backs the interpreter's `DESKTOP_*` commands (window management, click/type,
screenshots, vision assertions). TestQL core resolves this package lazily —
installing it is enough; there is nothing to configure or register.
"""

from desktop2testql.backend import DesktopBackend, get_desktop_backend
from desktop2testql.catalog import collect_desktop_catalog
from desktop2testql.element_assert import evaluate_element_assert
from desktop2testql.models import DesktopSession, DesktopWindow

__all__ = [
    "DesktopBackend",
    "DesktopSession",
    "DesktopWindow",
    "collect_desktop_catalog",
    "evaluate_element_assert",
    "get_desktop_backend",
]

"""DOM Scan mixin for OqlInterpreter — Playwright Accessibility Object Model.

DEPRECATED: This module now re-exports DOM scan components from split files for backward compatibility.
Import directly from:
- dom_scan_models: data models
- dom_scan_formatters: output formatters
- dom_scanner: DomScanner class
- dom_scan_mixin: DomScanMixin class
"""

from __future__ import annotations

from .dom_scan_models import (
    FocusableElement,
    DomScanResult,
    ButtonAuditResult,
    ButtonAuditReport,
)
from .dom_scan_formatters import (
    to_json,
    to_toon,
    to_text,
    to_text_audit,
)
from .dom_scanner import DomScanner
from .dom_scan_mixin import DomScanMixin


__all__ = [
    'FocusableElement',
    'DomScanResult',
    'ButtonAuditResult',
    'ButtonAuditReport',
    'to_json',
    'to_toon',
    'to_text',
    'to_text_audit',
    'DomScanner',
    'DomScanMixin',
]

"""DOM Scan output formatters.

This module provides functions to format DOM scan results.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from .dom_scan_models import DomScanResult, ButtonAuditReport


def to_json(result: DomScanResult, indent: int = 2) -> str:
    return json.dumps(asdict(result), indent=indent, ensure_ascii=False)


def to_toon(result: DomScanResult) -> str:
    lines = [
        f"# DOM_SCAN result — {result.scan_type}",
        f"# URL: {result.url}",
        f"# Total elements: {result.total}",
        "",
        f"DOMSCAN[{result.total}]{{index, role, name, selector, tag, disabled, value}}:",
    ]
    for el in result.elements:
        name_safe = el.name.replace(",", " ").replace("\n", " ")[:50]
        val_safe = str(el.value).replace(",", " ").replace("\n", " ") if el.value else "-"
        lines.append(
            f"  {el.index}, {el.role}, {name_safe}, "
            f"{el.selector}, {el.tag}, {el.disabled}, {val_safe}"
        )
    if result.warnings:
        lines += ["", "# WARNINGS:"]
        lines += [f"#   ⚠  {w}" for w in result.warnings]
    if result.errors:
        lines += ["", "# ERRORS:"]
        lines += [f"#   ❌ {e}" for e in result.errors]
    return "\n".join(lines)


def to_text(result: DomScanResult) -> str:
    lines = [
        f"DOM Scan [{result.scan_type.upper()}] — {result.url}",
        f"{'─' * 60}",
        f"Found: {result.total} elements",
        "",
    ]
    for el in result.elements:
        state_parts = []
        if el.disabled:
            state_parts.append("DISABLED")
        if el.required:
            state_parts.append("REQUIRED")
        if el.checked is True:
            state_parts.append("CHECKED")
        if el.expanded is not None:
            state_parts.append(f"expanded={el.expanded}")
        state = f" [{', '.join(state_parts)}]" if state_parts else ""
        value_hint = f" = '{el.value}'" if el.value else ""
        lines.append(
            f"  #{el.index:>3}  [{el.role:<16}]  {el.name or '(no name)':<40}"
            f"  {el.selector}{state}{value_hint}"
        )
    if result.warnings:
        lines += ["", "⚠ Warnings:"]
        lines += [f"  {w}" for w in result.warnings]
    if result.errors:
        lines += ["", "❌ Errors:"]
        lines += [f"  {e}" for e in result.errors]
    return "\n".join(lines)


def to_text_audit(report: ButtonAuditReport) -> str:
    lines = [
        f"DOM Button Audit — {report.url}",
        f"{'─' * 60}",
        f"Tested: {report.total_tested} | OK: {report.ok} | DEAD: {report.dead} | BROKEN: {report.broken}",
        "",
    ]
    for res in report.results:
        icon = "✅" if res.status == "OK" else "❌" if res.status in ("DEAD", "BROKEN") else "⏭️"
        lines.append(f"  {icon} [{res.status:<6}] {res.name[:30]:<30} {res.selector[:20]:<20} -> {res.details}")
    return "\n".join(lines)

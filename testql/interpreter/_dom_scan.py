"""DOM Scan mixin for IqlInterpreter — Playwright Accessibility Object Model."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any

from testql.base import StepResult, StepStatus
from ._parser import IqlLine


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class FocusableElement:
    index: int                      # TAB order position (1-based)
    role: str                       # ARIA role: button, link, textbox …
    name: str                       # accessible name (label / aria-label)
    selector: str                   # CSS selector or xpath hint
    tag: str                        # raw HTML tag
    tabindex: int | None            # explicit tabindex value or None
    disabled: bool = False
    expanded: bool | None = None    # for menus / accordions
    checked: bool | None = None     # for checkboxes / radios
    required: bool = False
    value: str | None = None        # current value for inputs
    description: str | None = None  # aria-description / title
    children_count: int = 0


@dataclass
class DomScanResult:
    url: str
    scan_type: str
    total: int
    elements: list[FocusableElement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)   # e.g. duplicate labels
    errors: list[str] = field(default_factory=list)     # broken ARIA


@dataclass
class ButtonAuditResult:
    selector: str
    name: str
    status: str  # "OK", "DEAD", "BROKEN", "SKIPPED"
    details: str

@dataclass
class ButtonAuditReport:
    url: str
    total_tested: int
    ok: int
    dead: int
    broken: int
    results: list[ButtonAuditResult] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------

FOCUSABLE_SELECTOR = (
    "a[href], button:not([disabled]), input:not([disabled]), "
    "select:not([disabled]), textarea:not([disabled]), "
    "[tabindex]:not([tabindex='-1']), [contenteditable='true'], "
    "details > summary"
)

INTERACTIVE_ROLES = {
    "button", "link", "textbox", "checkbox", "radio", "combobox",
    "listbox", "menuitem", "menuitemcheckbox", "menuitemradio",
    "option", "searchbox", "slider", "spinbutton", "switch",
    "tab", "treeitem",
}


def _aom_node_to_element(node: dict, index: int) -> FocusableElement | None:
    role = node.get("role", "")
    name = node.get("name", "")
    if not role:
        return None

    return FocusableElement(
        index=index,
        role=role,
        name=name,
        selector=f"[role='{role}']",
        tag=node.get("tag", ""),
        tabindex=node.get("tabIndex"),
        disabled=node.get("disabled", False),
        expanded=node.get("expanded"),
        checked=node.get("checked"),
        required=node.get("required", False),
        value=node.get("value"),
        description=node.get("description"),
        children_count=len(node.get("children", [])),
    )


def _flatten_aom(node: dict, result: list, depth: int = 0) -> None:
    result.append((depth, node))
    for child in node.get("children", []):
        _flatten_aom(child, result, depth + 1)


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Core scanner
# ---------------------------------------------------------------------------

class DomScanner:
    def __init__(self, page):
        self.page = page

    def scan_focusable(self, url: str) -> DomScanResult:
        elements = self._get_focusable_elements()
        return DomScanResult(
            url=url,
            scan_type="focusable",
            total=len(elements),
            elements=elements,
            warnings=self._check_duplicate_labels(elements),
        )

    def scan_aria(self, url: str) -> DomScanResult:
        snapshot = self.page.accessibility.snapshot(interesting_only=False)
        flat: list[tuple[int, dict]] = []
        if snapshot:
            _flatten_aom(snapshot, flat)

        elements = []
        for idx, (depth, node) in enumerate(flat):
            el = _aom_node_to_element(node, idx + 1)
            if el:
                elements.append(el)

        return DomScanResult(
            url=url,
            scan_type="aria",
            total=len(elements),
            elements=elements,
            warnings=self._check_duplicate_labels(elements),
            errors=self._check_aria_errors(elements),
        )

    def scan_interactive(self, url: str) -> DomScanResult:
        all_elements = self._get_focusable_elements()
        interactive = [e for e in all_elements if e.role in INTERACTIVE_ROLES]
        return DomScanResult(
            url=url,
            scan_type="interactive",
            total=len(interactive),
            elements=interactive,
            warnings=self._check_duplicate_labels(interactive),
        )

    def scan_taborder(self, url: str) -> DomScanResult:
        elements = self._simulate_tab_order()
        return DomScanResult(
            url=url,
            scan_type="taborder",
            total=len(elements),
            elements=elements,
            warnings=self._check_tabindex_warnings(elements),
        )

    def audit_buttons(self, url: str, ignore_selectors: list[str] = None) -> ButtonAuditReport:
        ignore_selectors = ignore_selectors or []
        all_elements = self._get_focusable_elements()
        buttons = [e for e in all_elements if e.role == "button"]

        report = ButtonAuditReport(url=url, total_tested=0, ok=0, dead=0, broken=0)

        for btn in buttons:
            skip = False
            for ign in ignore_selectors:
                if ign in btn.selector or ign in btn.name:
                    skip = True
                    break
            
            if skip:
                report.results.append(ButtonAuditResult(btn.selector, btn.name, "SKIPPED", "Ignored by selector"))
                continue

            request_detected = False
            page_error = None
            console_error = None

            def on_request(req):
                nonlocal request_detected
                request_detected = True

            def on_pageerror(err):
                nonlocal page_error
                page_error = str(err)

            def on_console(msg):
                nonlocal console_error
                if msg.type == "error":
                    console_error = msg.text

            self.page.on("request", on_request)
            self.page.on("pageerror", on_pageerror)
            self.page.on("console", on_console)

            self.page.evaluate('''() => {
                window.__auditMutations = 0;
                if (window.__auditObserver) window.__auditObserver.disconnect();
                window.__auditObserver = new MutationObserver(() => window.__auditMutations++);
                window.__auditObserver.observe(document.body, {childList: true, subtree: true, attributes: true, characterData: true});
            }''')

            try:
                self.page.locator(btn.selector).first.click(force=True, timeout=1000, no_wait_after=True)
                self.page.wait_for_timeout(500)
                
                mutations = self.page.evaluate("window.__auditMutations || 0")
                
                if page_error or console_error:
                    err_msg = page_error or console_error
                    report.broken += 1
                    report.results.append(ButtonAuditResult(btn.selector, btn.name, "BROKEN", f"Error: {str(err_msg)[:50]}"))
                elif request_detected or mutations > 0:
                    report.ok += 1
                    report.results.append(ButtonAuditResult(btn.selector, btn.name, "OK", f"Mutations: {mutations}, Req: {request_detected}"))
                else:
                    report.dead += 1
                    report.results.append(ButtonAuditResult(btn.selector, btn.name, "DEAD", "No DOM mutation or network request"))
            except Exception as e:
                error_msg = str(e)
                if "Element is not visible" in error_msg or "Node is detached" in error_msg or "hidden" in error_msg.lower():
                    report.results.append(ButtonAuditResult(btn.selector, btn.name, "SKIPPED", "Element is hidden or detached"))
                else:
                    report.broken += 1
                    report.results.append(ButtonAuditResult(btn.selector, btn.name, "BROKEN", f"Click failed: {error_msg[:50]}"))

            self.page.remove_listener("request", on_request)
            self.page.remove_listener("pageerror", on_pageerror)
            self.page.remove_listener("console", on_console)
            
            report.total_tested += 1

            if self.page.url != url:
                try:
                    self.page.goto(url, wait_until="networkidle")
                except Exception:
                    pass

        return report

    def assert_taborder(self, selector: str, expected_index: int) -> tuple[bool, str]:
        elements = self._simulate_tab_order()
        for el in elements:
            if selector.lower() in el.selector.lower() or selector.lower() in el.name.lower():
                if el.index == expected_index:
                    return True, f"✅ '{selector}' is #{expected_index} in TAB order"
                else:
                    return False, (
                        f"❌ '{selector}' is #{el.index} in TAB order, "
                        f"expected #{expected_index}"
                    )
        return False, f"❌ '{selector}' not found in TAB order"

    def assert_aria(self, role: str, name: str) -> tuple[bool, str]:
        snapshot = self.page.accessibility.snapshot()
        flat: list[tuple[int, dict]] = []
        if snapshot:
            _flatten_aom(snapshot, flat)
        for _, node in flat:
            if (node.get("role", "").lower() == role.lower() and
                    name.lower() in node.get("name", "").lower()):
                return True, f"✅ ARIA [{role}] '{name}' found"
        return False, f"❌ ARIA [{role}] '{name}' not found in accessibility tree"

    def assert_focusable(self, selector: str) -> tuple[bool, str]:
        try:
            count = self.page.locator(
                f"{selector}:is({FOCUSABLE_SELECTOR})"
            ).count()
            if count > 0:
                return True, f"✅ '{selector}' is keyboard-reachable"
            
            el = self.page.locator(selector).first
            ti = el.get_attribute("tabindex")
            if ti is not None and ti != "-1":
                return True, f"✅ '{selector}' has tabindex={ti}"
            return False, f"❌ '{selector}' is NOT keyboard-reachable"
        except Exception as exc:
            return False, f"❌ Error checking focusable: {exc}"

    def _get_focusable_elements(self) -> list[FocusableElement]:
        handles = self.page.locator(FOCUSABLE_SELECTOR).all()
        results = []
        for idx, handle in enumerate(handles, start=1):
            try:
                tag = handle.evaluate("el => el.tagName.toLowerCase()")
                role = (
                    handle.get_attribute("role")
                    or self._implicit_role(tag)
                )
                name = (
                    handle.get_attribute("aria-label")
                    or handle.get_attribute("title")
                    or handle.inner_text()[:60].strip()
                    or handle.get_attribute("placeholder")
                    or handle.get_attribute("name")
                    or ""
                )
                tabindex_raw = handle.get_attribute("tabindex")
                tabindex = int(tabindex_raw) if tabindex_raw is not None else None
                disabled = handle.is_disabled()
                value = None
                try:
                    value = handle.input_value() if tag in ("input", "select", "textarea") else None
                except Exception:
                    pass

                results.append(FocusableElement(
                    index=idx,
                    role=role,
                    name=name,
                    selector=self._build_selector(handle, tag),
                    tag=tag,
                    tabindex=tabindex,
                    disabled=disabled,
                    value=value,
                    required="true" == (handle.get_attribute("required") or ""),
                    description=handle.get_attribute("aria-describedby"),
                ))
            except Exception:
                continue
        return results

    def _simulate_tab_order(self) -> list[FocusableElement]:
        seen_selectors: list[str] = []
        ordered: list[FocusableElement] = []
        max_tabs = 200

        self.page.evaluate("document.body.focus()")

        for i in range(max_tabs):
            self.page.keyboard.press("Tab")
            focused = self.page.evaluate("""() => {
                const el = document.activeElement;
                if (!el || el === document.body) return null;
                return {
                    tag: el.tagName.toLowerCase(),
                    role: el.getAttribute('role') || '',
                    name: el.getAttribute('aria-label') || el.innerText?.slice(0, 60) || el.name || '',
                    tabindex: el.getAttribute('tabindex'),
                    disabled: el.disabled || false,
                    id: el.id || '',
                    className: el.className || '',
                    type: el.type || '',
                    value: (el.tagName === 'INPUT' || el.tagName === 'SELECT') ? el.value : null,
                    outerHTMLSnippet: el.outerHTML.slice(0, 120),
                }
            }""")
            if not focused:
                break

            selector = (
                f"#{focused['id']}" if focused["id"]
                else f"{focused['tag']}.{focused['className'].split()[0]}" if focused["className"]
                else focused["tag"]
            )

            if selector in seen_selectors[:3] and i > 5:
                break

            seen_selectors.append(selector)
            ordered.append(FocusableElement(
                index=len(ordered) + 1,
                role=focused["role"] or self._implicit_role(focused["tag"]),
                name=focused["name"],
                selector=selector,
                tag=focused["tag"],
                tabindex=int(focused["tabindex"]) if focused["tabindex"] else None,
                disabled=focused["disabled"],
                value=focused.get("value"),
            ))

        return ordered

    def _implicit_role(self, tag: str) -> str:
        return {
            "a": "link", "button": "button", "input": "textbox",
            "select": "listbox", "textarea": "textbox",
            "summary": "button", "details": "group",
            "nav": "navigation", "main": "main", "header": "banner",
            "footer": "contentinfo", "form": "form",
            "h1": "heading", "h2": "heading", "h3": "heading",
            "ul": "list", "ol": "list", "li": "listitem",
            "table": "table", "tr": "row", "td": "cell", "th": "columnheader",
            "img": "img", "dialog": "dialog",
        }.get(tag, "generic")

    def _build_selector(self, handle, tag: str) -> str:
        try:
            id_ = handle.get_attribute("id")
            if id_:
                return f"#{id_}"
            name = handle.get_attribute("name")
            if name:
                return f"{tag}[name='{name}']"
            cls = handle.get_attribute("class")
            if cls:
                first_cls = cls.split()[0]
                return f"{tag}.{first_cls}"
        except Exception:
            pass
        return tag

    def _check_duplicate_labels(self, elements: list[FocusableElement]) -> list[str]:
        seen: dict[str, int] = {}
        warnings = []
        for el in elements:
            key = f"{el.role}:{el.name}"
            if el.name:
                seen[key] = seen.get(key, 0) + 1
        for key, count in seen.items():
            if count > 1:
                warnings.append(f"Duplicate accessible name: '{key}' appears {count}×")
        return warnings

    def _check_aria_errors(self, elements: list[FocusableElement]) -> list[str]:
        errors = []
        for el in elements:
            if el.role in INTERACTIVE_ROLES and not el.name:
                errors.append(f"Missing accessible name for [{el.role}] at '{el.selector}'")
        return errors

    def _check_tabindex_warnings(self, elements: list[FocusableElement]) -> list[str]:
        warnings = []
        positive_tabs = [e for e in elements if e.tabindex and e.tabindex > 0]
        if positive_tabs:
            warnings.append(
                f"Found {len(positive_tabs)} element(s) with positive tabindex "
                f"— this disrupts natural TAB order: "
                + ", ".join(f"{e.selector}(tabindex={e.tabindex})" for e in positive_tabs[:5])
            )
        return warnings


# ---------------------------------------------------------------------------
# TestQL Mixin
# ---------------------------------------------------------------------------

class DomScanMixin:
    """Mixin for DOM Scan commands."""

    def _cmd_dom_scan(self, args: str, line: IqlLine) -> None:
        """DOM_SCAN <type> [--output <format>] [--out-file <path>]"""
        parts = args.split()
        if not parts:
            self.out.fail(f"L{line.number}: DOM_SCAN requires type (focusable|aria|interactive|taborder)")
            self.results.append(StepResult(
                name="DOM_SCAN", status=StepStatus.ERROR, message="Missing type"
            ))
            return

        scan_type = parts[0].lower()
        output_format = "text"
        out_file = None

        i = 1
        while i < len(parts):
            if parts[i] == "--output" and i + 1 < len(parts):
                output_format = parts[i + 1].lower()
                i += 2
            elif parts[i] == "--out-file" and i + 1 < len(parts):
                out_file = parts[i + 1]
                i += 2
            else:
                i += 1

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: DOM_SCAN requires active GUI session. Use GUI_START first.")
            self.results.append(StepResult(
                name=f"DOM_SCAN {scan_type}", status=StepStatus.ERROR, message="No active GUI session"
            ))
            return

        if self.dry_run:
            self.out.step("🔍", f"DOM_SCAN {scan_type} (dry-run)")
            self.results.append(StepResult(name=f"DOM_SCAN {scan_type}", status=StepStatus.PASSED))
            return

        try:
            scanner = DomScanner(self._gui_page)
            url = self._gui_page.url

            scan_methods = {
                "focusable":   scanner.scan_focusable,
                "aria":        scanner.scan_aria,
                "interactive": scanner.scan_interactive,
                "taborder":    scanner.scan_taborder,
            }

            if scan_type not in scan_methods:
                self.out.fail(f"L{line.number}: Unknown scan type '{scan_type}'")
                self.results.append(StepResult(
                    name=f"DOM_SCAN {scan_type}", status=StepStatus.ERROR, message=f"Unknown type: {scan_type}"
                ))
                return

            result = scan_methods[scan_type](url)

            formatters = {"text": to_text, "json": to_json, "toon": to_toon}
            formatter = formatters.get(output_format, to_text)
            output_str = formatter(result)

            if out_file:
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(output_str)
                self.out.step("🔍", f"DOM_SCAN [{scan_type}] → saved to {out_file} ({result.total} elements)")
            else:
                self.out.emit(output_str)
                self.out.step("🔍", f"DOM_SCAN [{scan_type}] → {result.total} elements")

            self._last_dom_scan = result

            if result.errors:
                for err in result.errors:
                    self.out.fail(f"DOM_SCAN:ARIA {err}")
                self.results.append(StepResult(
                    name=f"DOM_SCAN {scan_type}", status=StepStatus.FAILED, message=f"Found {len(result.errors)} errors"
                ))
            else:
                self.results.append(StepResult(
                    name=f"DOM_SCAN {scan_type}", status=StepStatus.PASSED, details=asdict(result)
                ))

        except Exception as exc:
            self.out.fail(f"L{line.number}: DOM_SCAN error: {exc}")
            self.results.append(StepResult(
                name=f"DOM_SCAN {scan_type}", status=StepStatus.ERROR, message=str(exc)
            ))

    def _cmd_dom_audit_buttons(self, args: str, line: IqlLine) -> None:
        """DOM_AUDIT_BUTTONS [--ignore "#logout, .delete"]"""
        import shlex
        parts = shlex.split(args)
        
        ignore_selectors = []
        i = 0
        while i < len(parts):
            if parts[i] == "--ignore" and i + 1 < len(parts):
                ignore_selectors = [s.strip() for s in parts[i+1].split(",")]
                i += 2
            else:
                i += 1

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: DOM_AUDIT_BUTTONS requires active GUI session.")
            self.results.append(StepResult(name="DOM_AUDIT_BUTTONS", status=StepStatus.ERROR, message="No active GUI session"))
            return

        if self.dry_run:
            self.out.step("🐵", "DOM_AUDIT_BUTTONS (dry-run)")
            self.results.append(StepResult(name="DOM_AUDIT_BUTTONS", status=StepStatus.PASSED))
            return

        scanner = DomScanner(self._gui_page)
        url = self._gui_page.url

        try:
            report = scanner.audit_buttons(url, ignore_selectors)
            output_str = to_text_audit(report)
            self.out.emit(output_str)

            if report.dead > 0 or report.broken > 0:
                self.out.fail(f"DOM_AUDIT_BUTTONS failed: {report.dead} dead, {report.broken} broken buttons.")
                self.results.append(StepResult(
                    name="DOM_AUDIT_BUTTONS", status=StepStatus.FAILED, 
                    message=f"{report.dead} dead, {report.broken} broken",
                    details=asdict(report)
                ))
            else:
                self.out.step("✅", f"DOM_AUDIT_BUTTONS passed: {report.ok} OK")
                self.results.append(StepResult(
                    name="DOM_AUDIT_BUTTONS", status=StepStatus.PASSED, details=asdict(report)
                ))
        except Exception as exc:
            self.out.fail(f"L{line.number}: DOM_AUDIT_BUTTONS error: {exc}")
            self.results.append(StepResult(
                name="DOM_AUDIT_BUTTONS", status=StepStatus.ERROR, message=str(exc)
            ))

    def _cmd_assert_taborder(self, args: str, line: IqlLine) -> None:
        import shlex
        parts = shlex.split(args)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: ASSERT_TABORDER requires selector and expected position")
            self.results.append(StepResult(
                name="ASSERT_TABORDER", status=StepStatus.ERROR, message="Missing arguments"
            ))
            return

        selector = parts[0]
        try:
            expected_pos = int(parts[1])
        except ValueError:
            self.out.fail(f"L{line.number}: Position must be an integer, got '{parts[1]}'")
            self.results.append(StepResult(
                name="ASSERT_TABORDER", status=StepStatus.ERROR, message="Invalid position"
            ))
            return

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: ASSERT_TABORDER requires active GUI session.")
            self.results.append(StepResult(
                name=f"ASSERT_TABORDER {selector}", status=StepStatus.ERROR, message="No active GUI session"
            ))
            return

        if self.dry_run:
            self.out.step("✅", f"ASSERT_TABORDER {selector} {expected_pos} (dry-run)")
            self.results.append(StepResult(name=f"ASSERT_TABORDER {selector}", status=StepStatus.PASSED))
            return

        scanner = DomScanner(self._gui_page)
        ok, msg = scanner.assert_taborder(selector, expected_pos)
        if ok:
            self.out.step("✅", msg)
            self.results.append(StepResult(name=f"ASSERT_TABORDER {selector}", status=StepStatus.PASSED))
        else:
            self.out.fail(f"L{line.number}: {msg}")
            self.results.append(StepResult(name=f"ASSERT_TABORDER {selector}", status=StepStatus.FAILED, message=msg))

    def _cmd_assert_aria(self, args: str, line: IqlLine) -> None:
        import shlex
        parts = shlex.split(args)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: ASSERT_ARIA requires role and name")
            self.results.append(StepResult(
                name="ASSERT_ARIA", status=StepStatus.ERROR, message="Missing arguments"
            ))
            return

        role = parts[0]
        name = parts[1]

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: ASSERT_ARIA requires active GUI session.")
            self.results.append(StepResult(
                name=f"ASSERT_ARIA {role}", status=StepStatus.ERROR, message="No active GUI session"
            ))
            return

        if self.dry_run:
            self.out.step("✅", f"ASSERT_ARIA {role} {name} (dry-run)")
            self.results.append(StepResult(name=f"ASSERT_ARIA {role}", status=StepStatus.PASSED))
            return

        scanner = DomScanner(self._gui_page)
        ok, msg = scanner.assert_aria(role, name)
        if ok:
            self.out.step("✅", msg)
            self.results.append(StepResult(name=f"ASSERT_ARIA {role}", status=StepStatus.PASSED))
        else:
            self.out.fail(f"L{line.number}: {msg}")
            self.results.append(StepResult(name=f"ASSERT_ARIA {role}", status=StepStatus.FAILED, message=msg))

    def _cmd_assert_focusable(self, args: str, line: IqlLine) -> None:
        import shlex
        parts = shlex.split(args)
        if not parts:
            self.out.fail(f"L{line.number}: ASSERT_FOCUSABLE requires selector")
            self.results.append(StepResult(
                name="ASSERT_FOCUSABLE", status=StepStatus.ERROR, message="Missing argument"
            ))
            return

        selector = parts[0]

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: ASSERT_FOCUSABLE requires active GUI session.")
            self.results.append(StepResult(
                name=f"ASSERT_FOCUSABLE {selector}", status=StepStatus.ERROR, message="No active GUI session"
            ))
            return

        if self.dry_run:
            self.out.step("✅", f"ASSERT_FOCUSABLE {selector} (dry-run)")
            self.results.append(StepResult(name=f"ASSERT_FOCUSABLE {selector}", status=StepStatus.PASSED))
            return

        scanner = DomScanner(self._gui_page)
        ok, msg = scanner.assert_focusable(selector)
        if ok:
            self.out.step("✅", msg)
            self.results.append(StepResult(name=f"ASSERT_FOCUSABLE {selector}", status=StepStatus.PASSED))
        else:
            self.out.fail(f"L{line.number}: {msg}")
            self.results.append(StepResult(name=f"ASSERT_FOCUSABLE {selector}", status=StepStatus.FAILED, message=msg))

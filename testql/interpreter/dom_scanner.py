"""DOM Scanner core implementation.

This module provides the DomScanner class for scanning DOM elements.
"""

from __future__ import annotations

from .dom_scan_models import DomScanResult, FocusableElement, ButtonAuditReport, ButtonAuditResult


# Playwright helpers

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
            if self._should_skip_button(btn, ignore_selectors):
                report.results.append(ButtonAuditResult(btn.selector, btn.name, "SKIPPED", "Ignored by selector"))
                continue

            result = self._audit_single_button(btn)
            report.results.append(result)
            self._update_report_counts(report, result)
            report.total_tested += 1
            
            self._restore_page_if_needed(url)

        return report

    def _should_skip_button(self, btn: FocusableElement, ignore_selectors: list[str]) -> bool:
        """Check if button should be skipped based on ignore selectors."""
        for ign in ignore_selectors:
            if ign in btn.selector or ign in btn.name:
                return True
        return False

    def _audit_single_button(self, btn: FocusableElement) -> ButtonAuditResult:
        """Audit a single button and return the result."""
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

        self._setup_mutation_observer()

        try:
            self.page.locator(btn.selector).first.click(force=True, timeout=1000, no_wait_after=True)
            self.page.wait_for_timeout(500)
            
            mutations = self.page.evaluate("window.__auditMutations || 0")
            return self._classify_button_result(btn, request_detected, page_error, console_error, mutations)
        except Exception as e:
            return self._handle_button_click_error(btn, e)
        finally:
            self._remove_event_listeners(on_request, on_pageerror, on_console)

    def _setup_mutation_observer(self) -> None:
        """Set up mutation observer to detect DOM changes."""
        self.page.evaluate('''() => {
            window.__auditMutations = 0;
            if (window.__auditObserver) window.__auditObserver.disconnect();
            window.__auditObserver = new MutationObserver(() => window.__auditMutations++);
            window.__auditObserver.observe(document.body, {childList: true, subtree: true, attributes: true, characterData: true});
        }''')

    def _classify_button_result(self, btn: FocusableElement, request_detected: bool, page_error: str | None, console_error: str | None, mutations: int) -> ButtonAuditResult:
        """Classify the button test result based on observed behavior."""
        if page_error or console_error:
            err_msg = page_error or console_error
            return ButtonAuditResult(btn.selector, btn.name, "BROKEN", f"Error: {str(err_msg)[:50]}")
        elif request_detected or mutations > 0:
            return ButtonAuditResult(btn.selector, btn.name, "OK", f"Mutations: {mutations}, Req: {request_detected}")
        else:
            return ButtonAuditResult(btn.selector, btn.name, "DEAD", "No DOM mutation or network request")

    def _handle_button_click_error(self, btn: FocusableElement, error: Exception) -> ButtonAuditResult:
        """Handle button click error and classify result."""
        error_msg = str(error)
        if "Element is not visible" in error_msg or "Node is detached" in error_msg or "hidden" in error_msg.lower():
            return ButtonAuditResult(btn.selector, btn.name, "SKIPPED", "Element is hidden or detached")
        else:
            return ButtonAuditResult(btn.selector, btn.name, "BROKEN", f"Click failed: {error_msg[:50]}")

    def _remove_event_listeners(self, on_request, on_pageerror, on_console) -> None:
        """Remove event listeners after button test."""
        self.page.remove_listener("request", on_request)
        self.page.remove_listener("pageerror", on_pageerror)
        self.page.remove_listener("console", on_console)

    def _update_report_counts(self, report: ButtonAuditReport, result: ButtonAuditResult) -> None:
        """Update report counts based on result status."""
        if result.status == "OK":
            report.ok += 1
        elif result.status == "DEAD":
            report.dead += 1
        elif result.status == "BROKEN":
            report.broken += 1

    def _restore_page_if_needed(self, url: str) -> None:
        """Restore original page URL if navigation occurred."""
        if self.page.url != url:
            try:
                self.page.goto(url, wait_until="networkidle")
            except Exception:
                pass

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

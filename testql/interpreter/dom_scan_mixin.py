"""DOM Scan mixin for OqlInterpreter — Playwright Accessibility Object Model.

This module provides the DomScanMixin class with OQL command implementations.
"""

from __future__ import annotations

import shlex
from dataclasses import asdict

from testql.base import StepResult, StepStatus

from ._parser import OqlLine
from .dom_scanner import DomScanner
from .dom_scan_formatters import to_text, to_json, to_toon, to_text_audit


class DomScanMixin:
    """Mixin for DOM Scan commands."""

    def _parse_dom_scan_args(self, args: str, line: OqlLine) -> tuple[str, str, str | None] | None:
        """Parse DOM_SCAN command arguments.

        Returns (scan_type, output_format, out_file) or None on error.
        """
        parts = args.split()
        if not parts:
            self.out.fail(f"L{line.number}: DOM_SCAN requires type (focusable|aria|interactive|taborder)")
            self.results.append(StepResult(
                name="DOM_SCAN", status=StepStatus.ERROR, message="Missing type"
            ))
            return None

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

        return scan_type, output_format, out_file

    def _execute_dom_scan(self, scan_type: str, output_format: str, out_file: str | None, line: OqlLine) -> None:
        """Execute DOM scan and handle output."""
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

    def _cmd_dom_scan(self, args: str, line: OqlLine) -> None:
        """DOM_SCAN <type> [--output <format>] [--out-file <path>]"""
        parsed = self._parse_dom_scan_args(args, line)
        if parsed is None:
            return

        scan_type, output_format, out_file = parsed

        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: DOM_SCAN requires active GUI session.")
            self.out.info("Hint: Add 'GUI_START http://your-app-url' before this command")
            self.results.append(StepResult(
                name=f"DOM_SCAN {scan_type}", status=StepStatus.ERROR, message="No active GUI session. Use GUI_START first."
            ))
            return

        if self.dry_run:
            self.out.step("🔍", f"DOM_SCAN {scan_type} (dry-run)")
            self.results.append(StepResult(name=f"DOM_SCAN {scan_type}", status=StepStatus.PASSED))
            return

        try:
            self._execute_dom_scan(scan_type, output_format, out_file, line)
        except Exception as exc:
            self.out.fail(f"L{line.number}: DOM_SCAN error: {exc}")
            self.results.append(StepResult(
                name=f"DOM_SCAN {scan_type}", status=StepStatus.ERROR, message=str(exc)
            ))

    def _cmd_dom_audit_buttons(self, args: str, line: OqlLine) -> None:
        """DOM_AUDIT_BUTTONS [--selector "css"] [--ignore "#logout, .delete"] [--report-file path]"""
        selector, ignore_selectors, report_file = self._parse_audit_args(args)

        if not self._ensure_gui_session(line):
            return

        if self.dry_run:
            self.out.step("🐵", "DOM_AUDIT_BUTTONS (dry-run)")
            self.results.append(StepResult(name="DOM_AUDIT_BUTTONS", status=StepStatus.PASSED))
            return

        scanner = DomScanner(self._gui_page)
        url = self._gui_page.url

        try:
            report = scanner.audit_buttons(url, ignore_selectors)
            self._handle_audit_report(report, report_file)
        except Exception as exc:
            self.out.fail(f"L{line.number}: DOM_AUDIT_BUTTONS error: {exc}")
            self.results.append(StepResult(
                name="DOM_AUDIT_BUTTONS", status=StepStatus.ERROR, message=str(exc)
            ))

    def _parse_audit_args(self, args: str) -> tuple[str | None, list[str], str | None]:
        """Parse DOM_AUDIT_BUTTONS command arguments."""
        parts = shlex.split(args)
        selector = None
        ignore_selectors = []
        report_file = None
        i = 0
        
        while i < len(parts):
            if parts[i] == "--selector" and i + 1 < len(parts):
                selector = parts[i + 1]
                i += 2
            elif parts[i] == "--ignore" and i + 1 < len(parts):
                ignore_selectors = [s.strip() for s in parts[i+1].split(",")]
                i += 2
            elif parts[i] == "--report-file" and i + 1 < len(parts):
                report_file = parts[i + 1]
                i += 2
            else:
                i += 1
        
        return selector, ignore_selectors, report_file

    def _ensure_gui_session(self, line: OqlLine) -> bool:
        """Check if GUI session is active, return False if not."""
        if not getattr(self, "_gui_page", None):
            self.out.fail(f"L{line.number}: DOM_AUDIT_BUTTONS requires active GUI session.")
            self.out.info("Hint: Add 'GUI_START http://your-app-url' before this command")
            self.results.append(StepResult(
                name="DOM_AUDIT_BUTTONS",
                status=StepStatus.ERROR,
                message="No active GUI session. Use GUI_START first."
            ))
            return False
        return True

    def _handle_audit_report(self, report: ButtonAuditReport, report_file: str | None) -> None:
        """Handle audit report output and result classification."""
        output_str = to_text_audit(report)
        self.out.emit(output_str)

        if report_file:
            self._save_report_to_file(report, report_file)

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

    def _save_report_to_file(self, report: ButtonAuditReport, report_file: str) -> None:
        """Save audit report to JSON file."""
        import json
        report_dict = asdict(report)
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        self.out.step("📄", f"Report saved to {report_file}")

    def _cmd_assert_taborder(self, args: str, line: OqlLine) -> None:
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

    def _cmd_assert_aria(self, args: str, line: OqlLine) -> None:
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

    def _cmd_assert_focusable(self, args: str, line: OqlLine) -> None:
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

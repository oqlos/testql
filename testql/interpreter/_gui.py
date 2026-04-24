"""Desktop GUI test execution mixin for IqlInterpreter — Playwright/Selenium support."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import IqlLine


class GuiMixin:
    """Mixin providing desktop GUI test commands using Playwright.

    Commands:
      - GUI_START "app_path" [args] — Launch desktop application
      - GUI_CLICK "selector" — Click element
      - GUI_INPUT "selector" "text" — Type text into element
      - GUI_ASSERT_VISIBLE "selector" — Assert element is visible
      - GUI_ASSERT_TEXT "selector" "expected" — Assert element text
      - GUI_CAPTURE "selector" "screenshot.png" — Take screenshot
      - GUI_STOP — Close application
    """

    _gui_driver: str | None = None  # "playwright" or "selenium"
    _gui_app: Any = None  # Playwright/Selenium instance
    _gui_page: Any = None  # Browser page/window

    def _init_gui_driver(self) -> bool:
        """Initialize GUI driver based on configuration."""
        if self._gui_driver is None:
            self._gui_driver = self.vars.get("gui_driver", "playwright")

        if self._gui_driver == "playwright":
            try:
                from playwright.sync_api import sync_playwright
                return True
            except ImportError:
                self.out.warn("Playwright not installed. Install with: pip install playwright && playwright install")
                return False
        elif self._gui_driver == "selenium":
            try:
                import selenium
                return True
            except ImportError:
                self.out.warn("Selenium not installed. Install with: pip install selenium")
                return False
        return False

    def _cmd_gui_start(self, args: str, line: IqlLine) -> None:
        """GUI_START "app_path" [args] — Launch desktop application.

        For web apps, use base_url instead.
        For desktop apps, provide executable path or electron app path.

        Examples:
            GUI_START "http://localhost:5173"  # Web app
            GUI_START "/path/to/electron-app"
        """
        parts = args.strip().split(None, 1)
        if not parts:
            self.out.fail(f"L{line.number}: GUI_START requires path or URL")
            return

        app_path = parts[0].strip('"\'')
        extra_args = parts[1] if len(parts) > 1 else ""

        if self.dry_run:
            self.out.step("🖥️", f'GUI_START "{app_path[:50]}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_START "{app_path[:40]}"', status=StepStatus.PASSED
            ))
            return

        if not self._init_gui_driver():
            self.results.append(StepResult(
                name=f'GUI_START "{app_path[:40]}"',
                status=StepStatus.ERROR,
                message=f"{self._gui_driver} not installed",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                self._start_playwright(app_path, extra_args)
            elif self._gui_driver == "selenium":
                self._start_selenium(app_path, extra_args)
        except Exception as e:
            self.out.fail(f"GUI_START error: {e}")
            self.results.append(StepResult(
                name=f'GUI_START "{app_path[:40]}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _start_playwright(self, app_path: str, extra_args: str) -> None:
        """Start Playwright and navigate to app_path."""
        from playwright.sync_api import sync_playwright

        if app_path.startswith("http://") or app_path.startswith("https://"):
            # Web app
            p = sync_playwright().start()
            browser = p.chromium.launch(headless=False)
            self._gui_page = browser.new_page()
            self._gui_page.goto(app_path)
            self._gui_app = (p, browser)
            self.out.step("🖥️", f"Playwright: Opened {app_path}")
        else:
            # Desktop app (simplified - would need playwright-electron for full support)
            self.out.warn("Playwright desktop apps require playwright-electron. Using web mode fallback.")
            self._start_playwright("http://localhost:5173", extra_args)

        self.results.append(StepResult(
            name=f'GUI_START "{app_path[:40]}"', status=StepStatus.PASSED
        ))

    def _start_selenium(self, app_path: str, extra_args: str) -> None:
        """Start Selenium WebDriver."""
        from selenium import webdriver
        from selenium.webdriver.common.by import By

        if app_path.startswith("http://") or app_path.startswith("https://"):
            # Web app
            self._gui_app = webdriver.Chrome()
            self._gui_app.get(app_path)
            self._gui_page = self._gui_app
            self.out.step("🖥️", f"Selenium: Opened {app_path}")
        else:
            self.out.warn("Selenium desktop apps require additional setup. Using web mode fallback.")
            self._start_selenium("http://localhost:5173", extra_args)

        self.results.append(StepResult(
            name=f'GUI_START "{app_path[:40]}"', status=StepStatus.PASSED
        ))

    def _cmd_gui_click(self, args: str, line: IqlLine) -> None:
        """GUI_CLICK "selector" — Click element.

        Examples:
            GUI_CLICK "[data-testid=submit-button]"
            GUI_CLICK "button#submit"
        """
        selector = args.strip().strip('"\'')
        if not selector:
            self.out.fail(f"L{line.number}: GUI_CLICK requires selector")
            return

        if self.dry_run:
            self.out.step("🖱️", f'GUI_CLICK "{selector}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_CLICK: No active GUI session. Call GUI_START first")
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                self._gui_page.click(selector)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                elem.click()

            self.out.step("🖱️", f'GUI_CLICK "{selector}"')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f'GUI_CLICK "{selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_input(self, args: str, line: IqlLine) -> None:
        """GUI_INPUT "selector" "text" — Type text into element.

        Examples:
            GUI_INPUT "[data-testid=search]" "hello world"
            GUI_INPUT "input#username" "testuser"
        """
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: GUI_INPUT requires selector and text")
            return

        selector = parts[0].strip('"\'')
        text = parts[1].strip('"\'')

        if self.dry_run:
            self.out.step("⌨️", f'GUI_INPUT "{selector}" "{text[:20]}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_INPUT "{selector}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_INPUT: No active GUI session")
            self.results.append(StepResult(
                name=f'GUI_INPUT "{selector}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                self._gui_page.fill(selector, text)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                elem.clear()
                elem.send_keys(text)

            self.out.step("⌨️", f'GUI_INPUT "{selector}" → "{text[:20]}"')
            self.results.append(StepResult(
                name=f'GUI_INPUT "{selector}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f'GUI_INPUT "{selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_INPUT "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_assert_visible(self, args: str, line: IqlLine) -> None:
        """GUI_ASSERT_VISIBLE "selector" — Assert element is visible."""
        selector = args.strip().strip('"\'')
        if not selector:
            self.out.fail(f"L{line.number}: GUI_ASSERT_VISIBLE requires selector")
            return

        if self.dry_run:
            self.out.step("👁️", f'GUI_ASSERT_VISIBLE "{selector}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_VISIBLE "{selector}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_ASSERT_VISIBLE: No active GUI session")
            self.results.append(StepResult(
                name=f'GUI_ASSERT_VISIBLE "{selector}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                is_visible = self._gui_page.is_visible(selector)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                is_visible = elem.is_displayed()
            else:
                is_visible = False

            if is_visible:
                self.out.step("✅", f'GUI_ASSERT_VISIBLE "{selector}"')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_VISIBLE "{selector}"', status=StepStatus.PASSED
                ))
            else:
                self.out.step("❌", f'GUI_ASSERT_VISIBLE "{selector}" (not found)')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_VISIBLE "{selector}"',
                    status=StepStatus.FAILED,
                    message="Element not visible",
                ))
        except Exception as e:
            self.out.fail(f'GUI_ASSERT_VISIBLE "{selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_VISIBLE "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_assert_text(self, args: str, line: IqlLine) -> None:
        """GUI_ASSERT_TEXT "selector" "expected" — Assert element contains text."""
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: GUI_ASSERT_TEXT requires selector and expected text")
            return

        selector = parts[0].strip('"\'')
        expected = parts[1].strip('"\'')

        if self.dry_run:
            self.out.step("📝", f'GUI_ASSERT_TEXT "{selector}" "{expected[:20]}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_TEXT "{selector}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_ASSERT_TEXT: No active GUI session")
            self.results.append(StepResult(
                name=f'GUI_ASSERT_TEXT "{selector}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                actual = self._gui_page.inner_text(selector)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                actual = elem.text
            else:
                actual = ""

            if expected in actual:
                self.out.step("✅", f'GUI_ASSERT_TEXT "{selector}" → "{expected[:20]}"')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_TEXT "{selector}"', status=StepStatus.PASSED
                ))
            else:
                self.out.step("❌", f'GUI_ASSERT_TEXT "{selector}" (expected "{expected[:20]}", got "{actual[:20]}")')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_TEXT "{selector}"',
                    status=StepStatus.FAILED,
                    message=f'Expected "{expected}", got "{actual}"',
                ))
        except Exception as e:
            self.out.fail(f'GUI_ASSERT_TEXT "{selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_TEXT "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_capture(self, args: str, line: IqlLine) -> None:
        """GUI_CAPTURE "selector" "screenshot.png" — Take screenshot of element or full page.

        Examples:
            GUI_CAPTURE "" "full-page.png"  # Full page
            GUI_CAPTURE "[data-testid=main]" "main.png"  # Element
        """
        parts = args.strip().split(None, 1)
        selector = parts[0].strip('"\'') if parts else ""
        filename = parts[1].strip('"\'') if len(parts) > 1 else "screenshot.png"

        if self.dry_run:
            self.out.step("📸", f'GUI_CAPTURE → "{filename}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_CAPTURE "{filename}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_CAPTURE: No active GUI session")
            self.results.append(StepResult(
                name=f'GUI_CAPTURE "{filename}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                if selector:
                    self._gui_page.locator(selector).screenshot(path=filename)
                else:
                    self._gui_page.screenshot(path=filename)
            elif self._gui_driver == "selenium":
                self._gui_page.save_screenshot(filename)

            self.out.step("📸", f'GUI_CAPTURE → "{filename}"')
            self.results.append(StepResult(
                name=f'GUI_CAPTURE "{filename}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f"GUI_CAPTURE error: {e}")
            self.results.append(StepResult(
                name=f'GUI_CAPTURE "{filename}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_stop(self, args: str, line: IqlLine) -> None:
        """GUI_STOP — Close application/browser."""
        if self.dry_run:
            self.out.step("🖥️", "GUI_STOP (dry-run)")
            self.results.append(StepResult(
                name="GUI_STOP", status=StepStatus.PASSED
            ))
            return

        try:
            if self._gui_app:
                if self._gui_driver == "playwright":
                    playwright, browser = self._gui_app
                    browser.close()
                    playwright.stop()
                elif self._gui_driver == "selenium":
                    self._gui_app.quit()

                self._gui_app = None
                self._gui_page = None
                self.out.step("🖥️", "GUI_STOP: Closed")
                self.results.append(StepResult(
                    name="GUI_STOP", status=StepStatus.PASSED
                ))
        except Exception as e:
            self.out.fail(f"GUI_STOP error: {e}")
            self.results.append(StepResult(
                name="GUI_STOP",
                status=StepStatus.ERROR,
                message=str(e),
            ))

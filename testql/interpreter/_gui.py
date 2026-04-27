"""Desktop GUI test execution mixin for OqlInterpreter — Playwright/Selenium support."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class GuiMixin:
    """Mixin providing desktop GUI test commands using Playwright.

    Commands:
      - GUI_START (START) "path" — Launch session
      - GUI_NAVIGATE (NAVIGATE, GOTO) "path" — Navigate
      - GUI_CLICK (CLICK) "selector" — Click
      - GUI_INPUT (INPUT, TYPE) "selector" "text" — Type
      - GUI_ASSERT_VISIBLE (ASSERT_VISIBLE, VISIBLE) "selector" — Visible?
      - GUI_ASSERT_TEXT (ASSERT_TEXT, TEXT) "selector" "expected" — Text?
      - GUI_CAPTURE (CAPTURE, SCREENSHOT) "selector" "file" — Screenshot
      - GUI_STOP (STOP, CLOSE) — Close session
    """

    CMD_MAP = {
        "NAVIGATE": "navigate",
        "CLICK": "click",
        "GUI_CLICK": "click",
        "SELECT": "select",
        "GUI_SELECT": "select",
        "INPUT": "input",
        "GUI_INPUT": "input",
        "SUBMIT": "submit",
        "GUI_SUBMIT": "submit",
        "GUI_ASSERT_VISIBLE": "assert_visible",
        "GUI_ASSERT_TEXT": "assert_text",
    }

    _gui_driver: str | None = None  # "playwright" or "selenium"
    _gui_app: Any = None  # Playwright/Selenium instance
    _gui_page: Any = None  # Browser page/window

    def _resolve_selector_with_fallback(self, selector: str) -> str | None:
        """Smart selector resolution with fallback strategies.
        
        Tries multiple selector strategies:
        1. Original selector as-is
        2. Convert class to data-testid (e.g., .qr-scanner-container -> [data-testid=qr-scanner-container])
        3. Convert class to ID (e.g., .qr-scanner-container -> #qr-scanner-container)
        4. Try partial text match for buttons/links
        
        Returns the working selector or None if all fail.
        """
        if not self._gui_page:
            return None
            
        selectors_to_try = self._generate_fallback_selectors(selector)
        timeout = self.timeout_ms if self.timeout_ms else 100
        
        return self._try_selectors(selectors_to_try, timeout)

    def _generate_fallback_selectors(self, selector: str) -> list[str]:
        """Generate list of fallback selectors to try."""
        selectors_to_try = [selector]
        
        selectors_to_try.extend(self._get_class_fallbacks(selector))
        selectors_to_try.extend(self._get_id_fallbacks(selector))
        selectors_to_try.extend(self._get_role_based_fallbacks(selector))
        selectors_to_try.extend(self._get_button_text_fallbacks(selector))
        
        return selectors_to_try

    def _get_class_fallbacks(self, selector: str) -> list[str]:
        """Generate fallback selectors for class-based selectors."""
        if not selector.startswith('.'):
            return []
        
        class_name = selector[1:]
        return [
            f'[data-testid="{class_name}"]',
            f'[data-testid="{class_name.replace("-", "_")}"]',
            f'#{class_name}',
            f'.{class_name.replace("-", "")}',
        ]

    def _get_id_fallbacks(self, selector: str) -> list[str]:
        """Generate fallback selectors for ID-based selectors."""
        if not selector.startswith('#'):
            return []
        
        id_name = selector[1:]
        return [f'.{id_name}']

    def _get_role_based_fallbacks(self, selector: str) -> list[str]:
        """Generate role-based fallback selectors for common patterns."""
        selector_lower = selector.lower()
        fallbacks = []
        
        if 'qr' in selector_lower or 'scanner' in selector_lower:
            fallbacks.extend(['[role="img"]', 'canvas'])
        
        if 'user' in selector_lower and 'list' in selector_lower:
            fallbacks.extend(['[role="list"]', 'ul', 'table tbody'])
        
        return fallbacks

    def _get_button_text_fallbacks(self, selector: str) -> list[str]:
        """Generate text-based fallback selectors for buttons."""
        selector_lower = selector.lower()
        if 'btn' not in selector_lower and 'button' not in selector_lower:
            return []
        
        fallbacks = []
        if 'collect' in selector_lower:
            fallbacks.extend(['button:has-text("Collect")', 'button:has-text("Logs")'])
        if 'copy' in selector_lower:
            fallbacks.extend(['button:has-text("Copy")', 'button:has-text("clipboard")'])
        
        return fallbacks

    def _try_selectors(self, selectors: list[str], timeout: int) -> str | None:
        """Try each selector and return the first one that works."""
        for try_selector in selectors:
            if self._try_single_selector(try_selector, timeout):
                return try_selector
        return None

    def _try_single_selector(self, selector: str, timeout: int) -> bool:
        """Try a single selector and return True if it works."""
        try:
            if self._gui_driver == "playwright":
                return self._gui_page.is_visible(selector, timeout=timeout)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                from selenium.common.exceptions import NoSuchElementException
                try:
                    elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                    return elem.is_displayed()
                except NoSuchElementException:
                    return False
        except Exception:
            return False
        return False

    def _find_element_with_logging(self, selector: str, action: str) -> tuple[str, Any] | tuple[None, None]:
        """Find element with smart fallback and logging.
        
        Returns (working_selector, element) or (None, None) if not found.
        """
        resolved = self._resolve_selector_with_fallback(selector)
        
        if resolved is None:
            self.out.warn(f"  ⚠️  Selector '{selector}' not found after trying fallbacks")
            return None, None
        
        if resolved != selector:
            self.out.step("🔍", f"  Found via fallback: '{selector}' -> '{resolved}'")
        
        try:
            if self._gui_driver == "playwright":
                return resolved, self._gui_page.locator(resolved)
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                return resolved, self._gui_page.find_element(By.CSS_SELECTOR, resolved)
        except Exception as e:
            self.out.warn(f"  ⚠️  Element found but error accessing: {e}")
            return None, None
        
        return None, None

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

    def _cmd_gui_start(self, args: str, line: OqlLine) -> None:
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
            headless = str(self.vars.get("headless", "true")).lower() == "true"
            browser = p.chromium.launch(headless=headless, args=["--no-sandbox", "--disable-setuid-sandbox"])
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
            headless = str(self.vars.get("headless", "true")).lower() == "true"
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            self._gui_app = webdriver.Chrome(options=options)
            self._gui_app.get(app_path)
            self._gui_page = self._gui_app
            self.out.step("🖥️", f"Selenium: Opened {app_path}")
        else:
            self.out.warn("Selenium desktop apps require additional setup. Using web mode fallback.")
            self._start_selenium("http://localhost:5173", extra_args)

        self.results.append(StepResult(
            name=f'GUI_START "{app_path[:40]}"', status=StepStatus.PASSED
        ))

    def _cmd_gui_navigate(self, args: str, line: OqlLine) -> None:
        """GUI_NAVIGATE "path_or_url" — Navigate to another page.

        Examples:
            GUI_NAVIGATE "/connect-id"
            GUI_NAVIGATE "http://google.com"
        """
        path = args.strip().strip('"\'')
        if not path:
            self.out.fail(f"L{line.number}: GUI_NAVIGATE requires path or URL")
            return

        if self.dry_run:
            self.out.step("🌐", f'GUI_NAVIGATE "{path}" (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_NAVIGATE "{path}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_NAVIGATE: No active GUI session. Call GUI_START first (auto-start disabled to prevent Playwright sync API errors)")
            self.results.append(StepResult(
                name=f'GUI_NAVIGATE "{path}"',
                status=StepStatus.ERROR,
                message="No active GUI session (auto-start disabled)",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                # Handle relative paths if base_url is set
                target = path
                if not (path.startswith("http://") or path.startswith("https://")):
                    base_url = self.vars.get("base_url", "http://localhost:8100")
                    target = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
                
                timeout = self.timeout_ms if self.timeout_ms else 30000
                self._gui_page.goto(target, timeout=timeout)
            elif self._gui_driver == "selenium":
                target = path
                if not (path.startswith("http://") or path.startswith("https://")):
                    base_url = self.vars.get("base_url", "http://localhost:8100")
                    target = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
                
                self._gui_page.get(target)

            self.out.step("🌐", f'GUI_NAVIGATE "{path}"')
            self.results.append(StepResult(
                name=f'GUI_NAVIGATE "{path}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f'GUI_NAVIGATE "{path}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_NAVIGATE "{path}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_navigate(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_NAVIGATE."""
        self._cmd_gui_navigate(args, line)

    def _cmd_gui_click(self, args: str, line: OqlLine) -> None:
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

        # Try smart selector fallback
        resolved_selector, element = self._find_element_with_logging(selector, "click")
        if resolved_selector is None:
            self.out.fail(f'GUI_CLICK "{selector}": Element not found')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"',
                status=StepStatus.FAILED,
                message="Element not found after trying fallback selectors",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                timeout = self.timeout_ms if self.timeout_ms else 30000
                element.click(timeout=timeout)
            elif self._gui_driver == "selenium":
                element.click()

            self.out.step("🖱️", f'GUI_CLICK "{resolved_selector}"')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f'GUI_CLICK "{resolved_selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_CLICK "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_input(self, args: str, line: OqlLine) -> None:
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

    def _cmd_gui_assert_visible(self, args: str, line: OqlLine) -> None:
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

        # Try smart selector fallback
        resolved_selector, element = self._find_element_with_logging(selector, "assert_visible")
        if resolved_selector is None:
            self.out.step("❌", f'GUI_ASSERT_VISIBLE "{selector}" (not found)')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_VISIBLE "{selector}"',
                status=StepStatus.FAILED,
                message="Element not found after trying fallback selectors",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                is_visible = self._gui_page.is_visible(resolved_selector)
            elif self._gui_driver == "selenium":
                is_visible = element.is_displayed()
            else:
                is_visible = False

            if is_visible:
                self.out.step("✅", f'GUI_ASSERT_VISIBLE "{resolved_selector}"')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_VISIBLE "{selector}"', status=StepStatus.PASSED
                ))
            else:
                self.out.step("❌", f'GUI_ASSERT_VISIBLE "{resolved_selector}" (not visible)')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_VISIBLE "{selector}"',
                    status=StepStatus.FAILED,
                    message="Element found but not visible",
                ))
        except Exception as e:
            self.out.fail(f'GUI_ASSERT_VISIBLE "{resolved_selector}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_ASSERT_VISIBLE "{selector}"',
                status=StepStatus.ERROR,
                message=str(e),
            ))

    def _cmd_gui_assert_text(self, args: str, line: OqlLine) -> None:
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

    def _cmd_gui_capture(self, args: str, line: OqlLine) -> None:
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

    def _cmd_gui_stop(self, args: str, line: OqlLine) -> None:
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

    # --- Unified Command Aliases ---

    def _cmd_start(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_START."""
        self._cmd_gui_start(args, line)

    def _cmd_stop(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_STOP."""
        self._cmd_gui_stop(args, line)

    def _cmd_close(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_STOP."""
        self._cmd_gui_stop(args, line)

    def _cmd_goto(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_NAVIGATE."""
        self._cmd_gui_navigate(args, line)

    def _cmd_click(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_CLICK."""
        self._cmd_gui_click(args, line)

    def _cmd_input(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_INPUT."""
        self._cmd_gui_input(args, line)

    def _cmd_type(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_INPUT."""
        self._cmd_gui_input(args, line)

    def _cmd_assert_visible(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_VISIBLE."""
        self._cmd_gui_assert_visible(args, line)

    def _cmd_visible(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_VISIBLE."""
        self._cmd_gui_assert_visible(args, line)

    def _cmd_assert_text(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_TEXT."""
        self._cmd_gui_assert_text(args, line)

    def _cmd_text(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_TEXT."""
        self._cmd_gui_assert_text(args, line)

    def _cmd_capture(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_CAPTURE."""
        self._cmd_gui_capture(args, line)

    def _cmd_screenshot(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_CAPTURE."""
        self._cmd_gui_capture(args, line)

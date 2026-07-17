"""Desktop GUI test execution mixin for OqlInterpreter — Playwright/Selenium support."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import shlex
import time
from urllib.parse import parse_qs, urlparse

from testql.base import StepResult, StepStatus

from ._parser import OqlLine


class GuiMixin:
    """Mixin providing desktop GUI test commands using Playwright.

    Commands:
      - GUI_START (START) "path" — Launch session
      - GUI_NAVIGATE (NAVIGATE, GOTO) "path" — Navigate
      - GUI_CLICK (CLICK) "selector" — Click
      - GUI_INPUT (INPUT, TYPE) "selector" "text" — Type
      - GUI_SCROLL (SCROLL, WHEEL) "selector" [delta_y] — Scroll page or element
      - GUI_ASSERT_VISIBLE (ASSERT_VISIBLE, VISIBLE) "selector" — Visible?
      - GUI_ASSERT_TEXT (ASSERT_TEXT, TEXT) "selector" "expected" — Text?
      - GUI_EVAL (EVAL) "javascript" — Execute JavaScript in the active page
      - GUI_ASSERT_COUNT (ASSERT_COUNT, COUNT) "selector" [op] expected — Count elements
      - GUI_WAIT_FOR_COUNT (WAIT_FOR_COUNT) "selector" [op] expected [timeout_ms] — Wait for count
      - GUI_ASSERT_URL_PARAM (ASSERT_URL_PARAM) "name" "value" — Assert URL query param
      - GUI_ASSERT_VALUE (ASSERT_VALUE) "selector" [op] expected — Assert form control value
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
        "SCROLL": "scroll",
        "GUI_SCROLL": "scroll",
        "WHEEL": "scroll",
        "GUI_WHEEL": "scroll",
        "SUBMIT": "submit",
        "GUI_SUBMIT": "submit",
        "GUI_ASSERT_VISIBLE": "assert_visible",
        "GUI_ASSERT_TEXT": "assert_text",
        "GUI_EVAL": "eval",
        "GUI_ASSERT_COUNT": "assert_count",
        "GUI_WAIT_FOR_COUNT": "wait_for_count",
        "GUI_ASSERT_URL_PARAM": "assert_url_param",
        "GUI_ASSERT_VALUE": "assert_value",
    }

    _gui_driver: str | None = None  # "playwright" or "selenium"
    _gui_app: Any = None  # Playwright/Selenium instance
    _gui_page: Any = None  # Browser page/window
    _gui_engine_unavailable: bool = False  # set when the browser engine is not installed

    def _gui_operation_timeout(self, default_ms: int = 5000) -> int:
        """Return one bounded timeout for a single browser operation.

        Playwright's implicit 30 second timeout made a missing selector look like
        a hung TestQL run.  Keep the CLI override, but use a fail-fast default for
        assertions and form actions.
        """
        configured = self.timeout_ms
        return max(1, int(configured)) if configured is not None else default_ms

    @staticmethod
    def _same_url_without_hash(left: str, right: str) -> bool:
        return left.split("#", 1)[0] == right.split("#", 1)[0]

    @staticmethod
    def _is_transient_browser_network_error(error: Exception) -> bool:
        text = str(error)
        return (
            "Failed to fetch" in text
            or "net::ERR_ABORTED" in text
            or "net::ERR_CONNECTION" in text
            or "net::ERR_TIMED_OUT" in text
        )

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
        # Fallback probes are intentionally short. The operation-level timeout
        # is enforced by the command itself and must not be multiplied by every
        # generated selector candidate.
        timeout = min(self._gui_operation_timeout(), 250)
        
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
                from playwright.sync_api import sync_playwright  # noqa: F401  (availability probe)
                return True
            except ImportError:
                self.out.warn("Playwright not installed. Install with: pip install playwright && playwright install")
                self._gui_engine_unavailable = True
                return False
        elif self._gui_driver == "selenium":
            try:
                import selenium  # noqa: F401  (availability probe)
                return True
            except ImportError:
                self.out.warn("Selenium not installed. Install with: pip install selenium")
                self._gui_engine_unavailable = True
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
            message = (
                f"{self._gui_driver} not installed — GUI scenario cannot run. "
                f"Install with: pip install testql[playwright] && playwright install chromium"
            )
            self.out.fail(f"GUI_START: {message}")
            self.errors.append(f"L{line.number}: {message}")
            self.results.append(StepResult(
                name=f'GUI_START "{app_path[:40]}"',
                status=StepStatus.ERROR,
                message=message,
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
            self._gui_page.set_default_timeout(self._gui_operation_timeout())
            self._gui_page.set_default_navigation_timeout(self._gui_operation_timeout(15000))
            self._gui_page.goto(app_path, timeout=self._gui_operation_timeout(15000))
            self._gui_app = (p, browser)
            self.out.step("🖥️", f"Playwright: Opened {app_path}")
        else:
            path = Path(app_path).expanduser()
            if path.is_file():
                from ._desktop import _desktop_api

                backend = _desktop_api().get_desktop_backend()
                pid = backend.launch(str(path), extra_args)
                self._gui_driver = "desktop"
                self._gui_app = backend
                self.out.step("🖥️", f"Desktop: launched {path.name} pid={pid}")
            else:
                self.out.fail(f"GUI_START: path not found: {app_path}")
                self.results.append(StepResult(
                    name=f'GUI_START "{app_path[:40]}"',
                    status=StepStatus.ERROR,
                    message="executable not found",
                ))
                return

        self.results.append(StepResult(
            name=f'GUI_START "{app_path[:40]}"', status=StepStatus.PASSED
        ))

    def _start_selenium(self, app_path: str, extra_args: str) -> None:
        """Start Selenium WebDriver."""
        from selenium import webdriver

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
                
                timeout = self._gui_operation_timeout(15000)
                try:
                    self._gui_page.goto(target, timeout=timeout)
                except Exception as nav_error:
                    # Chromium reports ERR_ABORTED when a client-side route or
                    # redirect interrupts the initial document request. In SPA
                    # apps page.url may be updated shortly after the exception.
                    if "net::ERR_ABORTED" not in str(nav_error):
                        raise
                    try:
                        self._gui_page.wait_for_url(target, wait_until="domcontentloaded", timeout=min(timeout, 5000))
                    except Exception as wait_error:
                        if not self._same_url_without_hash(self._gui_page.url, target):
                            raise nav_error from wait_error
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
        display_text = "***REDACTED***" if getattr(self, "is_secret_value", lambda value: False)(text) else text[:20]

        if self.dry_run:
            self.out.step("⌨️", f'GUI_INPUT "{selector}" "{display_text}" (dry-run)')
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

            self.out.step("⌨️", f'GUI_INPUT "{selector}" → "{display_text}"')
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

    def _cmd_gui_select(self, args: str, line: OqlLine) -> None:
        """GUI_SELECT "selector" "value" — select an option by value, then by label."""
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split(None, 1)
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: GUI_SELECT requires selector and value")
            self.results.append(StepResult(name="GUI_SELECT", status=StepStatus.ERROR, message="selector and value required"))
            return
        selector, value = parts[0], parts[1]
        name = f'GUI_SELECT "{selector}"'
        if self.dry_run:
            self.out.step("🔽", f'{name} → "{value}" (dry-run)')
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return
        if not self._gui_page:
            self.out.fail("GUI_SELECT: No active GUI session")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message="No active GUI session"))
            return
        try:
            if self._gui_driver == "playwright":
                selected = self._gui_page.select_option(selector, value=value)
                if not selected:
                    selected = self._gui_page.select_option(selector, label=value)
                if not selected:
                    raise ValueError(f"option not found: {value}")
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                from selenium.webdriver.support.ui import Select
                select = Select(self._gui_page.find_element(By.CSS_SELECTOR, selector))
                try:
                    select.select_by_value(value)
                except Exception:
                    select.select_by_visible_text(value)
            self.out.step("🔽", f'{name} → "{value}"')
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        except Exception as e:
            self.out.fail(f'{name} error: {e}')
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _cmd_select(self, args: str, line: OqlLine) -> None:
        self._cmd_gui_select(args, line)

    def _cmd_gui_submit(self, args: str, line: OqlLine) -> None:
        """GUI_SUBMIT "form-selector" — submit a form using browser-native validation."""
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()
        selector = parts[0] if parts else "form"
        name = f'GUI_SUBMIT "{selector}"'
        if self.dry_run:
            self.out.step("📨", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return
        if not self._gui_page:
            self.out.fail("GUI_SUBMIT: No active GUI session")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message="No active GUI session"))
            return
        try:
            if self._gui_driver == "playwright":
                self._gui_page.locator(selector).evaluate("form => form.requestSubmit()")
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                self._gui_page.find_element(By.CSS_SELECTOR, selector).submit()
            self.out.step("📨", name)
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
        except Exception as e:
            self.out.fail(f'{name} error: {e}')
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _cmd_submit(self, args: str, line: OqlLine) -> None:
        self._cmd_gui_submit(args, line)

    def _parse_scroll_args(self, args: str) -> tuple[str, int, int]:
        """Parse GUI_SCROLL args.

        Supported forms:
          GUI_SCROLL ".module-main-content" 900
          GUI_SCROLL ".module-main-content" y=900 x=0
          GUI_SCROLL 900
        """
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()

        selector = ""
        delta_x = 0
        delta_y = 900
        if parts and "=" not in parts[0]:
            if parts[0].lstrip("-").isdigit():
                delta_y = int(parts[0])
            else:
                selector = parts[0]

        for part in parts[1 if selector else 0:]:
            if part.lstrip("-").isdigit():
                delta_y = int(part)
                continue
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key = key.lower()
            try:
                number = int(float(value))
            except ValueError:
                continue
            if key in ("x", "dx", "deltax", "delta_x"):
                delta_x = number
            elif key in ("y", "dy", "deltay", "delta_y"):
                delta_y = number

        return selector, delta_x, delta_y

    def _cmd_gui_scroll(self, args: str, line: OqlLine) -> None:
        """GUI_SCROLL "selector" [delta_y] — Scroll page or scrollable element."""
        selector, delta_x, delta_y = self._parse_scroll_args(args)
        label_target = selector or "window"

        if self.dry_run:
            self.out.step("↕️", f'GUI_SCROLL "{label_target}" x={delta_x} y={delta_y} (dry-run)')
            self.results.append(StepResult(
                name=f'GUI_SCROLL "{label_target}"', status=StepStatus.PASSED
            ))
            return

        if not self._gui_page:
            self.out.fail("GUI_SCROLL: No active GUI session. Call GUI_START first")
            self.results.append(StepResult(
                name=f'GUI_SCROLL "{label_target}"',
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                if selector:
                    resolved_selector, element = self._find_element_with_logging(selector, "scroll")
                    if resolved_selector is None:
                        self.out.fail(f'GUI_SCROLL "{selector}": Element not found')
                        self.results.append(StepResult(
                            name=f'GUI_SCROLL "{selector}"',
                            status=StepStatus.FAILED,
                            message="Element not found after trying fallback selectors",
                        ))
                        return
                    element.evaluate(
                        "(el, delta) => el.scrollBy({ left: delta.x, top: delta.y, behavior: 'auto' })",
                        {"x": delta_x, "y": delta_y},
                    )
                    label_target = resolved_selector
                else:
                    self._gui_page.mouse.wheel(delta_x, delta_y)
            elif self._gui_driver == "selenium":
                if selector:
                    from selenium.webdriver.common.by import By
                    elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                    self._gui_page.execute_script(
                        "arguments[0].scrollBy(arguments[1], arguments[2]);",
                        elem,
                        delta_x,
                        delta_y,
                    )
                else:
                    self._gui_page.execute_script("window.scrollBy(arguments[0], arguments[1]);", delta_x, delta_y)

            self.out.step("↕️", f'GUI_SCROLL "{label_target}" x={delta_x} y={delta_y}')
            self.results.append(StepResult(
                name=f'GUI_SCROLL "{label_target}"', status=StepStatus.PASSED
            ))
        except Exception as e:
            self.out.fail(f'GUI_SCROLL "{label_target}" error: {e}')
            self.results.append(StepResult(
                name=f'GUI_SCROLL "{label_target}"',
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
            # Poll until the expected substring appears or the operation budget
            # elapses.  A single-shot read raced against asynchronous UI updates
            # (LLM calls, fetch-driven panels) and reported a FAILED assertion
            # while the text was still rendering.  When the text already matches,
            # the first iteration breaks immediately — no added latency on green
            # assertions.
            budget_ms = self._gui_operation_timeout()
            deadline = time.monotonic() + budget_ms / 1000.0
            per_read_timeout = min(budget_ms, 1000)
            actual = ""
            last_error: Exception | None = None
            while True:
                try:
                    if self._gui_driver == "playwright":
                        actual = self._gui_page.inner_text(selector, timeout=per_read_timeout)
                    elif self._gui_driver == "selenium":
                        from selenium.webdriver.common.by import By
                        elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
                        actual = elem.text
                    else:
                        actual = ""
                    last_error = None
                except Exception as read_error:
                    # Element not present/ready yet — keep polling within budget.
                    last_error = read_error
                    actual = ""
                if expected in actual or time.monotonic() >= deadline:
                    break
                time.sleep(0.1)

            if expected in actual:
                self.out.step("✅", f'GUI_ASSERT_TEXT "{selector}" → "{expected[:20]}"')
                self.results.append(StepResult(
                    name=f'GUI_ASSERT_TEXT "{selector}"', status=StepStatus.PASSED
                ))
            elif last_error is not None and not actual:
                raise last_error
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

    def _cmd_gui_eval(self, args: str, line: OqlLine) -> None:
        """GUI_EVAL "javascript" — Execute JavaScript in the active page.

        The script can be synchronous or async. In Playwright it is wrapped as
        an async function body, so `await fetch(...)` works directly.
        """
        script = args.strip()
        if (script.startswith('"') and script.endswith('"')) or (script.startswith("'") and script.endswith("'")):
            script = script[1:-1]

        if not script:
            self.out.fail(f"L{line.number}: GUI_EVAL requires JavaScript")
            self.results.append(StepResult(
                name="GUI_EVAL",
                status=StepStatus.ERROR,
                message="requires JavaScript",
            ))
            return

        name = f'GUI_EVAL "{script[:60]}"'

        if self.dry_run:
            self.out.step("🧩", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return

        if not self._gui_page:
            self.out.fail("GUI_EVAL: No active GUI session")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            attempts = 3
            result = None
            for attempt in range(1, attempts + 1):
                try:
                    if self._gui_driver == "playwright":
                        result = self._gui_page.evaluate(f"async () => {{ {script} }}")
                    elif self._gui_driver == "selenium":
                        result = self._gui_page.execute_script(script)
                    else:
                        result = None
                    break
                except Exception as eval_error:
                    if attempt >= attempts or not self._is_transient_browser_network_error(eval_error):
                        raise
                    time.sleep(0.25 * attempt)
            self.out.step("🧩", f"{name} → {str(result)[:80]}")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.PASSED,
                message=str(result) if result is not None else None,
            ))
        except Exception as e:
            self.out.fail(f"{name} error: {e}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _parse_count_assertion_args(self, args: str) -> tuple[str, str, int] | None:
        """Parse ASSERT_COUNT args.

        Supported forms:
          ASSERT_COUNT ".item" 12
          ASSERT_COUNT ".item" == 12
          ASSERT_COUNT ".item" >= 1
        """
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()
        if len(parts) == 2:
            selector, expected = parts
            return selector, "==", int(expected)
        if len(parts) >= 3:
            selector, op, expected = parts[0], parts[1], parts[2]
            return selector, op, int(expected)
        return None

    def _parse_wait_count_args(self, args: str) -> tuple[str, str, int, int] | None:
        """Parse WAIT_FOR_COUNT args.

        Supported forms:
          WAIT_FOR_COUNT ".item" 12
          WAIT_FOR_COUNT ".item" == 12 5000
          WAIT_FOR_COUNT ".item" >= 1 10000
        """
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()
        if len(parts) == 2:
            selector, expected = parts
            return selector, "==", int(expected), 5000
        if len(parts) >= 3:
            selector, op, expected = parts[0], parts[1], parts[2]
            timeout_ms = 5000
            if len(parts) >= 4:
                timeout_ms = int(parts[3])
            return selector, op, int(expected), timeout_ms
        return None

    @staticmethod
    def _compare_count(actual: int, op: str, expected: int) -> bool:
        if op in ("=", "==", "EQ"):
            return actual == expected
        if op in ("!=", "NE"):
            return actual != expected
        if op in (">", "GT"):
            return actual > expected
        if op in (">=", "GTE"):
            return actual >= expected
        if op in ("<", "LT"):
            return actual < expected
        if op in ("<=", "LTE"):
            return actual <= expected
        return False

    def _cmd_gui_assert_count(self, args: str, line: OqlLine) -> None:
        """GUI_ASSERT_COUNT "selector" [op] expected — Assert matching element count."""
        parsed = self._parse_count_assertion_args(args)
        if parsed is None:
            self.out.fail(f"L{line.number}: GUI_ASSERT_COUNT requires selector and expected count")
            self.results.append(StepResult(
                name="GUI_ASSERT_COUNT",
                status=StepStatus.ERROR,
                message="requires selector and expected count",
            ))
            return
        selector, op, expected = parsed
        name = f'GUI_ASSERT_COUNT "{selector}" {op} {expected}'

        if self.dry_run:
            self.out.step("🔢", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return

        if not self._gui_page:
            self.out.fail("GUI_ASSERT_COUNT: No active GUI session")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.ERROR,
                message="No active GUI session",
            ))
            return

        try:
            if self._gui_driver == "playwright":
                actual = self._gui_page.locator(selector).count()
            elif self._gui_driver == "selenium":
                from selenium.webdriver.common.by import By
                actual = len(self._gui_page.find_elements(By.CSS_SELECTOR, selector))
            else:
                actual = 0

            if self._compare_count(actual, op.upper(), expected):
                self.out.step("✅", f"{name} (actual: {actual})")
                self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            else:
                self.out.step("❌", f"{name} (actual: {actual})")
                self.results.append(StepResult(
                    name=name,
                    status=StepStatus.FAILED,
                    message=f"expected count {op} {expected}, actual {actual}",
                ))
        except Exception as e:
            self.out.fail(f"{name} error: {e}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _cmd_gui_wait_for_count(self, args: str, line: OqlLine) -> None:
        """GUI_WAIT_FOR_COUNT "selector" [op] expected [timeout_ms] — Poll DOM until count matches."""
        parsed = self._parse_wait_count_args(args)
        if parsed is None:
            self.out.fail(f"L{line.number}: GUI_WAIT_FOR_COUNT requires selector, expected count, optional timeout")
            self.results.append(StepResult(
                name="GUI_WAIT_FOR_COUNT",
                status=StepStatus.ERROR,
                message="requires selector, expected count, optional timeout",
            ))
            return
        selector, op, expected, timeout_ms = parsed
        name = f'GUI_WAIT_FOR_COUNT "{selector}" {op} {expected} timeout={timeout_ms}ms'

        if self.dry_run:
            self.out.step("⏳", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return

        if not self._gui_page:
            self.out.fail("GUI_WAIT_FOR_COUNT: No active GUI session")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message="No active GUI session"))
            return

        deadline = time.monotonic() + max(timeout_ms, 0) / 1000
        actual = 0
        try:
            while True:
                if self._gui_driver == "playwright":
                    actual = self._gui_page.locator(selector).count()
                elif self._gui_driver == "selenium":
                    from selenium.webdriver.common.by import By
                    actual = len(self._gui_page.find_elements(By.CSS_SELECTOR, selector))
                if self._compare_count(actual, op.upper(), expected):
                    self.out.step("✅", f"{name} (actual: {actual})")
                    self.results.append(StepResult(name=name, status=StepStatus.PASSED))
                    return
                if time.monotonic() >= deadline:
                    break
                time.sleep(0.1)
            self.out.step("❌", f"{name} (actual: {actual})")
            self.results.append(StepResult(
                name=name,
                status=StepStatus.FAILED,
                message=f"expected count {op} {expected}, actual {actual}",
            ))
        except Exception as e:
            self.out.fail(f"{name} error: {e}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _cmd_gui_assert_url_param(self, args: str, line: OqlLine) -> None:
        """GUI_ASSERT_URL_PARAM "name" "value" — Assert current URL query parameter."""
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()
        if len(parts) < 2:
            self.out.fail(f"L{line.number}: GUI_ASSERT_URL_PARAM requires parameter name and expected value")
            self.results.append(StepResult(
                name="GUI_ASSERT_URL_PARAM",
                status=StepStatus.ERROR,
                message="requires parameter name and expected value",
            ))
            return
        param, expected = parts[0], parts[1]
        name = f'GUI_ASSERT_URL_PARAM "{param}" == "{expected}"'

        if self.dry_run:
            self.out.step("🔗", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return

        if not self._gui_page:
            self.out.fail("GUI_ASSERT_URL_PARAM: No active GUI session")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message="No active GUI session"))
            return

        try:
            if self._gui_driver == "playwright":
                url = self._gui_page.url
            elif self._gui_driver == "selenium":
                url = self._gui_page.current_url
            else:
                url = ""
            actual = parse_qs(urlparse(url).query).get(param, [""])[0]
            if actual == expected:
                self.out.step("✅", f'{name} (actual: "{actual}")')
                self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            else:
                self.out.step("❌", f'{name} (actual: "{actual}")')
                self.results.append(StepResult(
                    name=name,
                    status=StepStatus.FAILED,
                    message=f'expected "{expected}", actual "{actual}"',
                ))
        except Exception as e:
            self.out.fail(f"{name} error: {e}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

    def _parse_value_assertion_args(self, args: str) -> tuple[str, str, str] | None:
        """Parse ASSERT_VALUE args.

        Supported forms:
          ASSERT_VALUE "#kind" "36m"
          ASSERT_VALUE "#kind" == "36m"
          ASSERT_VALUE "#kind" != ""
        """
        try:
            parts = shlex.split(args)
        except ValueError:
            parts = args.strip().split()
        if len(parts) == 2:
            selector, expected = parts
            return selector, "==", expected
        if len(parts) >= 3:
            selector, op, expected = parts[0], parts[1], parts[2]
            return selector, op, expected
        return None

    @staticmethod
    def _compare_value(actual: str, op: str, expected: str) -> bool:
        if op in ("=", "==", "EQ"):
            return actual == expected
        if op in ("!=", "NE"):
            return actual != expected
        if op in ("CONTAINS", "~"):
            return expected in actual
        if op in ("NOT_CONTAINS", "!~"):
            return expected not in actual
        return False

    def _read_gui_value(self, selector: str) -> str:
        if self._gui_driver == "playwright":
            locator = self._gui_page.locator(selector).first
            try:
                return locator.input_value()
            except Exception:
                value = locator.get_attribute("value")
                return value or ""
        if self._gui_driver == "selenium":
            from selenium.webdriver.common.by import By

            elem = self._gui_page.find_element(By.CSS_SELECTOR, selector)
            value = elem.get_attribute("value")
            return value or ""
        return ""

    def _cmd_gui_assert_value(self, args: str, line: OqlLine) -> None:
        """GUI_ASSERT_VALUE "selector" [op] expected — Assert form control value."""
        parsed = self._parse_value_assertion_args(args)
        if parsed is None:
            self.out.fail(f"L{line.number}: GUI_ASSERT_VALUE requires selector and expected value")
            self.results.append(StepResult(
                name="GUI_ASSERT_VALUE",
                status=StepStatus.ERROR,
                message="requires selector and expected value",
            ))
            return
        selector, op, expected = parsed
        name = f'GUI_ASSERT_VALUE "{selector}" {op} "{expected}"'

        if self.dry_run:
            self.out.step("🔎", f"{name} (dry-run)")
            self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            return

        if not self._gui_page:
            self.out.fail("GUI_ASSERT_VALUE: No active GUI session")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message="No active GUI session"))
            return

        try:
            actual = self._read_gui_value(selector)
            if self._compare_value(actual, op.upper(), expected):
                self.out.step("✅", f'{name} (actual: "{actual}")')
                self.results.append(StepResult(name=name, status=StepStatus.PASSED))
            else:
                self.out.step("❌", f'{name} (actual: "{actual}")')
                self.results.append(StepResult(
                    name=name,
                    status=StepStatus.FAILED,
                    message=f'expected "{expected}", actual "{actual}"',
                ))
        except Exception as e:
            self.out.fail(f"{name} error: {e}")
            self.results.append(StepResult(name=name, status=StepStatus.ERROR, message=str(e)))

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
                self._close_gui_session()
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

    def _close_gui_session(self) -> None:
        """Close an active browser without recording an extra TestQL step."""
        app = self._gui_app
        driver = self._gui_driver
        self._gui_app = None
        self._gui_page = None
        if not app:
            return
        if driver == "playwright":
            playwright, browser = app
            try:
                browser.close()
            finally:
                playwright.stop()
        elif driver == "selenium":
            app.quit()

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

    def _cmd_scroll(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_SCROLL."""
        self._cmd_gui_scroll(args, line)

    def _cmd_wheel(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_SCROLL."""
        self._cmd_gui_scroll(args, line)

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

    def _cmd_assert_count(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_COUNT."""
        self._cmd_gui_assert_count(args, line)

    def _cmd_count(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_COUNT."""
        self._cmd_gui_assert_count(args, line)

    def _cmd_wait_for_count(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_WAIT_FOR_COUNT."""
        self._cmd_gui_wait_for_count(args, line)

    def _cmd_assert_url_param(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_URL_PARAM."""
        self._cmd_gui_assert_url_param(args, line)

    def _cmd_assert_value(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_VALUE."""
        self._cmd_gui_assert_value(args, line)

    def _cmd_value(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_ASSERT_VALUE."""
        self._cmd_gui_assert_value(args, line)

    def _cmd_eval(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_EVAL."""
        self._cmd_gui_eval(args, line)

    def _cmd_capture(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_CAPTURE."""
        self._cmd_gui_capture(args, line)

    def _cmd_screenshot(self, args: str, line: OqlLine) -> None:
        """Alias for GUI_CAPTURE."""
        self._cmd_gui_capture(args, line)

#!/usr/bin/env python3
"""
Page Analyzer for TestQL - Comprehensive page analysis and logging
Analyzes page content, detects errors, captures screenshots, generates reports
"""

import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


class PageAnalyzer:
    """
    Comprehensive page analyzer for TestQL visual demos.

    Features:
    - HTTP status detection (200, 404, 500, etc.)
    - DOM analysis (element counts, structure)
    - Error detection (console errors, failed resources)
    - Screenshot capture with metadata
    - Performance metrics (load time, size)
    - Content validation (missing elements, broken links)
    - Detailed JSON/HTML reports
    """

    def __init__(self, output_dir: Path = Path("./page-analysis")):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.analysis_results = []
        self.start_time = time.time()

        # Counters
        self.pages_analyzed = 0
        self.errors_found = 0
        self.warnings_found = 0

    async def analyze_page(
        self,
        page,
        url: str,
        step_number: int,
        test_name: str = "encoder_test"
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of current page.

        Returns detailed analysis including:
        - HTTP status
        - Page title and URL
        - DOM element counts
        - Console errors
        - Failed network requests
        - Screenshots
        - Performance metrics
        """
        analysis_start = time.time()

        print(f"\n{'='*80}")
        print(f"📊 ANALYZING PAGE: {url}")
        print(f"{'='*80}")

        result = {
            "step": step_number,
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "status": "unknown",
            "errors": [],
            "warnings": [],
            "metrics": {},
            "dom": {},
            "screenshots": [],
        }

        try:
            # 1. HTTP Response Analysis
            print("🔍 Checking HTTP response...")
            response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)

            if response:
                result["status"] = response.status
                result["status_text"] = response.status_text

                if response.status == 200:
                    print(f"  ✅ HTTP {response.status} OK")
                elif response.status == 404:
                    print(f"  ❌ HTTP {response.status} NOT FOUND")
                    result["errors"].append(f"Page not found: {url}")
                    self.errors_found += 1
                elif response.status >= 500:
                    print(f"  ❌ HTTP {response.status} SERVER ERROR")
                    result["errors"].append(f"Server error: {response.status}")
                    self.errors_found += 1
                elif response.status >= 400:
                    print(f"  ⚠️  HTTP {response.status} CLIENT ERROR")
                    result["warnings"].append(f"Client error: {response.status}")
                    self.warnings_found += 1
                else:
                    print(f"  ℹ️  HTTP {response.status} {response.status_text}")
            else:
                print("  ⚠️  No response received")
                result["warnings"].append("No HTTP response")
                self.warnings_found += 1

            # Wait for page to stabilize
            await page.wait_for_load_state("networkidle", timeout=5000)

            # 2. Page Title and URL
            print("\n📄 Page Information:")
            title = await page.title()
            current_url = page.url
            result["title"] = title
            result["final_url"] = current_url
            print(f"  • Title: {title}")
            print(f"  • Final URL: {current_url}")

            if current_url != url:
                print(f"  ℹ️  Redirected from: {url}")
                result["redirected"] = True

            # 3. DOM Analysis
            print("\n🌳 DOM Structure Analysis:")
            dom_stats = await page.evaluate("""
                () => {
                    return {
                        total_elements: document.querySelectorAll('*').length,
                        buttons: document.querySelectorAll('button').length,
                        inputs: document.querySelectorAll('input').length,
                        tables: document.querySelectorAll('table').length,
                        forms: document.querySelectorAll('form').length,
                        links: document.querySelectorAll('a').length,
                        images: document.querySelectorAll('img').length,
                        body_text_length: document.body.innerText.length,
                        has_header: !!document.querySelector('header, .header'),
                        has_footer: !!document.querySelector('footer, .footer'),
                        has_menu: !!document.querySelector('nav, .menu, .navigation'),
                    }
                }
            """)

            result["dom"] = dom_stats
            print(f"  • Total elements: {dom_stats['total_elements']}")
            print(f"  • Buttons: {dom_stats['buttons']}")
            print(f"  • Inputs: {dom_stats['inputs']}")
            print(f"  • Tables: {dom_stats['tables']}")
            print(f"  • Forms: {dom_stats['forms']}")
            print(f"  • Links: {dom_stats['links']}")
            print(f"  • Images: {dom_stats['images']}")
            print(f"  • Text length: {dom_stats['body_text_length']} chars")

            # Check for empty page
            if dom_stats['total_elements'] < 10:
                print("  ⚠️  Very few elements - page might be empty")
                result["warnings"].append("Page has very few DOM elements")
                self.warnings_found += 1

            if dom_stats['body_text_length'] < 50:
                print("  ⚠️  Very little text content")
                result["warnings"].append("Page has minimal text content")
                self.warnings_found += 1

            # 4. Console Errors
            print("\n🐛 Console Errors:")
            console_errors = await page.evaluate("""
                () => {
                    // Return any errors caught by window.onerror
                    return window.__testql_console_errors || [];
                }
            """)

            if console_errors and len(console_errors) > 0:
                print(f"  ❌ Found {len(console_errors)} console error(s)")
                for err in console_errors[:5]:  # Show first 5
                    print(f"    • {err}")
                    result["errors"].append(f"Console: {err}")
                self.errors_found += len(console_errors)
            else:
                print("  ✅ No console errors detected")

            # 5. Network Errors (failed resources)
            print("\n🌐 Network Resources:")
            failed_resources = await page.evaluate("""
                () => {
                    return window.__testql_failed_resources || [];
                }
            """)

            if failed_resources and len(failed_resources) > 0:
                print(f"  ⚠️  Found {len(failed_resources)} failed resource(s)")
                for res in failed_resources[:5]:
                    print(f"    • {res}")
                    result["warnings"].append(f"Failed resource: {res}")
                self.warnings_found += len(failed_resources)
            else:
                print("  ✅ All resources loaded successfully")

            # 6. Encoder Mode Detection
            print("\n⚙️  Encoder Mode Detection:")
            encoder_check = await page.evaluate("""
                () => {
                    const url = window.location.href;
                    const hasEncoderParam = url.includes('mode=encoder');
                    const hasKeyboardParam = url.includes('mode=keyboard');

                    // Check for encoder indicators in DOM
                    const encoderIndicator = document.querySelector('.encoder-mode-indicator, [data-encoder-active]');

                    return {
                        url_param_encoder: hasEncoderParam,
                        url_param_keyboard: hasKeyboardParam,
                        encoder_indicator_present: !!encoderIndicator,
                    };
                }
            """)

            result["encoder_mode"] = encoder_check

            if encoder_check["url_param_encoder"]:
                print("  ✅ Encoder mode URL parameter detected")
            elif encoder_check["url_param_keyboard"]:
                print("  ✅ Keyboard mode URL parameter detected")
            else:
                print("  ℹ️  No encoder/keyboard mode parameter")

            # 7. Performance Metrics
            print("\n⚡ Performance Metrics:")
            perf_metrics = await page.evaluate("""
                () => {
                    const perf = performance.getEntriesByType('navigation')[0];
                    if (perf) {
                        return {
                            load_time: Math.round(perf.loadEventEnd - perf.fetchStart),
                            dom_content_loaded: Math.round(perf.domContentLoadedEventEnd - perf.fetchStart),
                            dom_interactive: Math.round(perf.domInteractive - perf.fetchStart),
                        };
                    }
                    return {};
                }
            """)

            result["performance"] = perf_metrics

            if perf_metrics.get("load_time"):
                print(f"  • Load time: {perf_metrics['load_time']}ms")
                print(f"  • DOM ready: {perf_metrics['dom_content_loaded']}ms")
                print(f"  • Interactive: {perf_metrics['dom_interactive']}ms")

                if perf_metrics["load_time"] > 5000:
                    print("  ⚠️  Slow page load (>5s)")
                    result["warnings"].append("Slow page load time")
                    self.warnings_found += 1

            # 8. Screenshot Capture
            print("\n📸 Capturing Screenshots:")
            screenshot_base = f"step_{step_number:03d}_{test_name}"

            # Full page screenshot
            screenshot_path = self.output_dir / f"{screenshot_base}_full.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"  ✅ Full page: {screenshot_path}")
            result["screenshots"].append(str(screenshot_path))

            # Viewport screenshot
            viewport_path = self.output_dir / f"{screenshot_base}_viewport.png"
            await page.screenshot(path=str(viewport_path), full_page=False)
            print(f"  ✅ Viewport: {viewport_path}")
            result["screenshots"].append(str(viewport_path))

            # 9. Analysis Duration
            analysis_duration = (time.time() - analysis_start) * 1000
            result["analysis_duration_ms"] = round(analysis_duration)

            print(f"\n✅ Analysis completed in {analysis_duration:.0f}ms")

        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            result["errors"].append(f"Analysis exception: {str(e)}")
            result["status"] = "error"
            self.errors_found += 1

        # Store result
        self.analysis_results.append(result)
        self.pages_analyzed += 1

        print(f"{'='*80}\n")

        return result

    def generate_report(self, filename: str = "analysis_report.json"):
        """Generate comprehensive analysis report."""
        report = {
            "summary": {
                "total_pages": self.pages_analyzed,
                "total_errors": self.errors_found,
                "total_warnings": self.warnings_found,
                "duration_seconds": round(time.time() - self.start_time, 2),
                "timestamp": datetime.now().isoformat(),
            },
            "pages": self.analysis_results,
        }

        report_path = self.output_dir / filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n{'='*80}")
        print("📊 ANALYSIS REPORT")
        print(f"{'='*80}")
        print(f"✅ Total Pages Analyzed: {self.pages_analyzed}")
        print(f"❌ Total Errors: {self.errors_found}")
        print(f"⚠️  Total Warnings: {self.warnings_found}")
        print(f"⏱️  Total Duration: {report['summary']['duration_seconds']}s")
        print(f"📄 Report saved: {report_path}")
        print(f"{'='*80}\n")

        return report

    def generate_html_report(self, filename: str = "analysis_report.html"):
        """Generate HTML report with visual presentation."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>TestQL Page Analysis Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .page-result {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .status-ok {{ color: #4CAF50; }}
        .status-error {{ color: #f44336; }}
        .status-warning {{ color: #ff9800; }}
        .metric {{ display: inline-block; margin-right: 20px; }}
        .screenshot {{ max-width: 200px; margin: 10px; cursor: pointer; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 0; }}
        .errors {{ background: #ffebee; padding: 10px; border-left: 4px solid #f44336; }}
        .warnings {{ background: #fff3e0; padding: 10px; border-left: 4px solid #ff9800; }}
    </style>
</head>
<body>
    <h1>📊 TestQL Page Analysis Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <div class="metric"><strong>Pages:</strong> {self.pages_analyzed}</div>
        <div class="metric"><strong>Errors:</strong> <span class="status-error">{self.errors_found}</span></div>
        <div class="metric"><strong>Warnings:</strong> <span class="status-warning">{self.warnings_found}</span></div>
        <div class="metric"><strong>Duration:</strong> {round(time.time() - self.start_time, 2)}s</div>
    </div>
"""

        for result in self.analysis_results:
            status_class = "status-ok" if result["status"] == 200 else "status-error"

            html += f"""
    <div class="page-result">
        <h2>Step {result['step']}: {result.get('title', 'Unknown')}</h2>
        <p><strong>URL:</strong> <code>{result['url']}</code></p>
        <p><strong>Status:</strong> <span class="{status_class}">{result['status']}</span></p>

        <p><strong>DOM Elements:</strong> {result['dom'].get('total_elements', 0)}
           (Buttons: {result['dom'].get('buttons', 0)}, Tables: {result['dom'].get('tables', 0)})</p>
"""

            if result.get("errors"):
                html += f"""
        <div class="errors">
            <strong>❌ Errors:</strong>
            <ul>
                {''.join(f'<li>{err}</li>' for err in result['errors'])}
            </ul>
        </div>
"""

            if result.get("warnings"):
                html += f"""
        <div class="warnings">
            <strong>⚠️ Warnings:</strong>
            <ul>
                {''.join(f'<li>{warn}</li>' for warn in result['warnings'])}
            </ul>
        </div>
"""

            if result.get("screenshots"):
                html += """
        <div>
            <strong>📸 Screenshots:</strong><br>
"""
                for screenshot in result["screenshots"]:
                    html += f'            <img src="{Path(screenshot).name}" class="screenshot"><br>\n'
                html += "        </div>\n"

            html += "    </div>\n"

        html += """
</body>
</html>
"""

        report_path = self.output_dir / filename
        with open(report_path, 'w') as f:
            f.write(html)

        print(f"📄 HTML Report saved: {report_path}")

        return report_path


# Install console error tracking script
async def install_error_tracking(page):
    """Install error tracking in page context."""
    await page.add_init_script("""
        window.__testql_console_errors = [];
        window.__testql_failed_resources = [];

        // Capture console errors
        const originalError = console.error;
        console.error = function(...args) {
            window.__testql_console_errors.push(args.join(' '));
            originalError.apply(console, args);
        };

        // Capture failed resources
        window.addEventListener('error', (e) => {
            if (e.target !== window) {
                window.__testql_failed_resources.push(e.target.src || e.target.href || 'unknown');
            }
        }, true);
    """)

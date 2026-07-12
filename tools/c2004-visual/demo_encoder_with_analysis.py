#!/usr/bin/env python3
"""
Encoder Testing with Full Page Analysis
Combines encoder testing with comprehensive page analysis and reporting
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode
from page_analyzer import PageAnalyzer, install_error_tracking


async def test_encoder_with_analysis():
    """Test encoder with full page analysis."""
    from playwright.async_api import async_playwright

    print("\n" + "=" * 80)
    print("ENCODER TESTING WITH COMPREHENSIVE PAGE ANALYSIS")
    print("=" * 80)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=150,
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # Install error tracking
        await install_error_tracking(page)

        demo = VisualDemoMode(
            page=page,
            speed="medium",
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./encoder-analysis-screenshots"),
        )

        # Create analyzer
        analyzer = PageAnalyzer(output_dir=Path("./encoder-analysis-reports"))

        await demo.inject_demo_styles()
        print("✓ Visual demo + Page analyzer ready\n")

        modules = [
            ("connect-id", "Connect-ID"),
            ("connect-data", "Connect-Data"),
            ("connect-reports", "Connect-Reports"),
            ("connect-manager", "Connect-Manager"),
            ("connect-config", "Connect-Config"),
        ]

        step_number = 1

        try:
            for module, name in modules:
                print(f"\n{'#'*80}")
                print(f"TESTING MODULE: {name}")
                print(f"{'#'*80}\n")

                url = f"http://localhost:8100/{module}?mode=encoder"

                # Navigate
                await demo.show_step(f"Loading {name}", "info")
                await asyncio.sleep(0.1)

                # ANALYZE PAGE
                analysis = await analyzer.analyze_page(
                    page=page,
                    url=url,
                    step_number=step_number,
                    test_name=f"{module}_encoder"
                )

                # Check analysis results
                if analysis["status"] != 200:
                    print(f"❌ Page failed to load: HTTP {analysis['status']}")
                elif analysis["errors"]:
                    print(f"❌ Found {len(analysis['errors'])} errors on page")
                elif analysis["warnings"]:
                    print(f"⚠️  Found {len(analysis['warnings'])} warnings on page")
                else:
                    print(f"✅ Page analysis passed - no issues")

                # Test encoder functionality
                print(f"\n⌨️  Testing encoder on {name}...")

                # Activate
                await demo.show_step(f"Activate encoder (Ctrl+E)", "info")
                await asyncio.sleep(0.1)
                await page.keyboard.press("Control+e")
                await asyncio.sleep(0.1)
                await demo.take_screenshot(f"{module}_activated")
                await asyncio.sleep(1)

                # Navigate
                await demo.show_step(f"Navigate down (Arrow)", "info")
                await asyncio.sleep(0.1)
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.1)
                await demo.take_screenshot(f"{module}_navigated")
                await asyncio.sleep(1)

                # Deactivate
                await demo.show_step(f"Deactivate (Escape)", "info")
                await asyncio.sleep(0.1)
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.1)
                await demo.take_screenshot(f"{module}_deactivated")

                print(f"✅ {name} encoder test complete\n")

                step_number += 1
                await asyncio.sleep(1)

            # Generate reports
            print("\n" + "=" * 80)
            print("GENERATING ANALYSIS REPORTS")
            print("=" * 80 + "\n")

            json_report = analyzer.generate_report("encoder_analysis_report.json")
            html_report = analyzer.generate_html_report("encoder_analysis_report.html")

            print(f"\n📊 FINAL RESULTS:")
            print(f"  • Pages analyzed: {analyzer.pages_analyzed}")
            print(f"  • Errors found: {analyzer.errors_found}")
            print(f"  • Warnings found: {analyzer.warnings_found}")
            print(f"  • JSON report: {json_report}")
            print(f"  • HTML report: {html_report}")

            # List all issues
            if analyzer.errors_found > 0:
                print(f"\n❌ ERRORS SUMMARY:")
                for result in analyzer.analysis_results:
                    if result.get("errors"):
                        print(f"  • {result['url']}:")
                        for err in result["errors"][:3]:
                            print(f"    - {err}")

            if analyzer.warnings_found > 0:
                print(f"\n⚠️  WARNINGS SUMMARY:")
                for result in analyzer.analysis_results:
                    if result.get("warnings"):
                        print(f"  • {result['url']}:")
                        for warn in result["warnings"][:3]:
                            print(f"    - {warn}")

            print("\n⏸️  Browser stays open for 15 seconds...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

        finally:
            print("\n🔚 Closing browser...")
            await browser.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║     ENCODER TESTING WITH COMPREHENSIVE PAGE ANALYSIS                   ║
║                                                                        ║
║  For each page, analyzes:                                              ║
║  ✓ HTTP status (200, 404, 500, etc.)                                   ║
║  ✓ DOM structure (elements, buttons, tables)                           ║
║  ✓ Console errors                                                      ║
║  ✓ Failed network resources                                            ║
║  ✓ Performance metrics (load time)                                     ║
║  ✓ Encoder mode detection                                              ║
║  ✓ Screenshots (full page + viewport)                                  ║
║  ✓ Detailed JSON + HTML reports                                        ║
║                                                                        ║
║  Generates:                                                            ║
║  • encoder_analysis_report.json                                        ║
║  • encoder_analysis_report.html                                        ║
║  • encoder-analysis-screenshots/                                       ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(test_encoder_with_analysis())

#!/usr/bin/env python3
"""
TestQL CLI - Command Line Interface for TestQL Testing Framework

Simple commands to run tests, analyze pages, and generate reports.
"""

import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# Add testql to path
sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode
from page_analyzer import PageAnalyzer, install_error_tracking


async def run_encoder_test(
    base_url: str = "http://localhost:8100",
    modules: Optional[list] = None,
    with_analysis: bool = True,
    headless: bool = False,
    speed: str = "medium",
):
    """Run encoder mode testing."""
    from playwright.async_api import async_playwright

    if modules is None:
        modules = [
            "connect-id",
            "connect-data",
            "connect-reports",
            "connect-manager",
            "connect-config",
        ]

    print(f"\n🚀 Starting TestQL Encoder Test")
    print(f"   Base URL: {base_url}")
    print(f"   Modules: {len(modules)}")
    print(f"   Analysis: {'ON' if with_analysis else 'OFF'}")
    print(f"   Headless: {'ON' if headless else 'OFF'}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=100)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        if with_analysis:
            await install_error_tracking(page)

        demo = VisualDemoMode(
            page=page,
            speed=speed,
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./testql-screenshots"),
        )

        analyzer = PageAnalyzer(output_dir=Path("./testql-reports")) if with_analysis else None

        await demo.inject_demo_styles()

        results = {"passed": 0, "failed": 0, "warnings": 0}

        for i, module in enumerate(modules, 1):
            print(f"\n[{i}/{len(modules)}] Testing {module}...")

            url = f"{base_url}/{module}?mode=encoder"

            if analyzer:
                analysis = await analyzer.analyze_page(
                    page=page,
                    url=url,
                    step_number=i,
                    test_name=f"{module}_test"
                )

                if analysis["status"] == 200 and not analysis["errors"]:
                    results["passed"] += 1
                    print(f"✅ {module}: PASSED")
                elif analysis["errors"]:
                    results["failed"] += 1
                    print(f"❌ {module}: FAILED ({len(analysis['errors'])} errors)")
                else:
                    results["warnings"] += 1
                    print(f"⚠️  {module}: WARNING")
            else:
                # Simple navigation test
                await demo.demo_navigate(url)
                results["passed"] += 1

            # Quick encoder test
            await asyncio.sleep(0.1)
            await page.keyboard.press("Control+e")
            await asyncio.sleep(0.5)
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        if analyzer:
            analyzer.generate_report("testql_report.json")
            analyzer.generate_html_report("testql_report.html")

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed:   {results['passed']}")
        print(f"❌ Failed:   {results['failed']}")
        print(f"⚠️  Warnings: {results['warnings']}")
        print(f"{'='*60}\n")

        await browser.close()

        return results


async def run_page_analysis(url: str, output_dir: str = "./testql-reports"):
    """Analyze a single page."""
    from playwright.async_api import async_playwright

    print(f"\n🔍 Analyzing page: {url}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await install_error_tracking(page)

        analyzer = PageAnalyzer(output_dir=Path(output_dir))

        analysis = await analyzer.analyze_page(
            page=page,
            url=url,
            step_number=1,
            test_name="single_page_analysis"
        )

        analyzer.generate_report("page_analysis.json")
        analyzer.generate_html_report("page_analysis.html")

        print(f"\n📊 Analysis Results:")
        print(f"   Status: {analysis['status']}")
        print(f"   Errors: {len(analysis['errors'])}")
        print(f"   Warnings: {len(analysis['warnings'])}")
        print(f"   DOM Elements: {analysis['dom'].get('total_elements', 0)}")
        print(f"   Load Time: {analysis['performance'].get('load_time', 0)}ms")

        await browser.close()

        return analysis


async def run_wheel_test(base_url: str = "http://localhost:8100"):
    """Test wheel scrolling for encoder."""
    from playwright.async_api import async_playwright

    print(f"\n🔄 Testing Wheel Scroll for Encoder Mode\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=150)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        demo = VisualDemoMode(
            page=page,
            speed="medium",
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./wheel-test-screenshots"),
        )

        await demo.inject_demo_styles()

        url = f"{base_url}/connect-id?mode=encoder"
        await demo.demo_navigate(url)

        print("⌨️  Activating encoder...")
        await page.keyboard.press("Control+e")
        await asyncio.sleep(1)

        print("🔄 Wheel RIGHT (5 scrolls)...")
        for i in range(5):
            await page.mouse.wheel(0, 100)
            await asyncio.sleep(0.15)

        await demo.take_screenshot("wheel_right")

        print("🔄 Wheel LEFT (5 scrolls)...")
        for i in range(5):
            await page.mouse.wheel(0, -100)
            await asyncio.sleep(0.15)

        await demo.take_screenshot("wheel_left")

        print("\n✅ Wheel test completed!")
        print(f"   Screenshots: {demo.screenshots_dir}\n")

        await asyncio.sleep(5)
        await browser.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TestQL - Visual Testing Framework for C2004",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run encoder test with analysis
  testql encoder

  # Test specific modules
  testql encoder --modules connect-id connect-data

  # Analyze single page
  testql analyze http://localhost:8100/connect-id

  # Test wheel scrolling
  testql wheel

  # Run in headless mode
  testql encoder --headless

  # Fast run without analysis
  testql encoder --no-analysis --fast
        """
    )

    parser.add_argument(
        "command",
        choices=["encoder", "analyze", "wheel", "help"],
        help="Command to run"
    )

    parser.add_argument(
        "target",
        nargs="?",
        help="Target URL (for 'analyze' command) or modules"
    )

    parser.add_argument(
        "--modules",
        nargs="+",
        help="Modules to test (default: all)"
    )

    parser.add_argument(
        "--base-url",
        default="http://localhost:8100",
        help="Base URL (default: http://localhost:8100)"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )

    parser.add_argument(
        "--no-analysis",
        action="store_true",
        help="Skip page analysis"
    )

    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode (speed=fast)"
    )

    parser.add_argument(
        "--output",
        default="./testql-reports",
        help="Output directory (default: ./testql-reports)"
    )

    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        return

    speed = "fast" if args.fast else "medium"

    try:
        if args.command == "encoder":
            asyncio.run(run_encoder_test(
                base_url=args.base_url,
                modules=args.modules,
                with_analysis=not args.no_analysis,
                headless=args.headless,
                speed=speed,
            ))

        elif args.command == "analyze":
            if not args.target:
                print("❌ Error: URL required for 'analyze' command")
                print("   Usage: testql analyze <url>")
                sys.exit(1)

            asyncio.run(run_page_analysis(
                url=args.target,
                output_dir=args.output
            ))

        elif args.command == "wheel":
            asyncio.run(run_wheel_test(base_url=args.base_url))

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

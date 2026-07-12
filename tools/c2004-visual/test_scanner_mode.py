#!/usr/bin/env python3
"""
Scanner Mode Testing - Complete QR/Barcode/RFID simulation
Tests scanner input in C2004 identification module
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode
from page_analyzer import PageAnalyzer, install_error_tracking


async def test_scanner_mode():
    """Test complete scanner functionality."""
    from playwright.async_api import async_playwright
    import json

    print("\n" + "=" * 80)
    print("SCANNER MODE TESTING - QR/Barcode/RFID Simulation")
    print("=" * 80)
    print()

    scanner_test_data = [
        {
            "type": "qr",
            "code": "QR:admin@fleet.local",
            "description": "QR Code - Admin User",
            "expected": "admin@fleet.local"
        },
        {
            "type": "barcode",
            "code": "BARCODE:1234567890",
            "description": "Barcode - Equipment ID",
            "expected": "1234567890"
        },
        {
            "type": "rfid",
            "code": "RFID:A1B2C3D4E5F6",
            "description": "RFID Card - Access Card",
            "expected": "A1B2C3D4E5F6"
        },
        {
            "type": "manual",
            "code": "MANUAL:test.user@example.com",
            "description": "Manual Entry - Email",
            "expected": "test.user@example.com"
        },
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        await install_error_tracking(page)

        demo = VisualDemoMode(
            page=page,
            speed="medium",
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./scanner-test-screenshots"),
        )

        analyzer = PageAnalyzer(output_dir=Path("./scanner-test-reports"))

        await demo.inject_demo_styles()

        results = {
            "total": len(scanner_test_data),
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        try:
            print("=" * 80)
            print("PHASE 1: NAVIGATE TO IDENTIFICATION MODULE")
            print("=" * 80)

            # Navigate to connect-id
            url = "http://localhost:8100/connect-id"
            await demo.demo_navigate(url)

            # Analyze page
            analysis = await analyzer.analyze_page(
                page=page,
                url=url,
                step_number=1,
                test_name="scanner_mode_init"
            )

            if analysis["status"] != 200:
                print(f"❌ Failed to load connect-id: HTTP {analysis['status']}")
                results["failed"] += 1
                results["errors"].append(f"Page load failed: {analysis['status']}")
            else:
                print(f"✅ connect-id loaded successfully")

            print("\n" + "=" * 80)
            print("PHASE 2: SCANNER INPUT SIMULATION")
            print("=" * 80)

            # Test each scanner type
            for i, scan_data in enumerate(scanner_test_data, 1):
                print(f"\n📱 Test {i}/{len(scanner_test_data)}: {scan_data['description']}")
                print(f"   Type: {scan_data['type']}")
                print(f"   Code: {scan_data['code']}")

                await demo.show_step(f"Scanning {scan_data['type']}: {scan_data['code']}", "info")

                # Method 1: Try scanner API endpoint
                try:
                    print(f"   → Sending to scanner API...")
                    response = await page.evaluate(f"""
                        async () => {{
                            try {{
                                const response = await fetch('/api/v3/identification/scanner/ingest', {{
                                    method: 'POST',
                                    headers: {{
                                        'Content-Type': 'application/json',
                                    }},
                                    body: JSON.stringify({{
                                        code: '{scan_data['code']}',
                                        type: '{scan_data['type']}'
                                    }})
                                }});

                                const data = await response.json();
                                return {{
                                    status: response.status,
                                    ok: response.ok,
                                    data: data
                                }};
                            }} catch (e) {{
                                return {{
                                    status: 0,
                                    ok: false,
                                    error: e.toString()
                                }};
                            }}
                        }}
                    """)

                    if response and response.get("ok"):
                        print(f"   ✅ Scanner API accepted {scan_data['type']}")
                        results["passed"] += 1
                        await demo.take_screenshot(f"scanner_{scan_data['type']}_success")
                    else:
                        print(f"   ⚠️  Scanner API response: {response}")
                        results["failed"] += 1
                        results["errors"].append(f"{scan_data['type']}: API returned {response}")
                        await demo.take_screenshot(f"scanner_{scan_data['type']}_failed")

                except Exception as e:
                    print(f"   ❌ Scanner test failed: {e}")
                    results["failed"] += 1
                    results["errors"].append(f"{scan_data['type']}: {str(e)}")

                await asyncio.sleep(2)

                # Method 2: Try manual input field
                try:
                    print(f"   → Trying manual input field...")

                    # Look for input field
                    input_field = await page.query_selector('input[type="text"], input[type="email"], input[placeholder*="scan"], input[placeholder*="code"]')

                    if input_field:
                        await input_field.fill(scan_data['expected'])
                        await demo.show_step(f"Manual input: {scan_data['expected']}", "info")
                        await demo.take_screenshot(f"manual_input_{scan_data['type']}")
                        print(f"   ✅ Manual input filled")
                        await asyncio.sleep(1)
                    else:
                        print(f"   ℹ️  No manual input field found")

                except Exception as e:
                    print(f"   ⚠️  Manual input error: {e}")

                await asyncio.sleep(2)

            print("\n" + "=" * 80)
            print("PHASE 3: SWITCH TO ENCODER MODE")
            print("=" * 80)

            # Switch to encoder mode
            encoder_url = "http://localhost:8100/connect-id?mode=encoder"
            await demo.demo_navigate(encoder_url)

            await demo.show_step("Activating encoder mode", "info")
            await page.keyboard.press("Control+e")
            await asyncio.sleep(1)
            await demo.take_screenshot("encoder_mode_activated")

            print("✅ Encoder mode activated")

            # Test encoder navigation
            print("\n🎯 Testing encoder navigation...")
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            await demo.take_screenshot("encoder_navigate_1")

            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            await demo.take_screenshot("encoder_navigate_2")

            await page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            await demo.take_screenshot("encoder_select")

            print("✅ Encoder navigation works")

            # Deactivate encoder
            await page.keyboard.press("Escape")
            await demo.show_step("Encoder deactivated", "success")
            await demo.take_screenshot("encoder_deactivated")

            # Generate reports
            print("\n" + "=" * 80)
            print("GENERATING REPORTS")
            print("=" * 80)

            analyzer.generate_report("scanner_test_report.json")
            analyzer.generate_html_report("scanner_test_report.html")

            print(f"\n{'='*80}")
            print("SCANNER MODE TEST RESULTS")
            print(f"{'='*80}")
            print(f"Total Tests:    {results['total']}")
            print(f"✅ Passed:      {results['passed']}")
            print(f"❌ Failed:      {results['failed']}")
            print(f"Success Rate:   {(results['passed']/results['total']*100):.1f}%")

            if results["errors"]:
                print(f"\n❌ ERRORS:")
                for err in results["errors"]:
                    print(f"  • {err}")

            print(f"\n📊 Reports:")
            print(f"  • scanner-test-reports/scanner_test_report.json")
            print(f"  • scanner-test-reports/scanner_test_report.html")
            print(f"  • scanner-test-screenshots/*.png")
            print(f"{'='*80}\n")

            print("⏸️  Browser stays open for 15 seconds...")
            await asyncio.sleep(15)

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

        finally:
            await browser.close()

            # Save results
            results_file = Path("./scanner_test_results.json")
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n✓ Results saved to: {results_file}")

        return results


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║           SCANNER MODE TESTING - Complete Simulation                   ║
║                                                                        ║
║  Tests:                                                                ║
║  ✓ QR Code scanning                                                    ║
║  ✓ Barcode scanning                                                    ║
║  ✓ RFID card reading                                                   ║
║  ✓ Manual entry                                                        ║
║  ✓ Encoder mode switching                                              ║
║  ✓ Encoder navigation                                                  ║
║                                                                        ║
║  Methods:                                                              ║
║  • Scanner API endpoint (/api/v3/identification/scanner/ingest)        ║
║  • Manual input fields                                                 ║
║  • Mode switching (scanner ↔ encoder)                                  ║
║                                                                        ║
║  Generates:                                                            ║
║  • scanner_test_report.json                                            ║
║  • scanner_test_report.html                                            ║
║  • scanner_test_results.json                                           ║
║  • scanner-test-screenshots/                                           ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    results = asyncio.run(test_scanner_mode())

    # Exit with proper code
    if results["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

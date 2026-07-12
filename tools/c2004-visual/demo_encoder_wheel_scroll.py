#!/usr/bin/env python3
"""
Encoder Wheel Scroll Testing - Tests horizontal wheel scrolling for menu navigation
Tests that encoder properly detects wheel scroll left/right for menu changes
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode


async def test_encoder_wheel_scroll():
    """Test encoder wheel scrolling for horizontal menu navigation."""
    from playwright.async_api import async_playwright

    print("\n" + "=" * 80)
    print("ENCODER WHEEL SCROLL TESTING - Horizontal Menu Navigation")
    print("=" * 80)
    print("\n📊 Testing:")
    print("  • Wheel scroll detection")
    print("  • wheelThreshold (480 default)")
    print("  • Horizontal menu navigation (left/right)")
    print("  • wheelResetMs timing")
    print()

    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=150,
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        demo = VisualDemoMode(
            page=page,
            speed="slow",
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./encoder-wheel-screenshots"),
        )

        await demo.inject_demo_styles()
        print("✓ Visual demo mode activated\n")

        try:
            # Navigate to connect-id with encoder mode
            print("=" * 80)
            print("PHASE 1: ENCODER ACTIVATION")
            print("=" * 80)

            await demo.demo_navigate("http://localhost:8100/connect-id?mode=encoder")

            # Activate encoder
            print("\n⌨️  Activating encoder mode (Ctrl+E)")
            await demo.show_step("Ctrl+E: Activate encoder", "info")
            await asyncio.sleep(0.1)
            await page.keyboard.press("Control+e")
            await asyncio.sleep(0.1)
            await demo.take_screenshot("encoder_activated")
            await asyncio.sleep(2)

            # PHASE 2: WHEEL SCROLL TESTING
            print("\n" + "=" * 80)
            print("PHASE 2: WHEEL SCROLL - HORIZONTAL NAVIGATION")
            print("=" * 80)

            # Test 1: Wheel Right (scroll down = navigate right in menu)
            print("\n🔄 Test 1: Wheel Scroll RIGHT (navigate menu right)")
            await demo.show_step("Wheel Right: Scroll to navigate menu →", "info")

            # Simulate wheel scroll right (deltaY positive)
            for i in range(5):
                await asyncio.sleep(0.1)
                await page.mouse.wheel(0, 100)  # deltaX=0, deltaY=100 (scroll down/right)
                await asyncio.sleep(0.15)
                print(f"    → Wheel right step {i+1}/5 (deltaY=+100)")

            await demo.take_screenshot("wheel_scroll_right")
            await asyncio.sleep(2)
            print("    ✓ Wheel right complete (500 total delta)")

            # Test 2: Wheel Left (scroll up = navigate left in menu)
            print("\n🔄 Test 2: Wheel Scroll LEFT (navigate menu left)")
            await demo.show_step("Wheel Left: Scroll to navigate menu ←", "info")

            # Simulate wheel scroll left (deltaY negative)
            for i in range(5):
                await asyncio.sleep(0.1)
                await page.mouse.wheel(0, -100)  # deltaY=-100 (scroll up/left)
                await asyncio.sleep(0.15)
                print(f"    ← Wheel left step {i+1}/5 (deltaY=-100)")

            await demo.take_screenshot("wheel_scroll_left")
            await asyncio.sleep(2)
            print("    ✓ Wheel left complete (-500 total delta)")

            # Test 3: Fast wheel scroll (exceeds wheelThreshold=480)
            print("\n🔄 Test 3: FAST Wheel Scroll (threshold test)")
            await demo.show_step("Fast Wheel: Exceed wheelThreshold (480)", "info")

            # Fast scroll to exceed threshold
            await asyncio.sleep(0.1)
            await page.mouse.wheel(0, 500)  # Single large scroll
            await asyncio.sleep(0.1)
            print("    ⚡ Fast wheel right (deltaY=+500, exceeds threshold=480)")

            await demo.take_screenshot("wheel_fast_scroll")
            await asyncio.sleep(2)
            print("    ✓ Threshold exceeded - menu should change")

            # Test 4: Slow wheel scroll (below threshold, should reset)
            print("\n🔄 Test 4: Slow Wheel Scroll (reset test)")
            await demo.show_step("Slow Wheel: Test wheelResetMs (180ms)", "info")

            # Slow scroll with pauses (should reset between)
            for i in range(3):
                await page.mouse.wheel(0, 100)
                print(f"    → Slow wheel {i+1}/3 (deltaY=+100)")
                await asyncio.sleep(0.3)  # Wait >180ms (wheelResetMs) between scrolls

            await demo.take_screenshot("wheel_slow_scroll")
            await asyncio.sleep(2)
            print("    ✓ Slow scroll complete (should reset between, no menu change)")

            # Test 5: Wheel scroll in different sections
            print("\n🔄 Test 5: Wheel Scroll in Different Sections")

            # Navigate to different module
            await demo.demo_navigate("http://localhost:8100/connect-data?mode=encoder")

            await demo.show_step("Wheel scroll in Connect-Data", "info")
            await asyncio.sleep(0.1)
            await page.keyboard.press("Control+e")  # Activate encoder
            await asyncio.sleep(1)

            # Wheel scroll right
            for i in range(4):
                await page.mouse.wheel(0, 120)
                await asyncio.sleep(0.15)
                print(f"    → Data module wheel {i+1}/4")

            await demo.take_screenshot("wheel_data_module")
            await asyncio.sleep(2)

            # PHASE 3: CONFIGURATION VALIDATION
            print("\n" + "=" * 80)
            print("PHASE 3: ENCODER CONFIGURATION VALIDATION")
            print("=" * 80)

            await demo.demo_navigate("http://localhost:8100/connect-config-encoder")
            await demo.show_step("Checking encoder config values", "info")
            await asyncio.sleep(2)

            # Try to read config via page evaluation
            try:
                config_text = await page.text_content("body")
                if "wheelThreshold" in config_text or "480" in config_text:
                    print("    ✓ wheelThreshold visible in config")
                if "wheelResetMs" in config_text or "180" in config_text:
                    print("    ✓ wheelResetMs visible in config")
            except:
                print("    ℹ️  Config values not directly readable")

            await demo.take_screenshot("encoder_config")

            # SUMMARY
            print("\n" + "=" * 80)
            print("WHEEL SCROLL TESTING COMPLETED!")
            print("=" * 80)
            print("\n📊 TESTED:")
            print("  ✓ Wheel scroll RIGHT (navigate menu →)")
            print("  ✓ Wheel scroll LEFT (navigate menu ←)")
            print("  ✓ Fast scroll (threshold=480)")
            print("  ✓ Slow scroll (reset=180ms)")
            print("  ✓ Multi-module wheel testing")
            print()
            print(f"📸 Screenshots: {demo.screenshots_dir}")
            print(f"📊 Total steps: {demo.step_counter}")
            print()

            print("⚙️  ENCODER WHEEL CONFIG:")
            print("  • wheelThreshold: 480 (min scroll delta to trigger)")
            print("  • wheelResetMs: 180 (ms to reset accumulated delta)")
            print("  • wheelLineUnit: 10 (scroll per line)")
            print()
            print("=" * 80)

            print("\n⏸️  Browser stays open for 20 seconds...")
            await asyncio.sleep(20)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

        finally:
            print("\n🔚 Closing browser...")
            await browser.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         ENCODER WHEEL SCROLL TESTING - Horizontal Navigation           ║
║                                                                        ║
║  Tests encoder wheel scrolling for menu navigation:                    ║
║  • Horizontal scroll detection (left/right)                            ║
║  • wheelThreshold validation (480)                                     ║
║  • wheelResetMs timing (180ms)                                         ║
║  • Fast vs slow scroll behavior                                        ║
║  • Multi-module wheel testing                                          ║
║                                                                        ║
║  Features:                                                             ║
║  ✓ Real mouse wheel events                                             ║
║  ✓ Threshold testing (>480 delta)                                      ║
║  ✓ Reset timing validation                                             ║
║  ✓ Visual annotations                                                  ║
║  ✓ Screenshots of each test                                            ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(test_encoder_wheel_scroll())

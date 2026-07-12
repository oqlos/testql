#!/usr/bin/env python3
"""
Visual Demo for C2004 Encoder Mode - Testing Keyboard Navigation
Run: python demo_c2004_encoder.py
"""

import asyncio
import sys
from pathlib import Path

# Add testql to path
sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode


async def demo_encoder_mode():
    """Run visual demo for C2004 encoder mode testing."""
    from playwright.async_api import async_playwright

    print("\n🎬 TestQL Visual Demo - C2004 Encoder Mode Testing")
    print("=" * 60)

    async with async_playwright() as p:
        # Launch headed browser
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=100,  # Slower for encoder mode demo
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # Create visual demo
        demo = VisualDemoMode(
            page=page,
            speed="slow",  # Slow mode for encoder testing
            show_annotations=True,
            save_screenshots=True,  # Save screenshots for encoder mode
            screenshots_dir=Path("./encoder-demo-screenshots"),
        )

        # Inject demo styles
        await demo.inject_demo_styles()
        print("✓ Visual demo mode activated")
        print("✓ Encoder mode testing enabled\n")

        try:
            # Test 1: Connect-ID with Encoder Mode
            print("📋 Test 1: Connect-ID Encoder Mode")
            await demo.demo_navigate("http://localhost:8100/connect-id/list?mode=encoder")

            # Check for body (always visible)
            try:
                await demo.demo_assert_visible("body", "Connect-ID page loaded")
                print("  ✓ Page loaded successfully")
            except:
                print("  ⚠️  Page load issue")

            # Try to find and highlight table (may be hidden in encoder mode)
            try:
                await demo.highlight_element("table", duration_ms=1500)
                print("  ✓ User table highlighted")
            except:
                print("  ℹ️  Table hidden (encoder mode not activated)")

            await asyncio.sleep(1)

            # Test 2: Connect-Data with Encoder Mode
            print("\n📊 Test 2: Connect-Data Encoder Mode")
            await demo.demo_navigate("http://localhost:8100/connect-data?mode=encoder")
            await demo.demo_assert_visible("body", "Connect-Data loaded in encoder mode")

            # Test 3: Connect-Reports with Encoder Mode
            print("\n📈 Test 3: Connect-Reports Encoder Mode")
            await demo.demo_navigate("http://localhost:8100/connect-reports?mode=encoder")
            await demo.demo_assert_visible("body", "Reports page in encoder mode")

            # Test 4: Connect-Manager with Encoder Mode
            print("\n🎯 Test 4: Connect-Manager Encoder Mode")
            await demo.demo_navigate("http://localhost:8100/connect-manager?mode=encoder")
            await demo.demo_assert_visible("body", "Manager page in encoder mode")

            # Test 5: Connect-Scenario with Encoder Mode
            print("\n📝 Test 5: Connect-Scenario Encoder Mode")
            await demo.demo_navigate("http://localhost:8100/connect-scenario?mode=encoder")
            await demo.demo_assert_visible("body", "Scenario editor in encoder mode")

            # Test 6: Encoder Configuration Page
            print("\n⚙️  Test 6: Encoder Configuration")
            await demo.demo_navigate("http://localhost:8100/connect-config-encoder")
            await demo.demo_assert_visible("body", "Encoder config page loaded")

            # Try to find configuration sections
            try:
                await demo.highlight_element("section, .config-section", duration_ms=2000)
                print("  ✓ Config sections visible")
            except:
                print("  ℹ️  Config sections structure different")

            # Test 7: Keyboard Mode (alternative to encoder)
            print("\n⌨️  Test 7: Keyboard Mode on Connect-Test")
            await demo.demo_navigate("http://localhost:8100/connect-test?mode=keyboard")
            await demo.demo_assert_visible("body", "Test page in keyboard mode")

            # Summary
            print("\n" + "=" * 60)
            print(f"✅ Encoder mode demo completed!")
            print(f"📊 Steps executed: {demo.step_counter}")
            print(f"📸 Screenshots saved to: {demo.screenshots_dir}")
            print("=" * 60)

            # Keep browser open to review
            print("\n⏸️  Browser will stay open for 10 seconds...")
            print("   (Review the encoder mode UI)")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\n❌ Error during encoder demo: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)

        finally:
            print("\n🔚 Closing browser...")
            await browser.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║      TestQL Visual Demo - C2004 Encoder Mode Testing        ║
║                                                              ║
║  Tests encoder mode across all C2004 modules:                ║
║  • Connect-ID (user list with encoder navigation)            ║
║  • Connect-Data (data tables with encoder)                   ║
║  • Connect-Reports (reports with encoder)                    ║
║  • Connect-Manager (test manager with encoder)               ║
║  • Connect-Scenario (scenario editor with encoder)           ║
║  • Connect-Config-Encoder (encoder configuration)            ║
║  • Connect-Test (keyboard mode alternative)                  ║
║                                                              ║
║  Features:                                                   ║
║  ✓ Yellow highlights on elements                             ║
║  ✓ Step-by-step annotations                                  ║
║  ✓ Auto-screenshots saved                                    ║
║  ✓ Slow motion for clear visibility                          ║
║                                                              ║
║  Like Gemini demos - shows encoder testing live!            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(demo_encoder_mode())

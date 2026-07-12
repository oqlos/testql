#!/usr/bin/env python3
"""
Manual Encoder Testing for C2004 - Using keyboard navigation through menu
Simulates real encoder usage: Ctrl+E to activate, arrows to navigate, Enter to select
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode


async def demo_encoder_manual_navigation():
    """Test encoder mode with manual keyboard navigation through menu."""
    from playwright.async_api import async_playwright

    print("\n⌨️  TestQL Visual Demo - C2004 MANUAL Encoder Testing")
    print("=" * 70)

    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=150,  # Very slow for manual observation
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        demo = VisualDemoMode(
            page=page,
            speed="slow",  # 2s delays
            show_annotations=True,
            save_screenshots=True,
            screenshots_dir=Path("./encoder-manual-screenshots"),
        )

        await demo.inject_demo_styles()
        print("✓ Visual demo mode activated\n")

        try:
            # Start at home page
            print("📍 Step 1: Navigate to C2004 home")
            await demo.demo_navigate("http://localhost:8100")
            await asyncio.sleep(1)

            # Activate encoder mode with Ctrl+E
            print("\n⌨️  Step 2: Activate Encoder Mode (Ctrl+E)")
            await demo.show_step("Pressing Ctrl+E to activate encoder", "info")
            await page.keyboard.press("Control+e")
            await asyncio.sleep(2)
            await demo.take_screenshot("encoder_activated")
            print("  ✓ Encoder activated")

            # Navigate to menu
            print("\n📋 Step 3: Navigate to Menu with Tab")
            await demo.show_step("Navigating with Tab key", "info")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1)
            await demo.take_screenshot("tab_to_menu")

            # Use arrows to navigate menu items
            print("\n⬇️  Step 4: Navigate menu items with Arrow Down")
            for i in range(3):
                await demo.show_step(f"Arrow Down - menu item {i+1}", "info")
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(1.5)
                await demo.take_screenshot(f"menu_item_{i+1}")
                print(f"  ↓ Menu item {i+1}")

            # Select with Enter
            print("\n✓ Step 5: Select menu item with Enter")
            await demo.show_step("Pressing Enter to select", "success")
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
            await demo.take_screenshot("menu_selected")
            print("  ✓ Item selected")

            # Navigate in the opened page
            print("\n⬇️  Step 6: Navigate within page (Arrow Down)")
            for i in range(4):
                await demo.show_step(f"Arrow Down - focus item {i+1}", "info")
                await page.keyboard.press("ArrowDown")
                await asyncio.sleep(1.5)
                await demo.take_screenshot(f"page_focus_{i+1}")
                print(f"  ↓ Focus item {i+1}")

            # Arrow Up navigation
            print("\n⬆️  Step 7: Navigate back up (Arrow Up)")
            for i in range(2):
                await demo.show_step(f"Arrow Up - focus back", "info")
                await page.keyboard.press("ArrowUp")
                await asyncio.sleep(1.5)
                await demo.take_screenshot(f"page_focus_up_{i+1}")
                print(f"  ↑ Focus up {i+1}")

            # Accept/confirm with Enter
            print("\n✓ Step 8: Accept current item (Enter)")
            await demo.show_step("Pressing Enter to confirm selection", "success")
            await page.keyboard.press("Enter")
            await asyncio.sleep(2)
            await demo.take_screenshot("item_confirmed")
            print("  ✓ Item confirmed")

            # Escape to cancel/go back
            print("\n⬅️  Step 9: Cancel/Back with Escape")
            await demo.show_step("Pressing Escape to cancel", "info")
            await page.keyboard.press("Escape")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("escape_cancel")
            print("  ✓ Cancelled")

            # Navigate to next section with Tab
            print("\n➡️  Step 10: Next section with Tab")
            await demo.show_step("Tab to next section", "info")
            await page.keyboard.press("Tab")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("next_section")
            print("  ✓ Next section")

            # Shift+Tab to go back
            print("\n⬅️  Step 11: Previous section with Shift+Tab")
            await demo.show_step("Shift+Tab to previous section", "info")
            await page.keyboard.press("Shift+Tab")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("prev_section")
            print("  ✓ Previous section")

            # Page navigation
            print("\n📄 Step 12: Page Down")
            await demo.show_step("PageDown for next page", "info")
            await page.keyboard.press("PageDown")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("page_down")
            print("  ✓ Page down")

            print("\n📄 Step 13: Page Up")
            await demo.show_step("PageUp for previous page", "info")
            await page.keyboard.press("PageUp")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("page_up")
            print("  ✓ Page up")

            # Deactivate encoder
            print("\n⌨️  Step 14: Deactivate Encoder (Escape)")
            await demo.show_step("Pressing Escape to deactivate encoder", "info")
            await page.keyboard.press("Escape")
            await asyncio.sleep(1.5)
            await demo.take_screenshot("encoder_deactivated")
            print("  ✓ Encoder deactivated")

            # Summary
            print("\n" + "=" * 70)
            print(f"✅ Manual encoder testing completed!")
            print(f"📊 Total steps: {demo.step_counter}")
            print(f"📸 Screenshots: {demo.screenshots_dir}")
            print("=" * 70)

            print("\n⏸️  Browser stays open for 15 seconds for review...")
            await asyncio.sleep(15)

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
╔════════════════════════════════════════════════════════════════════╗
║    TestQL Visual Demo - C2004 MANUAL Encoder Navigation Testing   ║
║                                                                    ║
║  Real encoder usage simulation:                                    ║
║  • Ctrl+E - Activate encoder mode                                  ║
║  • Arrow Down/Up - Navigate items                                  ║
║  • Tab/Shift+Tab - Switch sections                                 ║
║  • Enter - Select/Confirm                                          ║
║  • Escape - Cancel/Deactivate                                      ║
║  • PageDown/PageUp - Page navigation                               ║
║                                                                    ║
║  Features:                                                         ║
║  ✓ Yellow highlights on focused elements                           ║
║  ✓ Annotations showing each key press                              ║
║  ✓ Step-by-step screenshots                                        ║
║  ✓ Slow motion (2s per step) for observation                       ║
║                                                                    ║
║  Tests REAL encoder keyboard navigation!                           ║
╚════════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(demo_encoder_manual_navigation())

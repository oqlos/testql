#!/usr/bin/env python3
"""
Simple Visual Test - Shows browser window with highlights
NO imports from testql - pure Playwright
"""

import asyncio
from playwright.async_api import async_playwright


async def show_visual_test():
    """Show browser with visual feedback."""

    print("\n" + "=" * 80)
    print("🎬 OPENING BROWSER WINDOW - YOU WILL SEE IT!")
    print("=" * 80)
    print()

    async with async_playwright() as p:
        print("🚀 Launching Chrome...")

        # Launch browser - VISIBLE!
        browser = await p.chromium.launch(
            headless=False,  # VISIBLE WINDOW!
            slow_mo=800,     # Slow for visibility
            args=[
                '--start-maximized',
                '--window-size=1920,1080'
            ]
        )

        # Create page
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("✅ Browser window opened!")
        print("📺 LOOK AT YOUR SCREEN - You should see Chrome window!\n")

        # Add visual styles
        await page.add_style_tag(content="""
            .highlight {
                outline: 5px solid #FFD700 !important;
                outline-offset: 5px !important;
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.8) !important;
                background-color: rgba(255, 215, 0, 0.1) !important;
            }

            .message {
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
                padding: 30px !important;
                border-radius: 15px !important;
                font-size: 24px !important;
                font-weight: bold !important;
                z-index: 999999 !important;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3) !important;
                animation: slideIn 0.5s ease !important;
            }

            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
        """)

        # Test 1: Connect-ID
        print("🔵 [1/3] Loading Connect-ID...")
        await page.goto("http://localhost:8100/connect-id", wait_until="domcontentloaded")

        # Add message
        await page.evaluate("""
            () => {
                const msg = document.createElement('div');
                msg.className = 'message';
                msg.innerHTML = '🎬 TestQL Visual Demo<br>Step 1: Connect-ID';
                document.body.appendChild(msg);
            }
        """)

        print("   ✅ Page loaded - SEE THE PURPLE BOX IN TOP RIGHT?")
        await asyncio.sleep(3)

        # Highlight buttons
        print("   💛 Highlighting buttons...")
        await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('button');
                buttons.forEach((btn, i) => {
                    if (i < 5) {
                        btn.classList.add('highlight');
                    }
                });
            }
        """)
        await asyncio.sleep(3)

        # Test 2: Encoder Mode
        print("\n🔵 [2/3] Loading Encoder Mode...")
        await page.goto("http://localhost:8100/connect-id?mode=encoder", wait_until="domcontentloaded")

        await page.evaluate("""
            () => {
                document.querySelectorAll('.message').forEach(el => el.remove());
                const msg = document.createElement('div');
                msg.className = 'message';
                msg.innerHTML = '⌨️ Encoder Mode<br>Step 2';
                document.body.appendChild(msg);
            }
        """)

        print("   ✅ Encoder mode loaded")
        await asyncio.sleep(2)

        # Simulate encoder
        print("   ⌨️  Pressing Ctrl+E...")
        await page.keyboard.press("Control+e")
        await asyncio.sleep(2)

        print("   ⬇️  Arrow Down...")
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(1)

        print("   ⬇️  Arrow Down...")
        await page.keyboard.press("ArrowDown")
        await asyncio.sleep(1)

        print("   ✅ Enter...")
        await page.keyboard.press("Enter")
        await asyncio.sleep(2)

        # Test 3: Connect-Data
        print("\n🔵 [3/3] Loading Connect-Data...")
        await page.goto("http://localhost:8100/connect-data", wait_until="domcontentloaded")

        await page.evaluate("""
            () => {
                document.querySelectorAll('.message').forEach(el => el.remove());
                const msg = document.createElement('div');
                msg.className = 'message';
                msg.innerHTML = '📊 Connect-Data<br>Step 3: Final Test';
                document.body.appendChild(msg);
            }
        """)

        print("   ✅ Data page loaded")
        await asyncio.sleep(2)

        # Highlight tables
        print("   💛 Highlighting tables...")
        await page.evaluate("""
            () => {
                const tables = document.querySelectorAll('table');
                tables.forEach(table => {
                    table.classList.add('highlight');
                });
            }
        """)
        await asyncio.sleep(3)

        # Final message
        await page.evaluate("""
            () => {
                document.querySelectorAll('.message').forEach(el => el.remove());
                const msg = document.createElement('div');
                msg.className = 'message';
                msg.innerHTML = '✅ All Tests Complete!<br>🎉 Success!';
                msg.style.background = 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
                document.body.appendChild(msg);
            }
        """)

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETE!")
        print("=" * 80)
        print("\n📺 Browser window will stay open for 15 seconds...")
        print("   Look at your screen - do you see:")
        print("   ✅ Chrome window (full screen)")
        print("   ✅ Purple/Green box in top right corner")
        print("   ✅ Yellow highlights on elements")
        print()

        await asyncio.sleep(15)

        print("🔚 Closing browser...")
        await browser.close()
        print("✅ Done!\n")


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║              VISUAL TEST - BROWSER WINDOW WILL OPEN!                   ║
║                                                                        ║
║  This script will:                                                     ║
║  ✅ Open Chrome window (VISIBLE!)                                      ║
║  ✅ Show purple message box (top right)                                ║
║  ✅ Add yellow highlights to elements                                  ║
║  ✅ Test 3 pages (Connect-ID, Encoder, Connect-Data)                   ║
║  ✅ Stay open for 15 seconds                                           ║
║                                                                        ║
║  📺 WATCH YOUR SCREEN!                                                 ║
╚════════════════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(show_visual_test())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
Standalone Visual Demo for C2004 - No CLI dependencies
Run: python demo_c2004.py
"""

import asyncio
import sys
from pathlib import Path

# Add testql to path
sys.path.insert(0, str(Path(__file__).parent))

from testql.visual_demo import VisualDemoMode


async def demo_c2004():
    """Run visual demo for C2004 pages."""
    from playwright.async_api import async_playwright

    print("\n🎬 TestQL Visual Demo - C2004 Pages")
    print("=" * 50)

    async with async_playwright() as p:
        # Launch headed browser
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=50,
        )

        page = await browser.new_page(viewport={"width": 1280, "height": 800})

        # Create visual demo
        demo = VisualDemoMode(
            page=page,
            speed="medium",  # slow, medium, fast
            show_annotations=True,
            save_screenshots=False,  # Set to True to save screenshots
        )

        # Inject demo styles
        await demo.inject_demo_styles()
        print("✓ Visual demo mode activated\n")

        # Demo pages
        pages = [
            ("http://localhost:8100/connect-id/list", "Connect-ID: User List"),
            ("http://localhost:8100/connect-data", "Connect-Data: Data Management"),
            ("http://localhost:8100/connect-reports", "Connect-Reports: Weekly Reports"),
            ("http://localhost:8100/connect-manager", "Connect-Manager: Test Management"),
            ("http://localhost:8100/connect-config", "Connect-Config: Configuration"),
            ("http://localhost:8100/connect-scenario", "Connect-Scenario: Scenario Editor"),
            ("http://localhost:8100/connect-template", "Connect-Template: Templates"),
            ("http://localhost:8100/connect-test", "Connect-Test: Testing"),
            ("http://localhost:8100/connect-id/list?mode=encoder", "Connect-ID: Encoder Mode"),
            ("http://localhost:8100/connect-config-encoder", "Encoder Configuration"),
        ]

        try:
            for url, description in pages:
                print(f"▸ {description}")
                await demo.demo_navigate(url)
                await demo.demo_assert_visible("body", f"Page loaded: {description}")
                print(f"  ✓ Loaded\n")

            print("=" * 50)
            print(f"✅ Visual demo completed! ({demo.step_counter} steps)")

            # Keep browser open for a moment
            print("\nClosing in 3 seconds...")
            await asyncio.sleep(3)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║           TestQL Visual Demo Mode for C2004                  ║
║                                                              ║
║  Features:                                                   ║
║  • Headed browser (visible window)                           ║
║  • Yellow highlights on elements                             ║
║  • Step-by-step annotations                                  ║
║  • Success/Error indicators                                  ║
║  • Smooth animations                                         ║
║                                                              ║
║  Like Gemini/LLM demos - shows tests running live!          ║
╚══════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(demo_c2004())

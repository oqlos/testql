#!/usr/bin/env python3
"""
Visual Test Runner - Shows browser window with all actions
"""

import asyncio
import sys
from pathlib import Path

# Fix imports
sys.path.insert(0, str(Path(__file__).parent))

# Import from local files (not package)
import importlib.util

# Load visual_demo from testql/ directory if it exists, otherwise current
visual_demo_path = Path(__file__).parent / "testql" / "visual_demo.py"
if not visual_demo_path.exists():
    # Try to find it in current directory via imports
    try:
        from demo_c2004 import *
        print("Using demo imports from demo_c2004.py")
    except:
        print("❌ Cannot find visual_demo.py")
        sys.exit(1)

from playwright.async_api import async_playwright
import time


async def visual_test_demo():
    """Run visual test with visible browser."""
    
    print("\n" + "=" * 80)
    print("🎬 VISUAL TEST - Browser Window Will Open")
    print("=" * 80)
    print()
    print("✨ Features:")
    print("  • Visible browser window")
    print("  • Real-time navigation")
    print("  • Visual highlights")
    print("  • Step-by-step execution")
    print()
    
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        
        # Launch with visible window
        browser = await p.chromium.launch(
            headless=False,  # VISIBLE!
            slow_mo=500,     # 500ms between actions (visible)
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # Create context and page
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            no_viewport=True  # Use full window
        )
        
        page = await context.new_page()
        
        # Add visual styles
        await page.add_style_tag(content="""
            .testql-highlight {
                outline: 4px solid #FFD700 !important;
                outline-offset: 3px;
                box-shadow: 0 0 15px rgba(255, 215, 0, 0.8) !important;
                transition: all 0.3s ease;
            }
            
            .testql-step {
                position: fixed;
                top: 20px;
                right: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px 30px;
                border-radius: 12px;
                font-size: 18px;
                font-weight: bold;
                z-index: 999999;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                animation: slideIn 0.5s ease;
            }
            
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            
            .testql-counter {
                position: fixed;
                top: 90px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                z-index: 999999;
            }
        """)
        
        step = 0
        
        async def show_step(message, wait=2):
            nonlocal step
            step += 1
            
            # Show step message
            await page.evaluate(f"""
                () => {{
                    // Remove old elements
                    document.querySelectorAll('.testql-step, .testql-counter').forEach(el => el.remove());
                    
                    // Add counter
                    const counter = document.createElement('div');
                    counter.className = 'testql-counter';
                    counter.textContent = 'Step {step}';
                    document.body.appendChild(counter);
                    
                    // Add step message
                    const step = document.createElement('div');
                    step.className = 'testql-step';
                    step.innerHTML = '{message}';
                    document.body.appendChild(step);
                }}
            """)
            
            print(f"  [{step}] {message}")
            await asyncio.sleep(wait)
        
        try:
            # Test 1: Connect-ID
            print("\n📦 Test 1/3: Connect-ID")
            await show_step("Loading Connect-ID...", 1)
            await page.goto("http://localhost:8100/connect-id", wait_until="domcontentloaded")
            await show_step("✅ Connect-ID Loaded", 2)
            
            # Highlight elements
            await page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button');
                    buttons.forEach((btn, i) => {
                        if (i < 3) {
                            btn.classList.add('testql-highlight');
                        }
                    });
                }
            """)
            await show_step("🔍 Found buttons", 2)
            
            # Test 2: Encoder Mode
            print("\n📦 Test 2/3: Encoder Mode")
            await show_step("Switching to Encoder Mode...", 1)
            await page.goto("http://localhost:8100/connect-id?mode=encoder", wait_until="domcontentloaded")
            await show_step("⌨️ Encoder Mode Active", 2)
            
            # Activate encoder
            await show_step("Pressing Ctrl+E...", 1)
            await page.keyboard.press("Control+e")
            await asyncio.sleep(1)
            
            # Navigate with encoder
            await show_step("Arrow Down ↓", 1)
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            
            await show_step("Arrow Down ↓", 1)
            await page.keyboard.press("ArrowDown")
            await asyncio.sleep(0.5)
            
            await show_step("Enter - Select", 1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(1)
            
            await show_step("Escape - Exit", 1)
            await page.keyboard.press("Escape")
            await asyncio.sleep(1)
            
            # Test 3: Connect-Data
            print("\n📦 Test 3/3: Connect-Data")
            await show_step("Loading Connect-Data...", 1)
            await page.goto("http://localhost:8100/connect-data", wait_until="domcontentloaded")
            await show_step("✅ Connect-Data Loaded", 2)
            
            # Highlight table
            await page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    tables.forEach(table => {
                        table.classList.add('testql-highlight');
                    });
                }
            """)
            await show_step("🔍 Found tables", 2)
            
            # Final message
            await show_step("✅ All Tests Complete!", 3)
            
            print("\n" + "=" * 80)
            print("✅ VISUAL TEST COMPLETED")
            print("=" * 80)
            print("\n⏸️  Browser will stay open for 10 seconds...")
            print("   Watch the browser window to see all actions!")
            await asyncio.sleep(10)
            
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
║                    VISUAL TEST - LIVE DEMO                             ║
║                                                                        ║
║  Browser window will open and show:                                    ║
║  ✓ Real-time navigation                                                ║
║  ✓ Visual highlights on elements                                       ║
║  ✓ Step counter and messages                                           ║
║  ✓ Encoder mode testing                                                ║
║                                                                        ║
║  Watch the browser window to see everything happening!                 ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(visual_test_demo())

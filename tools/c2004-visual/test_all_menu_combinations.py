#!/usr/bin/env python3
"""
Complete Menu Testing - ALL combinations (col-1, col-2, submenu)
Tests every possible menu navigation path in C2004
"""

import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime


# Complete menu structure with ALL combinations
MENU_STRUCTURE = {
    "connect-id": {
        "name": "Connect-ID",
        "col-1": ["account", "list", "search"],
        "col-2": ["admin", "guest", "operator"]
    },
    "connect-data": {
        "name": "Connect-Data",
        "col-1": ["view", "edit", "export", "import"],
        "col-2": ["table", "grid", "list"]
    },
    "connect-reports": {
        "name": "Connect-Reports",
        "col-1": ["daily", "weekly", "monthly", "yearly"],
        "col-2": ["summary", "detailed"]
    },
    "connect-manager": {
        "name": "Connect-Manager",
        "col-1": ["tests", "scenarios", "protocols"],
        "col-2": ["active", "archived"]
    },
    "connect-config": {
        "name": "Connect-Config",
        "col-1": ["general", "encoder", "scanner", "display"],
        "col-2": ["basic", "advanced"]
    },
    "connect-scenario": {
        "name": "Connect-Scenario",
        "col-1": ["create", "edit", "delete", "copy"],
        "col-2": ["manual", "automatic"]
    },
    "connect-template": {
        "name": "Connect-Template",
        "col-1": ["new", "existing", "import"],
        "col-2": ["simple", "complex"]
    },
    "connect-test": {
        "name": "Connect-Test",
        "col-1": ["run", "debug", "report"],
        "col-2": ["single", "batch"]
    },
    "connect-protocol": {
        "name": "Connect-Protocol",
        "col-1": ["view", "edit", "export"],
        "col-2": ["standard", "custom"]
    }
}


async def test_all_menu_combinations(headless=False, max_concurrent=5):
    """Test ALL menu combinations."""
    
    print("\n" + "=" * 80)
    print("🎯 COMPLETE MENU TESTING - ALL COMBINATIONS")
    print("=" * 80)
    
    # Calculate total combinations
    total_combinations = 0
    for module, data in MENU_STRUCTURE.items():
        total_combinations += len(data["col-1"]) * len(data["col-2"])
    
    print(f"\n📊 Test Plan:")
    print(f"   • Modules: {len(MENU_STRUCTURE)}")
    print(f"   • Total combinations: {total_combinations}")
    print(f"   • Test method: Encoder mode navigation")
    print(f"   • Concurrent: {max_concurrent}")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=50)
        
        # Create contexts for parallel testing
        contexts = []
        for i in range(min(max_concurrent, len(MENU_STRUCTURE))):
            ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            contexts.append(ctx)
        
        all_results = []
        start_time = asyncio.get_event_loop().time()
        
        # Test each module
        for idx, (module, menu_data) in enumerate(MENU_STRUCTURE.items()):
            print(f"\n{'='*80}")
            print(f"MODULE {idx+1}/{len(MENU_STRUCTURE)}: {menu_data['name']}")
            print(f"{'='*80}")
            
            ctx = contexts[idx % len(contexts)]
            page = await ctx.new_page()
            
            # Add visual feedback
            await page.add_style_tag(content="""
                .testql-info {
                    position: fixed !important;
                    top: 10px !important;
                    right: 10px !important;
                    background: rgba(102, 126, 234, 0.95) !important;
                    color: white !important;
                    padding: 15px !important;
                    border-radius: 8px !important;
                    font-size: 14px !important;
                    z-index: 999999 !important;
                    font-family: monospace !important;
                }
            """)
            
            # Generate all combinations for this module
            combinations = []
            for col1_option in menu_data["col-1"]:
                for col2_option in menu_data["col-2"]:
                    combinations.append((col1_option, col2_option))
            
            print(f"\n🔍 Testing {len(combinations)} combinations:")
            
            # Test each combination
            for combo_idx, (col1, col2) in enumerate(combinations, 1):
                url = f"http://localhost:8100/{module}?mode=encoder&col-1={col1}&col-2={col2}"
                
                print(f"   [{combo_idx}/{len(combinations)}] {col1} + {col2}...", end=" ")
                
                try:
                    # Navigate
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    
                    # Show info on page
                    await page.evaluate(f"""
                        () => {{
                            const existing = document.querySelector('.testql-info');
                            if (existing) existing.remove();

                            const info = document.createElement('div');
                            info.className = 'testql-info';
                            info.innerHTML = `
                                <div><strong>{menu_data['name']}</strong></div>
                                <div>Col-1: {col1}</div>
                                <div>Col-2: {col2}</div>
                                <div>Test {combo_idx}/{len(combinations)}</div>
                            `;
                            document.body.appendChild(info);
                        }}
                    """)

                    # Wait for page to stabilize - INCREASED TO 200ms
                    await asyncio.sleep(0.2)

                    # Test encoder activation
                    await page.keyboard.press("Control+e")
                    # Wait for encoder to activate - INCREASED TO 200ms
                    await asyncio.sleep(0.2)

                    # Verify encoder is active
                    encoder_active = await page.evaluate("""
                        () => {
                            // Check multiple possible encoder indicators
                            return document.body.classList.contains('encoder-active') ||
                                   document.body.classList.contains('encoder-mode') ||
                                   document.querySelector('[data-encoder="true"]') !== null ||
                                   document.querySelector('.encoder-overlay') !== null;
                        }
                    """)

                    # Navigate with arrows - INCREASED TO 200ms each
                    await page.keyboard.press("ArrowDown")
                    await asyncio.sleep(0.2)
                    await page.keyboard.press("ArrowUp")
                    await asyncio.sleep(0.2)

                    # Deactivate
                    await page.keyboard.press("Escape")
                    # Wait for deactivation - INCREASED TO 200ms
                    await asyncio.sleep(0.2)
                    
                    # Get page info
                    title = await page.title()
                    dom_count = await page.evaluate("() => document.querySelectorAll('*').length")
                    
                    result = {
                        "module": module,
                        "col-1": col1,
                        "col-2": col2,
                        "url": url,
                        "status": response.status if response else 0,
                        "title": title,
                        "dom_elements": dom_count,
                        "encoder_active": encoder_active,
                        "success": response.status == 200 if response else False
                    }
                    
                    all_results.append(result)
                    
                    if result["success"]:
                        encoder_indicator = "🎯" if encoder_active else "⚠️"
                        print(f"✅ {response.status} ({dom_count} elements) {encoder_indicator}")
                    else:
                        print(f"❌ {response.status}")
                    
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    all_results.append({
                        "module": module,
                        "col-1": col1,
                        "col-2": col2,
                        "url": url,
                        "status": "error",
                        "error": str(e),
                        "success": False
                    })
            
            await page.close()
        
        # Close contexts
        for ctx in contexts:
            await ctx.close()
        
        await browser.close()
        
        total_time = asyncio.get_event_loop().time() - start_time
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 COMPLETE MENU TESTING - RESULTS")
        print("=" * 80)
        
        passed = sum(1 for r in all_results if r.get("success"))
        failed = len(all_results) - passed
        
        print(f"\n✅ Passed:        {passed}/{len(all_results)}")
        print(f"❌ Failed:        {failed}/{len(all_results)}")
        print(f"⏱️  Total time:    {total_time:.2f}s")
        print(f"⚡ Avg per test:  {(total_time/len(all_results)):.2f}s")
        print(f"📊 Coverage:      {(passed/len(all_results)*100):.1f}%")
        
        # Show failed combinations
        if failed > 0:
            print(f"\n❌ FAILED COMBINATIONS:")
            for r in all_results:
                if not r.get("success"):
                    print(f"   • {r['module']}: {r['col-1']} + {r['col-2']} ({r.get('status', 'error')})")
        
        # Group by module
        print(f"\n📋 BY MODULE:")
        for module in MENU_STRUCTURE.keys():
            module_results = [r for r in all_results if r["module"] == module]
            module_passed = sum(1 for r in module_results if r.get("success"))
            print(f"   • {module:<20} {module_passed}/{len(module_results)} ✅")
        
        # Save detailed results
        report = {
            "summary": {
                "total_combinations": len(all_results),
                "passed": passed,
                "failed": failed,
                "total_time": round(total_time, 2),
                "timestamp": datetime.now().isoformat()
            },
            "results": all_results
        }
        
        with open("complete_menu_test_results.json", 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report: complete_menu_test_results.json")
        print("=" * 80 + "\n")
        
        return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ALL menu combinations")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    parser.add_argument("--concurrent", type=int, default=5, help="Max concurrent (default: 5)")
    parser.add_argument("--visible", action="store_true", help="Run with visible browser")
    
    args = parser.parse_args()
    
    print("""
╔════════════════════════════════════════════════════════════════════════╗
║         COMPLETE MENU TESTING - ALL COMBINATIONS                       ║
║                                                                        ║
║  Tests EVERY possible menu combination:                                ║
║  • All modules (9)                                                     ║
║  • All col-1 options (3-4 per module)                                  ║
║  • All col-2 options (2-3 per module)                                  ║
║  • Total: ~100+ combinations                                           ║
║                                                                        ║
║  Method:                                                               ║
║  • Encoder mode navigation                                             ║
║  • Keyboard shortcuts (Ctrl+E, Arrow keys)                             ║
║  • URL parameters (?col-1=X&col-2=Y)                                   ║
║                                                                        ║
║  Generates: complete_menu_test_results.json                            ║
╚════════════════════════════════════════════════════════════════════════╝
    """)
    
    asyncio.run(test_all_menu_combinations(
        headless=args.headless and not args.visible,
        max_concurrent=args.concurrent
    ))

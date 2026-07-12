#!/usr/bin/env python3
"""
Parallel Testing - Test multiple pages simultaneously
Much faster than sequential testing!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright


async def test_single_page(page, url, module_name, step_num):
    """Test a single page independently."""
    result = {
        "module": module_name,
        "url": url,
        "step": step_num,
        "status": "unknown",
        "start_time": datetime.now().isoformat(),
        "errors": [],
        "warnings": [],
        "metrics": {}
    }

    try:
        # Navigate
        print(f"  [{step_num}] Loading {module_name}...")
        start = asyncio.get_event_loop().time()

        response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)

        load_time = (asyncio.get_event_loop().time() - start) * 1000

        result["status"] = response.status if response else 0
        result["metrics"]["load_time"] = round(load_time)

        # Wait for page to stabilize
        await page.wait_for_load_state("networkidle", timeout=5000)

        # Get page info
        title = await page.title()
        result["title"] = title

        # DOM analysis
        dom_stats = await page.evaluate("""
            () => ({
                elements: document.querySelectorAll('*').length,
                buttons: document.querySelectorAll('button').length,
                inputs: document.querySelectorAll('input').length,
                tables: document.querySelectorAll('table').length,
            })
        """)

        result["dom"] = dom_stats

        # Check for errors
        if result["status"] != 200:
            result["errors"].append(f"HTTP {result['status']}")

        if dom_stats["elements"] < 10:
            result["warnings"].append("Very few elements")

        result["end_time"] = datetime.now().isoformat()

        print(f"  [{step_num}] ✅ {module_name}: {result['status']} ({load_time:.0f}ms, {dom_stats['elements']} elements)")

        return result

    except Exception as e:
        result["errors"].append(str(e))
        result["status"] = "error"
        print(f"  [{step_num}] ❌ {module_name}: {e}")
        return result


async def parallel_test(modules, headless=False, max_concurrent=5):
    """Test multiple modules in parallel."""

    print("\n" + "=" * 80)
    print("🚀 PARALLEL TESTING - Multiple Pages Simultaneously")
    print("=" * 80)
    print(f"\n📊 Configuration:")
    print(f"   • Total modules: {len(modules)}")
    print(f"   • Max concurrent: {max_concurrent}")
    print(f"   • Headless: {headless}")
    print()

    async with async_playwright() as p:
        print("🚀 Launching browser...")
        browser = await p.chromium.launch(headless=headless)

        # Create multiple contexts (isolated browser tabs)
        contexts = []
        for i in range(min(max_concurrent, len(modules))):
            ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
            contexts.append(ctx)

        print(f"✅ Created {len(contexts)} browser contexts\n")

        start_time = asyncio.get_event_loop().time()

        # Test modules in batches
        all_results = []

        for batch_start in range(0, len(modules), max_concurrent):
            batch = modules[batch_start:batch_start + max_concurrent]

            print(f"🔄 Testing batch {batch_start//max_concurrent + 1} ({len(batch)} modules)...")

            # Create tasks for parallel execution
            tasks = []
            for i, (module, desc) in enumerate(batch):
                ctx_idx = i % len(contexts)
                page = await contexts[ctx_idx].new_page()

                url = f"http://localhost:8100/{module}?mode=encoder"
                task = test_single_page(page, url, module, batch_start + i + 1)
                tasks.append(task)

            # Run all tasks in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Close pages
            for ctx in contexts:
                for page in ctx.pages:
                    await page.close()

            all_results.extend([r for r in batch_results if not isinstance(r, Exception)])

            print()

        total_time = asyncio.get_event_loop().time() - start_time

        # Close contexts
        for ctx in contexts:
            await ctx.close()

        await browser.close()

        # Generate summary
        print("=" * 80)
        print("📊 RESULTS SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in all_results if r["status"] == 200 and not r["errors"])
        failed = sum(1 for r in all_results if r["errors"])
        warnings = sum(1 for r in all_results if r["warnings"])

        avg_load_time = sum(r["metrics"].get("load_time", 0) for r in all_results) / len(all_results)

        print(f"\n✅ Passed:       {passed}/{len(all_results)}")
        print(f"❌ Failed:       {failed}/{len(all_results)}")
        print(f"⚠️  Warnings:     {warnings}/{len(all_results)}")
        print(f"\n⏱️  Total time:   {total_time:.2f}s")
        print(f"⚡ Avg load:     {avg_load_time:.0f}ms")
        print(f"🚀 Speedup:      ~{len(modules)/max_concurrent:.1f}x faster than sequential")

        # Save results
        report = {
            "summary": {
                "total": len(all_results),
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "total_time": round(total_time, 2),
                "avg_load_time": round(avg_load_time),
            },
            "results": all_results
        }

        report_file = Path("./parallel_test_results.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Report saved: {report_file}")
        print("=" * 80 + "\n")

        return report


async def compare_sequential_vs_parallel():
    """Compare sequential vs parallel testing performance."""

    modules = [
        ("connect-id", "Connect-ID"),
        ("connect-data", "Connect-Data"),
        ("connect-reports", "Connect-Reports"),
        ("connect-manager", "Connect-Manager"),
        ("connect-config", "Connect-Config"),
        ("connect-scenario", "Connect-Scenario"),
        ("connect-template", "Connect-Template"),
        ("connect-test", "Connect-Test"),
        ("connect-protocol", "Connect-Protocol"),
    ]

    print("\n" + "=" * 80)
    print("⚡ PERFORMANCE COMPARISON: Sequential vs Parallel")
    print("=" * 80)

    # Test 1: Sequential (1 at a time)
    print("\n📊 Test 1: SEQUENTIAL (1 at a time)")
    print("-" * 80)
    start = asyncio.get_event_loop().time()
    await parallel_test(modules, headless=True, max_concurrent=1)
    sequential_time = asyncio.get_event_loop().time() - start

    # Test 2: Parallel (5 at a time)
    print("\n📊 Test 2: PARALLEL (5 at a time)")
    print("-" * 80)
    start = asyncio.get_event_loop().time()
    await parallel_test(modules, headless=True, max_concurrent=5)
    parallel_time = asyncio.get_event_loop().time() - start

    # Comparison
    print("\n" + "=" * 80)
    print("🏆 PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"\n📊 Sequential (1 at a time):  {sequential_time:.2f}s")
    print(f"⚡ Parallel (5 at a time):    {parallel_time:.2f}s")
    print(f"\n🚀 Speedup:                    {sequential_time/parallel_time:.2f}x FASTER!")
    print(f"⏱️  Time saved:                 {sequential_time - parallel_time:.2f}s")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parallel testing for C2004")
    parser.add_argument("--compare", action="store_true", help="Compare sequential vs parallel")
    parser.add_argument("--concurrent", type=int, default=5, help="Max concurrent tests (default: 5)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")

    args = parser.parse_args()

    modules = [
        ("connect-id", "Connect-ID"),
        ("connect-data", "Connect-Data"),
        ("connect-reports", "Connect-Reports"),
        ("connect-manager", "Connect-Manager"),
        ("connect-config", "Connect-Config"),
        ("connect-scenario", "Connect-Scenario"),
        ("connect-template", "Connect-Template"),
        ("connect-test", "Connect-Test"),
        ("connect-protocol", "Connect-Protocol"),
    ]

    if args.compare:
        asyncio.run(compare_sequential_vs_parallel())
    else:
        asyncio.run(parallel_test(modules, headless=args.headless, max_concurrent=args.concurrent))

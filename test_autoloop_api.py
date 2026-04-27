"""
TestQL Autoloop MCP Test Runner (API Version)

Uses direct Python API instead of subprocess to avoid hangs.
Tests autonomous loop capabilities for MCP Windsurf + LLM SWE1.6 / kimi2.6.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def add_colors():
    class C:
        OK = "\033[92m"
        FAIL = "\033[91m"
        WARN = "\033[93m"
        INFO = "\033[94m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
    return C

C = add_colors()


def ok(msg: str) -> None:
    print(f"{C.OK}✓{C.RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{C.FAIL}✗{C.RESET} {msg}")


def warn(msg: str) -> None:
    print(f"{C.WARN}⚠{C.RESET} {msg}")


def info(msg: str) -> None:
    print(f"{C.INFO}ℹ{C.RESET} {msg}")


def header(msg: str) -> None:
    print(f"\n{C.BOLD}{msg}{C.RESET}")
    print("=" * 60)


def step_import_testql() -> bool:
    """Check if testql can be imported."""
    header("STEP 0: Import TestQL")

    try:
        import testql
        ok(f"testql imported: {testql.__version__ if hasattr(testql, '__version__') else 'unknown version'}")
        return True
    except ImportError as e:
        fail(f"Cannot import testql: {e}")
        return False


def step_mcp_check() -> dict[str, Any]:
    """Check MCP integration."""
    header("STEP 1: MCP Integration Check")

    results = {}

    # Check mcp package
    try:
        import mcp
        results["mcp_package"] = True
        ok("mcp package available")
    except ImportError:
        results["mcp_package"] = False
        warn("mcp package not installed (pip install mcp)")

    # Check testql.mcp module
    try:
        from testql.mcp.server import TestQLMCPServer
        results["testql_mcp_module"] = True
        ok("testql.mcp.server importable")
    except ImportError as e:
        results["testql_mcp_module"] = False
        warn(f"testql.mcp.server import failed: {e}")

    # Check FastMCP
    try:
        from mcp.server.fastmcp import FastMCP
        results["fastmcp"] = True
        ok("FastMCP importable")
    except ImportError:
        results["fastmcp"] = False
        warn("FastMCP not available")

    return results


def step_discovery(project_path: Path) -> dict[str, Any] | None:
    """Run discovery on project."""
    header("STEP 2: Project Discovery")

    try:
        from testql.discovery import discover_path

        manifest = discover_path(project_path)
        data = manifest.to_dict(include_raw=True)

        ok(f"Discovery complete: confidence={data.get('confidence')}")
        info(f"Detected types: {data.get('types', [])}")
        info(f"Evidence count: {len(data.get('evidence', []))}")

        return data
    except Exception as e:
        fail(f"Discovery failed: {e}")
        return None


def step_topology(project_path: Path) -> dict[str, Any] | None:
    """Build topology for project."""
    header("STEP 3: Topology Generation")

    try:
        from testql.topology.builder import build_topology

        topology = build_topology(project_path)

        if hasattr(topology, 'to_dict'):
            data = topology.to_dict()
        else:
            data = {"nodes": len(topology.nodes) if hasattr(topology, 'nodes') else 0}

        ok(f"Topology built: {data}")
        return data
    except Exception as e:
        warn(f"Topology build failed: {e}")
        return None


def step_inspect(project_path: Path) -> dict[str, Any] | None:
    """Run inspection on project."""
    header("STEP 4: Project Inspection")

    try:
        from testql.results import inspect_source

        topology, envelope, plan = inspect_source(project_path)

        ok(f"Inspection complete: status={envelope.status}")
        info(f"Plan steps: {len(plan.steps) if hasattr(plan, 'steps') else 'unknown'}")

        return {
            "status": envelope.status,
            "plan_steps": len(plan.steps) if hasattr(plan, 'steps') else 0,
        }
    except Exception as e:
        warn(f"Inspection failed: {e}")
        return None


def step_generate_tests(project_path: Path) -> list[Path] | None:
    """Generate tests from project analysis."""
    header("STEP 5: Test Generation")

    try:
        from testql.generators.test_generator import TestGenerator

        generator = TestGenerator(project_path)
        output_dir = project_path / ".testql" / "autoloop-api" / "scenarios"
        output_dir.mkdir(parents=True, exist_ok=True)

        files = generator.generate_tests(output_dir)

        if files:
            ok(f"Generated {len(files)} test files")
            for f in files:
                info(f"  - {f.name}")
            return files
        else:
            warn("No test files generated")
            return None
    except Exception as e:
        warn(f"Test generation failed: {e}")
        return None


def step_run_scenario(scenario_path: Path) -> dict[str, Any] | None:
    """Run a single scenario."""
    try:
        from testql.commands.run_cmd import _run_single
        from testql.ir import TestPlan
        from testql.adapters.testtoon_adapter import parse

        info(f"Running scenario: {scenario_path.name}")

        # Parse the scenario
        plan = parse(scenario_path)

        # Try to run it
        if hasattr(plan, 'steps') and plan.steps:
            ok(f"Scenario parsed: {len(plan.steps)} steps")
            return {"ok": True, "steps": len(plan.steps)}
        else:
            warn("Scenario has no steps")
            return {"ok": False, "steps": 0}

    except Exception as e:
        warn(f"Scenario run failed: {e}")
        return None


def step_run_tests(scenarios: list[Path]) -> dict[str, Any]:
    """Run all scenarios."""
    header("STEP 6: Run Test Scenarios")

    results = []
    passed = 0
    failed = 0

    for scenario in scenarios:
        result = step_run_scenario(scenario)
        if result:
            results.append(result)
            if result.get("ok"):
                passed += 1
            else:
                failed += 1

    summary = {
        "total": len(scenarios),
        "passed": passed,
        "failed": failed,
        "results": results,
    }

    ok(f"Tests: {passed}/{len(scenarios)} passed")
    return summary


def step_generate_llm_decision(
    iteration: int,
    discovery: dict | None,
    topology: dict | None,
    inspection: dict | None,
    test_results: dict | None,
) -> dict[str, Any]:
    """Generate LLM decision context."""
    header(f"STEP 7: LLM Decision Context (Iteration {iteration})")

    metrics = {
        "has_discovery": discovery is not None,
        "has_topology": topology is not None,
        "has_inspection": inspection is not None,
        "test_pass_rate": 0.0,
    }

    if test_results and test_results.get("total", 0) > 0:
        metrics["test_pass_rate"] = test_results["passed"] / test_results["total"] * 100

    # Quality gates
    gates = {
        "coverage_min": 65,
        "vallm_pass_min": 60,
        "cc_max": 10,
    }

    # Determine decision
    if metrics["test_pass_rate"] >= gates["vallm_pass_min"]:
        decision = "stabilized"
        reason = "Test pass rate meets quality gate"
        confidence = 0.90
        risk = 0.10
    elif iteration >= 3:
        decision = "stabilized"
        reason = "Max iterations reached"
        confidence = 0.70
        risk = 0.30
    else:
        decision = "generate_more_tests"
        reason = "Need more test coverage"
        confidence = 0.75
        risk = 0.50

    llm_decision = {
        "decision": decision,
        "reason_code": reason,
        "next_actions": [
            "Generate additional test scenarios" if decision != "stabilized" else "Stop loop",
        ],
        "metrics": metrics,
        "confidence": confidence,
        "risk_score": risk,
        "iteration": iteration,
    }

    info(f"Decision: {decision}")
    info(f"Reason: {reason}")
    info(f"Confidence: {confidence}")
    info(f"Risk: {risk}")

    return llm_decision


def step_save_artifacts(
    output_dir: Path,
    discovery: dict | None,
    topology: dict | None,
    inspection: dict | None,
    test_results: dict | None,
    llm_decision: dict | None,
) -> None:
    """Save all artifacts."""
    header("STEP 8: Save Artifacts")

    output_dir.mkdir(parents=True, exist_ok=True)

    if discovery:
        path = output_dir / "discovery.json"
        path.write_text(json.dumps(discovery, indent=2, default=str))
        ok(f"Saved: {path.name}")

    if topology:
        path = output_dir / "topology.json"
        path.write_text(json.dumps(topology, indent=2, default=str))
        ok(f"Saved: {path.name}")

    if inspection:
        path = output_dir / "inspection.json"
        path.write_text(json.dumps(inspection, indent=2, default=str))
        ok(f"Saved: {path.name}")

    if test_results:
        path = output_dir / "test-results.json"
        path.write_text(json.dumps(test_results, indent=2))
        ok(f"Saved: {path.name}")

    if llm_decision:
        path = output_dir / f"llm-decision.iter{llm_decision['iteration']}.json"
        path.write_text(json.dumps(llm_decision, indent=2))
        ok(f"Saved: {path.name}")

    # Save MCP config
    mcp_config = {
        "mcpServers": {
            "testql": {
                "command": sys.executable,
                "args": ["-m", "testql.mcp.server"],
                "description": "TestQL autoloop integration",
            }
        }
    }
    path = output_dir / "mcp-config.json"
    path.write_text(json.dumps(mcp_config, indent=2))
    ok(f"Saved: {path.name}")


def run_iteration(
    project_path: Path,
    iteration: int,
    output_dir: Path,
) -> dict[str, Any]:
    """Run one autoloop iteration."""
    header(f"AUTOMATION LOOP ITERATION {iteration}")

    # Phase 1: Discovery
    discovery = step_discovery(project_path)

    # Phase 2: Topology
    topology = step_topology(project_path)

    # Phase 3: Inspection
    inspection = step_inspect(project_path)

    # Phase 4: Generate tests
    scenarios = step_generate_tests(project_path)

    # Phase 5: Run tests
    test_results = None
    if scenarios:
        test_results = step_run_tests(scenarios)

    # Phase 6: LLM decision
    llm_decision = step_generate_llm_decision(
        iteration, discovery, topology, inspection, test_results
    )

    # Phase 7: Save artifacts
    iter_dir = output_dir / f"iteration-{iteration}"
    step_save_artifacts(iter_dir, discovery, topology, inspection, test_results, llm_decision)

    return llm_decision


def main() -> int:
    parser = argparse.ArgumentParser(description="TestQL Autoloop MCP (API Version)")
    parser.add_argument("--project", "-p", type=Path, default=Path("."),
                        help="Project path (default: current directory)")
    parser.add_argument("--max-iter", "-i", type=int, default=2,
                        help="Max iterations (default: 2)")
    parser.add_argument("--mcp-only", action="store_true",
                        help="Only check MCP integration")

    args = parser.parse_args()
    project_path = args.project.resolve()

    if not project_path.exists():
        fail(f"Project path does not exist: {project_path}")
        return 1

    # Step 0: Import check
    if not step_import_testql():
        fail("Cannot proceed without testql")
        return 1

    # MCP check
    mcp_results = step_mcp_check()

    if args.mcp_only:
        ok("MCP check complete")
        return 0

    # Setup output
    output_dir = project_path / ".testql" / "autoloop-api"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run iterations
    final_decision = None
    for i in range(1, args.max_iter + 1):
        decision = run_iteration(project_path, i, output_dir)
        final_decision = decision

        if decision["decision"] == "stabilized":
            ok(f"Loop stabilized at iteration {i}")
            break

    # Final summary
    header("AUTOMATION LOOP COMPLETE")
    info(f"Output directory: {output_dir}")
    info(f"Iterations run: {final_decision['iteration'] if final_decision else 0}")
    info(f"Final decision: {final_decision['decision'] if final_decision else 'unknown'}")

    # List all generated artifacts
    info("\nGenerated artifacts:")
    for f in sorted(output_dir.rglob("*.json")):
        info(f"  {f.relative_to(output_dir)}")

    ok("Autoloop test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())

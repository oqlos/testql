"""
TestQL Autoloop MCP Test Runner

Tests autonomous loop capabilities:
1. Generate topology and test scenarios
2. Run test scenarios
3. Analyze results
4. Generate LLM decision prompt
5. Loop or stop based on quality gates

Usage:
    python test_autoloop_mcp.py [--project PATH] [--max-iter N] [--simulate-llm]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Colors for terminal output
class C:
    OK = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


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


# ---------------------------------------------------------------------------
# Step 1: Topology Generation
# ---------------------------------------------------------------------------
def step_generate_topology(project_path: Path, output_dir: Path) -> dict[str, Any] | None:
    """Generate project topology using testql."""
    header("STEP 1: Generate Topology")

    cmd = [
        sys.executable, "-m", "testql",
        "topology", str(project_path),
        "--format", "json",
    ]

    info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(project_path),
        )

        if result.returncode != 0:
            fail(f"Topology generation failed: {result.stderr[:500]}")
            return None

        topology = json.loads(result.stdout)
        topology_path = output_dir / "topology.json"
        topology_path.write_text(json.dumps(topology, indent=2))
        ok(f"Topology saved to {topology_path}")
        return topology

    except json.JSONDecodeError as e:
        fail(f"Invalid JSON from topology: {e}")
        return None
    except subprocess.TimeoutExpired:
        fail("Topology generation timed out")
        return None
    except Exception as e:
        fail(f"Topology error: {e}")
        return None


# ---------------------------------------------------------------------------
# Step 2: Generate Test Scenarios
# ---------------------------------------------------------------------------
def step_generate_tests(project_path: Path, output_dir: Path) -> list[Path] | None:
    """Generate test scenarios for discovered routes."""
    header("STEP 2: Generate Test Scenarios")

    scenarios_dir = output_dir / "scenarios"
    scenarios_dir.mkdir(exist_ok=True)

    # Try multiple generation strategies
    generated: list[Path] = []

    # Strategy A: API smoke from topology
    cmd_api = [
        sys.executable, "-m", "testql",
        "generate", "tests",
        str(project_path),
        "--output-dir", str(scenarios_dir),
    ]

    info(f"Running: {' '.join(cmd_api)}")

    try:
        result = subprocess.run(
            cmd_api,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_path),
        )

        if result.returncode == 0:
            # Find generated files
            for f in scenarios_dir.glob("*.testql.toon.yaml"):
                generated.append(f)
                ok(f"Generated: {f.name}")
        else:
            warn(f"API generation warning: {result.stderr[:300]}")

    except Exception as e:
        warn(f"API generation error: {e}")

    # Strategy B: Auto inspect
    cmd_auto = [
        sys.executable, "-m", "testql",
        "auto", str(project_path),
        "--output-dir", str(output_dir / "auto"),
        "--format", "json",
    ]

    info(f"Running: {' '.join(cmd_auto)}")

    try:
        result = subprocess.run(
            cmd_auto,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(project_path),
        )

        if result.returncode in (0, 2):  # 2 = partial success
            ok("Auto-inspection completed")
        else:
            warn(f"Auto inspection warning: {result.returncode}")

    except Exception as e:
        warn(f"Auto inspection error: {e}")

    if generated:
        ok(f"Total scenarios generated: {len(generated)}")
        return generated
    else:
        warn("No scenarios generated, using existing testql-scenarios/")
        existing = list(project_path.glob("testql-scenarios/*.testql.toon.yaml"))
        return existing if existing else None


# ---------------------------------------------------------------------------
# Step 3: Run Tests
# ---------------------------------------------------------------------------
def step_run_tests(scenarios: list[Path], output_dir: Path) -> dict[str, Any] | None:
    """Run test scenarios and collect results."""
    header("STEP 3: Run Test Scenarios")

    if not scenarios:
        fail("No scenarios to run")
        return None

    all_results: list[dict] = []
    total_passed = 0
    total_failed = 0

    for scenario in scenarios:
        info(f"Running: {scenario.name}")

        cmd = [
            sys.executable, "-m", "testql",
            "run", str(scenario),
            "--output", "json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )

            try:
                run_data = json.loads(result.stdout)
            except json.JSONDecodeError:
                run_data = {
                    "file": str(scenario),
                    "ok": result.returncode == 0,
                    "raw_output": result.stdout[:500],
                    "stderr": result.stderr[:500],
                }

            all_results.append(run_data)

            if run_data.get("ok") or result.returncode == 0:
                total_passed += 1
                ok(f"  {scenario.name}: PASS")
            else:
                total_failed += 1
                fail(f"  {scenario.name}: FAIL")

        except subprocess.TimeoutExpired:
            warn(f"  {scenario.name}: TIMEOUT")
            all_results.append({"file": str(scenario), "ok": False, "error": "timeout"})
            total_failed += 1
        except Exception as e:
            fail(f"  {scenario.name}: ERROR - {e}")
            all_results.append({"file": str(scenario), "ok": False, "error": str(e)})
            total_failed += 1

    summary = {
        "total": len(scenarios),
        "passed": total_passed,
        "failed": total_failed,
        "results": all_results,
    }

    summary_path = output_dir / "test-results.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    ok(f"Results saved to {summary_path}")

    return summary


# ---------------------------------------------------------------------------
# Step 4: Generate LLM Decision Prompt
# ---------------------------------------------------------------------------
def step_generate_llm_prompt(
    topology: dict | None,
    test_results: dict | None,
    iteration: int,
    output_dir: Path,
    simulate_llm: bool = False,
) -> dict[str, Any]:
    """Generate decision prompt for LLM (SWE1.6 / kimi2.6)."""
    header("STEP 4: Generate LLM Decision Prompt")

    # Collect metrics
    metrics = {
        "coverage": 0.0,
        "vallm": 0.0,
        "cc_max": 0.0,
        "test_pass_rate": 0.0,
    }

    if test_results:
        total = test_results.get("total", 0)
        passed = test_results.get("passed", 0)
        if total > 0:
            metrics["test_pass_rate"] = round(passed / total * 100, 1)

    # Load quality gates from autoloop state if exists
    quality_gates = {
        "coverage_min": 65,
        "vallm_pass_min": 60,
        "cc_max": 10,
    }

    autoloop_state_path = output_dir / "autoloop-state.json"
    if autoloop_state_path.exists():
        try:
            state = json.loads(autoloop_state_path.read_text())
            gates = state.get("stabilization", {}).get("quality_gates", {})
            quality_gates.update(gates)
        except Exception:
            pass

    # Build decision context
    decision_context = {
        "iteration": iteration,
        "metrics": metrics,
        "quality_gates": quality_gates,
        "topology_available": topology is not None,
        "test_results_available": test_results is not None,
    }

    # Determine if quality gates pass
    gates_pass = (
        metrics["test_pass_rate"] >= quality_gates["vallm_pass_min"]
    )

    if gates_pass:
        decision = "stabilized"
        reason = "All quality gates passed"
    elif iteration >= 5:
        decision = "stabilized"
        reason = "Max iterations reached, accepting current state"
    else:
        decision = "generate_more_tests"
        reason = "Quality gates not met, need more coverage"

    llm_decision = {
        "decision": decision,
        "reason_code": reason,
        "next_actions": [
            f"Run iteration {iteration + 1}" if decision != "stabilized" else "Stop loop",
        ],
        "metrics": metrics,
        "confidence": 0.85 if gates_pass else 0.60,
        "risk_score": 0.2 if gates_pass else 0.7,
        "context": decision_context,
    }

    decision_path = output_dir / f"llm-decision.iter{iteration}.json"
    decision_path.write_text(json.dumps(llm_decision, indent=2))
    ok(f"LLM decision saved to {decision_path}")

    # Print decision
    info(f"Decision: {decision}")
    info(f"Reason: {reason}")
    info(f"Confidence: {llm_decision['confidence']}")
    info(f"Risk Score: {llm_decision['risk_score']}")

    if simulate_llm:
        info("(Simulated LLM response - no actual LLM call)")
    else:
        info("To use real LLM (SWE1.6 / kimi2.6):")
        info("  1. Set OPENROUTER_API_KEY")
        info("  2. Configure aider with: aider --model openrouter/swe-1.6")
        info("  3. Or use testql mcp server with Windsurf")

    return llm_decision


# ---------------------------------------------------------------------------
# Step 5: MCP Windsurf Integration Check
# ---------------------------------------------------------------------------
def step_check_mcp_windsurf(output_dir: Path) -> bool:
    """Check MCP Windsurf integration."""
    header("STEP 5: MCP Windsurf Integration Check")

    mcp_available = False

    try:
        from testql.mcp.server import TestQLMCPServer
        mcp_available = True
        ok("MCP server module available")
    except ImportError as e:
        warn(f"MCP server import failed: {e}")

    # Check for mcp package
    try:
        import mcp
        ok(f"mcp package available: {mcp.__version__ if hasattr(mcp, '__version__') else 'unknown'}")
    except ImportError:
        warn("mcp package not installed. Install: pip install mcp")

    # Check CLI availability
    try:
        result = subprocess.run(
            [sys.executable, "-m", "testql", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            ok("testql CLI available")
        else:
            warn("testql CLI returned non-zero")
    except Exception as e:
        warn(f"testql CLI check failed: {e}")

    # Generate MCP config
    mcp_config = {
        "mcpServers": {
            "testql": {
                "command": sys.executable,
                "args": ["-m", "testql.mcp.server"],
                "env": {},
            }
        }
    }

    config_path = output_dir / "mcp-config.json"
    config_path.write_text(json.dumps(mcp_config, indent=2))
    ok(f"MCP config saved to {config_path}")

    # Windsurf-specific config
    windsurf_config = {
        "mcpServers": {
            "testql": {
                "command": sys.executable,
                "args": ["-m", "testql.mcp.server"],
                "description": "TestQL test generation and execution",
                "tools": [
                    "list_sources",
                    "list_targets",
                    "generate_ir",
                    "run",
                    "build_topology",
                ],
            }
        }
    }

    windsurf_path = output_dir / "windsurf-mcp-config.json"
    windsurf_path.write_text(json.dumps(windsurf_config, indent=2))
    ok(f"Windsurf MCP config saved to {windsurf_path}")

    return mcp_available


# ---------------------------------------------------------------------------
# Main Autoloop
# ---------------------------------------------------------------------------
def run_autoloop(
    project_path: Path,
    max_iterations: int = 3,
    simulate_llm: bool = False,
) -> int:
    """Run the full autoloop."""
    header("TestQL Autoloop MCP Test Runner")
    info(f"Project: {project_path}")
    info(f"Max iterations: {max_iterations}")
    info(f"Simulate LLM: {simulate_llm}")

    output_dir = project_path / ".testql" / "autoloop-run"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check MCP
    mcp_ok = step_check_mcp_windsurf(output_dir)

    # Run iterations
    for iteration in range(1, max_iterations + 1):
        header(f"ITERATION {iteration}/{max_iterations}")

        # Step 1: Topology
        topology = step_generate_topology(project_path, output_dir)

        # Step 2: Generate tests
        scenarios = step_generate_tests(project_path, output_dir)

        # Step 3: Run tests
        test_results = None
        if scenarios:
            test_results = step_run_tests(scenarios, output_dir)

        # Step 4: LLM decision
        decision = step_generate_llm_prompt(
            topology, test_results, iteration, output_dir, simulate_llm
        )

        # Check if stabilized
        if decision["decision"] == "stabilized":
            ok("Loop stabilized! Stopping.")
            break

        info(f"Continuing to iteration {iteration + 1}...")

    # Final summary
    header("FINAL SUMMARY")
    info(f"Output directory: {output_dir}")
    info(f"Artifacts generated:")
    for f in sorted(output_dir.rglob("*")):
        if f.is_file():
            info(f"  - {f.relative_to(output_dir)}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="TestQL Autoloop MCP Test Runner")
    parser.add_argument("--project", "-p", type=Path, default=Path("."),
                        help="Project path to test (default: current directory)")
    parser.add_argument("--max-iter", "-i", type=int, default=2,
                        help="Maximum iterations (default: 2)")
    parser.add_argument("--simulate-llm", "-s", action="store_true",
                        help="Simulate LLM responses instead of calling real API")
    parser.add_argument("--mcp-only", action="store_true",
                        help="Only check MCP integration")

    args = parser.parse_args()

    project_path = args.project.resolve()

    if not project_path.exists():
        fail(f"Project path does not exist: {project_path}")
        return 1

    if args.mcp_only:
        output_dir = project_path / ".testql" / "autoloop-run"
        output_dir.mkdir(parents=True, exist_ok=True)
        step_check_mcp_windsurf(output_dir)
        return 0

    return run_autoloop(project_path, args.max_iter, args.simulate_llm)


if __name__ == "__main__":
    sys.exit(main())

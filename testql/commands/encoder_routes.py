"""REST API routes for OQL file operations (list, read, run, logs)."""

from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse, JSONResponse

if TYPE_CHECKING:
    from typing import Any

try:
    from hub import hub
except ImportError:
    hub = None  # type: ignore[assignment]

try:
    from models import RunLineRequest, RunFileRequest
except ImportError:
    from pydantic import BaseModel

    class RunLineRequest(BaseModel):  # type: ignore[no-redef]
        line: str = ""

    class RunFileRequest(BaseModel):  # type: ignore[no-redef]
        path: str = ""

router = APIRouter(prefix="/oql", tags=["oql"])

# ── Paths ─────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OQL_DIR = PROJECT_ROOT / "testql" / "scenarios"
LOG_DIR = OQL_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WAIT_MS = 100
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404

LEGACY_C2004_ROOT_SEGMENT = "db/dsl/oql/"
TESTQL_SCENARIOS_SEGMENT = "testql/scenarios/"


def _strip_path_segments(candidate: str) -> str:
    """Remove known legacy prefix segments, returning the relative tail."""
    candidate = candidate.removeprefix("./")
    if LEGACY_C2004_ROOT_SEGMENT in candidate:
        candidate = candidate.split(LEGACY_C2004_ROOT_SEGMENT, 1)[1]
    if TESTQL_SCENARIOS_SEGMENT in candidate:
        candidate = candidate.split(TESTQL_SCENARIOS_SEGMENT, 1)[1]
    return candidate.lstrip("/")


def _migrate_legacy_extension(candidate: str) -> str:
    """Replace .oql/.tql with .testql.toon.yaml when the target file exists."""
    for old_ext in ('.oql', '.tql'):
        if candidate.endswith(old_ext):
            new_candidate = candidate[:-len(old_ext)] + '.testql.toon.yaml'
            if (OQL_DIR / new_candidate).is_file():
                return new_candidate
    return candidate


def _remap_tests_prefix(candidate: str) -> str:
    """Remap legacy tests/ prefix to c2004/views/ hierarchy."""
    if candidate.startswith("tests/views/"):
        return f"c2004/views/views/{candidate[len('tests/views/'):]}"
    if candidate.startswith("tests/"):
        return f"c2004/views/{candidate[len('tests/'):]}"
    return candidate


def _normalize_oql_path(path: str) -> str:
    """Map legacy c2004 OQL paths to the canonical testql scenario layout.

    Supports .testql.toon.yaml, .oql, and .tql extensions.
    """
    candidate = (path or "").strip().replace("\\", "/")
    if not candidate:
        return ""
    candidate = _strip_path_segments(candidate)
    candidate = _migrate_legacy_extension(candidate)
    return _remap_tests_prefix(candidate)


def _resolve_oql_path(path: str) -> tuple[str, Path]:
    normalized_path = _normalize_oql_path(path)
    return normalized_path, (OQL_DIR / normalized_path).resolve()


# ── OQL command executor ──────────────────────────────────────────

_ENCODER_SIMPLE_CMDS = {
    "ENCODER_ON": "activate",
    "ENCODER_OFF": "deactivate",
    "ENCODER_CLICK": "click",
    "ENCODER_DBLCLICK": "cancel",
    "ENCODER_STATUS": "status",
    "ENCODER_PAGE_NEXT": "pageNext",
    "ENCODER_PAGE_PREV": "pagePrev",
}


def _assert_bool_prop(result: dict, prop: str, expected: str | None) -> tuple[Any, bool]:
    actual = result.get(prop, False)
    passed = bool(actual) if expected is None else (str(actual).lower() == expected.lower())
    return actual, passed


def _assert_count_prop(result: dict, expected: str | None) -> tuple[Any, bool]:
    actual = result.get("count", 0)
    passed = (str(actual) == expected) if expected else actual > 0
    return actual, passed


def _assert_text_prop(result: dict, expected: str | None) -> tuple[Any, bool]:
    actual = result.get("text", "")
    passed = (expected in actual) if expected else len(actual) > 0
    return actual, passed


def _assert_classes_prop(result: dict, expected: str | None) -> tuple[Any, bool]:
    actual = result.get("classes", "")
    passed = (expected in actual) if expected else True
    return actual, passed


def _evaluate_assertion(result: dict, prop: str, expected: str | None) -> tuple[Any, bool]:
    """Evaluate an ASSERT property check. Returns (actual, passed)."""
    if prop in ("exists", "visible"):
        return _assert_bool_prop(result, prop, expected)
    if prop == "count":
        return _assert_count_prop(result, expected)
    if prop == "text":
        return _assert_text_prop(result, expected)
    if prop == "classes":
        return _assert_classes_prop(result, expected)
    actual = result.get(prop, None)
    passed = (str(actual) == expected) if expected else actual is not None
    return actual, passed


def _format_log_detail(cmd: str, result: dict) -> str:
    """Build a human-readable detail suffix for a log line."""
    if cmd == "ASSERT":
        if result.get("assertion"):
            return f" [{result['assertion']}] {result.get('prop', '')}={result.get('actual', '?')} (expected: {result.get('expected', '*')})"
        return f" ERROR: {result.get('error', 'unknown')}"
    if cmd == "NAVIGATE":
        return f" url={result.get('url', '?')}"
    if cmd == "CLICK":
        return f" sel={result.get('selector', '?')}"
    if "result" in result and isinstance(result["result"], dict):
        r = result["result"]
        return f" zone={r.get('zone', '-')} item={r.get('itemIndex', '-')}/{r.get('itemCount', '-')}"
    return ""


async def _exec_encoder_cmd(cmd: str, arg: str) -> dict[str, Any]:
    """Handle ENCODER_* commands."""
    if cmd in _ENCODER_SIMPLE_CMDS:
        result = await hub.send_command(_ENCODER_SIMPLE_CMDS[cmd])
        return {"ok": True, "command": cmd, "result": result}
    if cmd == "ENCODER_SCROLL":
        result = await hub.send_command("scroll", delta=int(arg) if arg else 1)
        return {"ok": True, "command": cmd, "result": result}
    if cmd == "ENCODER_FOCUS":
        result = await hub.send_command("focus", zone=arg or "col3")
        return {"ok": True, "command": cmd, "result": result}
    return None  # type: ignore[return-value]


async def _exec_browser_cmd(cmd: str, arg: str, raw_arg: str) -> dict[str, Any]:
    """Handle NAVIGATE, CLICK, QUERY commands."""
    if cmd == "NAVIGATE":
        url = arg or "/"
        result = await hub.send_oql_command("navigate", url=url)
        return {"ok": result.get("ok", False), "command": cmd, "url": url, "result": result}
    if cmd == "CLICK":
        if not arg:
            return {"ok": False, "command": cmd, "error": "missing selector"}
        result = await hub.send_oql_command("click", selector=arg)
        return {"ok": result.get("ok", False), "command": cmd, "selector": arg, "result": result}
    if cmd == "QUERY":
        m = re.match(r'"([^"]+)"\s*(.*)', raw_arg) if raw_arg else None
        selector, prop = (m.group(1), m.group(2).strip() or "exists") if m else (arg, "exists")
        result = await hub.send_oql_command("query", selector=selector, prop=prop)
        return {"ok": result.get("ok", False), "command": cmd, "selector": selector, "result": result}
    return None  # type: ignore[return-value]


async def _exec_assert_cmd(raw_arg: str) -> dict[str, Any]:
    """Handle ASSERT command."""
    m = re.match(r'"([^"]+)"\s*(.*)', raw_arg) if raw_arg else None
    if not m:
        return {"ok": False, "command": "ASSERT", "error": "syntax: ASSERT \"selector\" [prop] [expected]"}
    selector = m.group(1)
    rest = m.group(2).strip().split(None, 1)
    prop = rest[0] if rest else "exists"
    expected = rest[1].strip('"\'') if len(rest) > 1 else None

    result = await hub.send_oql_command("query", selector=selector, prop=prop)
    if not result.get("ok"):
        return {"ok": False, "command": "ASSERT", "selector": selector, "error": result.get("error", "query_failed"), "result": result}

    actual, passed = _evaluate_assertion(result, prop, expected)
    return {
        "ok": passed, "command": "ASSERT", "selector": selector,
        "prop": prop, "expected": expected, "actual": actual,
        "assertion": "PASS" if passed else "FAIL",
        "result": result,
    }


async def _execute_oql_line(line: str) -> dict[str, Any]:
    """Execute a single OQL command line. Returns structured result dict."""
    line = line.strip()
    if not line or line.startswith("#"):
        return {"ok": True, "skipped": True}

    parts = line.split(None, 1)
    cmd = parts[0].upper()
    raw_arg = parts[1].strip() if len(parts) > 1 else ""
    arg = raw_arg.strip('"\'')

    if cmd.startswith("ENCODER_"):
        return await _exec_encoder_cmd(cmd, arg)

    if cmd in ("NAVIGATE", "CLICK", "QUERY"):
        return await _exec_browser_cmd(cmd, arg, raw_arg)

    if cmd == "ASSERT":
        return await _exec_assert_cmd(raw_arg)

    if cmd == "WAIT":
        ms = int(arg) if arg else DEFAULT_WAIT_MS
        await asyncio.sleep(ms / 1000.0)
        return {"ok": True, "command": "WAIT", "ms": ms}
    if cmd in ("SET", "LOG", "PRINT"):
        return {"ok": True, "command": cmd, "arg": arg, "note": "logged"}
    return {"ok": False, "error": f"unknown command: {cmd}"}




# ── Route handlers ────────────────────────────────────────────────

@router.get("/files")
async def oql_list_files():
    """List all .testql.toon.yaml files in the project (with .oql/.tql fallback)."""
    files = []
    if OQL_DIR.is_dir():
        for pattern in ("*.testql.toon.yaml", "*.oql", "*.tql"):
            for f in sorted(OQL_DIR.rglob(pattern)):
                rel = f.relative_to(OQL_DIR)
                files.append({
                    "path": str(rel),
                    "name": f.name,
                    "dir": str(rel.parent) if str(rel.parent) != "." else "",
                    "size": f.stat().st_size,
                })
    # Deduplicate by path (prefer .testql.toon.yaml)
    seen = set()
    unique = []
    for f in files:
        if f["path"] not in seen:
            seen.add(f["path"])
            unique.append(f)
    return {"files": unique, "base_dir": str(OQL_DIR)}


@router.get("/file")
async def oql_read_file(path: str = Query(...)):
    """Read a TestQL file content (.testql.toon.yaml / .oql / .tql)."""
    normalized_path, target = _resolve_oql_path(path)
    if not str(target).startswith(str(OQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)
    content = target.read_text(encoding="utf-8")
    return {
        "path": normalized_path,
        "requested_path": path,
        "content": content,
        "lines": content.count("\n") + 1,
    }


@router.get("/tables")
async def oql_list_tables(path: str = Query(...)):
    """Extract table names from an OQL file."""
    normalized_path, target = _resolve_oql_path(path)
    if not str(target).startswith(str(OQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)

    content = target.read_text(encoding="utf-8")
    tables = _extract_table_names(content)
    return {"path": normalized_path, "requested_path": path, "tables": tables}


def _extract_table_names(content: str) -> list[str]:
    """Return sorted unique table names referenced in OQL content."""
    table_patterns = [
        r'TABLE\s+["\']?(\w+)["\']?',
        r'FROM\s+["\']?(\w+)["\']?',
        r'INTO\s+["\']?(\w+)["\']?',
        r'JOIN\s+["\']?(\w+)["\']?',
    ]
    tables: list[str] = []
    for pattern in table_patterns:
        tables.extend(re.findall(pattern, content, re.IGNORECASE))
    return sorted(set(tables))


@router.post("/run-line")
async def oql_run_line(req: RunLineRequest):
    """Execute a single OQL command line via the encoder bridge."""
    return await _execute_oql_line(req.line)


@router.post("/run-file")
async def oql_run_file(req: RunFileRequest):
    """Run an entire OQL file with validation. Returns structured results + saves log."""
    normalized_path, target = _resolve_oql_path(req.path)
    if not str(target).startswith(str(OQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found", "path": normalized_path}, status_code=HTTP_NOT_FOUND)

    lines = target.read_text(encoding="utf-8").splitlines()
    results, counters, log_lines = await _run_oql_lines(lines, normalized_path)
    summary = _build_run_summary(normalized_path, req.path, lines, results, counters)

    log_file = _write_run_log(normalized_path, lines, log_lines, summary)
    summary["log_file"] = str(log_file.relative_to(OQL_DIR))

    return {"summary": summary, "results": results}


async def _run_oql_lines(
    lines: list[str], label: str
) -> tuple[list[dict], dict[str, int], list[str]]:
    """Execute lines of OQL, returning (results, counters, log_lines)."""
    log_lines: list[str] = [
        f"# OQL Test Log: {label}",
        f"# Started: {datetime.now().isoformat()}",
        f"# Lines: {len(lines)}",
        "",
    ]
    results: list[dict] = []
    counters = {"passed": 0, "failed": 0, "asserts_pass": 0, "asserts_fail": 0}
    start_time = time.monotonic()

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        line_num = i + 1

        if not line or line.startswith("#"):
            log_lines.append(f"L{line_num:>4}: {raw_line}")
            continue

        t0 = time.monotonic()
        try:
            result = await _execute_oql_line(line)
        except Exception as exc:
            result = {"ok": False, "command": line.split()[0], "error": str(exc)}
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        result["line"] = line_num
        result["elapsed_ms"] = elapsed_ms
        results.append(result)

        _update_counters(counters, result)

        status_mark = "✅" if result.get("ok") else "❌"
        detail = _format_log_detail(result.get("command", "?"), result)
        log_lines.append(f"L{line_num:>4}: {status_mark} [{elapsed_ms:>5}ms] {line}{detail}")

    counters["total_ms"] = round((time.monotonic() - start_time) * 1000)
    return results, counters, log_lines


def _update_counters(counters: dict[str, int], result: dict) -> None:
    """Update passed/failed/assert counters from a single result."""
    if result.get("ok"):
        counters["passed"] += 1
    else:
        counters["failed"] += 1
    if result.get("command") == "ASSERT":
        if result.get("assertion") == "PASS":
            counters["asserts_pass"] += 1
        else:
            counters["asserts_fail"] += 1


def _build_run_summary(
    normalized_path: str,
    requested_path: str,
    lines: list[str],
    results: list[dict],
    counters: dict[str, int],
) -> dict:
    """Build the summary dict for a completed file run."""
    passed = counters["passed"]
    failed = counters["failed"]
    return {
        "file": normalized_path,
        "requested_path": requested_path,
        "total_lines": len(lines),
        "executed": passed + failed,
        "passed": passed,
        "failed": failed,
        "asserts_pass": counters["asserts_pass"],
        "asserts_fail": counters["asserts_fail"],
        "total_ms": counters["total_ms"],
        "status": "PASS" if failed == 0 else "FAIL",
    }


def _write_run_log(
    normalized_path: str,
    lines: list[str],
    log_lines: list[str],
    summary: dict,
) -> "Path":
    """Append summary footer to log_lines and write to disk. Returns log Path."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = Path(normalized_path).stem
    log_file = LOG_DIR / f"{test_name}_{ts}.log"

    log_lines.extend([
        "",
        "# ── Summary ──────────────────────────────────────",
        f"# Status:   {summary['status']}",
        f"# Executed: {summary['executed']} | Passed: {summary['passed']} | Failed: {summary['failed']}",
        f"# Asserts:  {summary['asserts_pass']} pass / {summary['asserts_fail']} fail",
        f"# Time:     {summary['total_ms']}ms",
        f"# Finished: {datetime.now().isoformat()}",
    ])
    log_file.write_text("\n".join(log_lines), encoding="utf-8")
    return log_file


@router.get("/logs")
async def oql_list_logs():
    """List available log files."""
    logs = []
    if LOG_DIR.is_dir():
        for f in sorted(LOG_DIR.glob("*.log"), reverse=True):
            logs.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    return {"logs": logs, "log_dir": str(LOG_DIR)}


@router.get("/log")
async def oql_read_log(name: str = Query(...)):
    """Read a specific log file."""
    target = (LOG_DIR / name).resolve()
    if not str(target).startswith(str(LOG_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)
    content = target.read_text(encoding="utf-8")
    return PlainTextResponse(content)

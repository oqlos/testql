"""REST API routes for IQL file operations (list, read, run, logs)."""

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

router = APIRouter(prefix="/iql", tags=["iql"])

# ── Paths ─────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
IQL_DIR = PROJECT_ROOT / "db" / "dsl" / "iql"
LOG_DIR = IQL_DIR / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_WAIT_MS = 100
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404


# ── IQL command executor ──────────────────────────────────────────

_ENCODER_SIMPLE_CMDS = {
    "ENCODER_ON": "activate",
    "ENCODER_OFF": "deactivate",
    "ENCODER_CLICK": "click",
    "ENCODER_DBLCLICK": "cancel",
    "ENCODER_STATUS": "status",
    "ENCODER_PAGE_NEXT": "pageNext",
    "ENCODER_PAGE_PREV": "pagePrev",
}


def _evaluate_assertion(result: dict, prop: str, expected: str | None) -> tuple[Any, bool]:
    """Evaluate an ASSERT property check. Returns (actual, passed)."""
    if prop in ("exists", "visible"):
        actual = result.get(prop, False)
        passed = bool(actual) if expected is None else (str(actual).lower() == expected.lower())
    elif prop == "count":
        actual = result.get("count", 0)
        passed = (str(actual) == expected) if expected else actual > 0
    elif prop == "text":
        actual = result.get("text", "")
        passed = (expected in actual) if expected else len(actual) > 0
    elif prop == "classes":
        actual = result.get("classes", "")
        passed = (expected in actual) if expected else True
    else:
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
        result = await hub.send_iql_command("navigate", url=url)
        return {"ok": result.get("ok", False), "command": cmd, "url": url, "result": result}
    if cmd == "CLICK":
        if not arg:
            return {"ok": False, "command": cmd, "error": "missing selector"}
        result = await hub.send_iql_command("click", selector=arg)
        return {"ok": result.get("ok", False), "command": cmd, "selector": arg, "result": result}
    if cmd == "QUERY":
        m = re.match(r'"([^"]+)"\s*(.*)', raw_arg) if raw_arg else None
        selector, prop = (m.group(1), m.group(2).strip() or "exists") if m else (arg, "exists")
        result = await hub.send_iql_command("query", selector=selector, prop=prop)
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

    result = await hub.send_iql_command("query", selector=selector, prop=prop)
    if not result.get("ok"):
        return {"ok": False, "command": "ASSERT", "selector": selector, "error": result.get("error", "query_failed"), "result": result}

    actual, passed = _evaluate_assertion(result, prop, expected)
    return {
        "ok": passed, "command": "ASSERT", "selector": selector,
        "prop": prop, "expected": expected, "actual": actual,
        "assertion": "PASS" if passed else "FAIL",
        "result": result,
    }


async def _execute_iql_line(line: str) -> dict[str, Any]:
    """Execute a single IQL command line. Returns structured result dict."""
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
async def iql_list_files():
    """List all .iql files in the project."""
    files = []
    if IQL_DIR.is_dir():
        for f in sorted(IQL_DIR.rglob("*.iql")):
            rel = f.relative_to(IQL_DIR)
            files.append({
                "path": str(rel),
                "name": f.name,
                "dir": str(rel.parent) if str(rel.parent) != "." else "",
                "size": f.stat().st_size,
            })
    return {"files": files, "base_dir": str(IQL_DIR)}


@router.get("/file")
async def iql_read_file(path: str = Query(...)):
    """Read an IQL file content."""
    target = (IQL_DIR / path).resolve()
    if not str(target).startswith(str(IQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)
    content = target.read_text(encoding="utf-8")
    return {"path": path, "content": content, "lines": content.count("\n") + 1}


@router.get("/tables")
async def iql_list_tables(path: str = Query(...)):
    """Extract table names from an IQL file."""
    target = (IQL_DIR / path).resolve()
    if not str(target).startswith(str(IQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)
    
    content = target.read_text(encoding="utf-8")
    tables = []
    
    # Extract table references from IQL commands
    # Pattern for TABLE commands or table references
    table_patterns = [
        r'TABLE\s+["\']?(\w+)["\']?',  # TABLE "tablename"
        r'FROM\s+["\']?(\w+)["\']?',     # FROM tablename
        r'INTO\s+["\']?(\w+)["\']?',     # INTO tablename
        r'JOIN\s+["\']?(\w+)["\']?',     # JOIN tablename
    ]
    
    for pattern in table_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        tables.extend(matches)
    
    # Remove duplicates and sort
    tables = sorted(list(set(tables)))
    
    return {"path": path, "tables": tables}


@router.post("/run-line")
async def iql_run_line(req: RunLineRequest):
    """Execute a single IQL command line via the encoder bridge."""
    return await _execute_iql_line(req.line)


@router.post("/run-file")
async def iql_run_file(req: RunFileRequest):
    """Run an entire IQL file with validation. Returns structured results + saves log."""
    target = (IQL_DIR / req.path).resolve()
    if not str(target).startswith(str(IQL_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found", "path": req.path}, status_code=HTTP_NOT_FOUND)

    content = target.read_text(encoding="utf-8")
    lines = content.splitlines()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = Path(req.path).stem
    log_file = LOG_DIR / f"{test_name}_{ts}.log"

    results: list[dict] = []
    passed = 0
    failed = 0
    asserts_pass = 0
    asserts_fail = 0
    start_time = time.monotonic()

    log_lines: list[str] = [
        f"# IQL Test Log: {req.path}",
        f"# Started: {datetime.now().isoformat()}",
        f"# Lines: {len(lines)}",
        "",
    ]

    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        line_num = i + 1

        if not line or line.startswith("#"):
            log_lines.append(f"L{line_num:>4}: {raw_line}")
            continue

        t0 = time.monotonic()
        try:
            result = await _execute_iql_line(line)
        except Exception as exc:
            result = {"ok": False, "command": line.split()[0], "error": str(exc)}
        elapsed_ms = round((time.monotonic() - t0) * 1000)

        result["line"] = line_num
        result["elapsed_ms"] = elapsed_ms
        results.append(result)

        ok = result.get("ok", False)
        if ok:
            passed += 1
        else:
            failed += 1

        cmd = result.get("command", "?")
        if cmd == "ASSERT":
            if result.get("assertion") == "PASS":
                asserts_pass += 1
            else:
                asserts_fail += 1

        status_mark = "✅" if ok else "❌"
        detail = _format_log_detail(cmd, result)
        log_lines.append(f"L{line_num:>4}: {status_mark} [{elapsed_ms:>5}ms] {line}{detail}")

    total_time = round((time.monotonic() - start_time) * 1000)

    summary = {
        "file": req.path,
        "total_lines": len(lines),
        "executed": passed + failed,
        "passed": passed,
        "failed": failed,
        "asserts_pass": asserts_pass,
        "asserts_fail": asserts_fail,
        "total_ms": total_time,
        "log_file": str(log_file.relative_to(IQL_DIR)),
        "status": "PASS" if failed == 0 else "FAIL",
    }

    log_lines.extend([
        "",
        "# ── Summary ──────────────────────────────────────",
        f"# Status:  {summary['status']}",
        f"# Executed: {summary['executed']} | Passed: {passed} | Failed: {failed}",
        f"# Asserts:  {asserts_pass} pass / {asserts_fail} fail",
        f"# Time:    {total_time}ms",
        f"# Finished: {datetime.now().isoformat()}",
    ])

    log_file.write_text("\n".join(log_lines), encoding="utf-8")

    return {"summary": summary, "results": results}


@router.get("/logs")
async def iql_list_logs():
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
async def iql_read_log(name: str = Query(...)):
    """Read a specific log file."""
    target = (LOG_DIR / name).resolve()
    if not str(target).startswith(str(LOG_DIR)):
        return JSONResponse({"error": "path_traversal"}, status_code=HTTP_BAD_REQUEST)
    if not target.is_file():
        return JSONResponse({"error": "not_found"}, status_code=HTTP_NOT_FOUND)
    content = target.read_text(encoding="utf-8")
    return PlainTextResponse(content)

"""Minimal MCP stdio client for nlp2env-mcp."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _find_mcp_command() -> str:
    forced = os.getenv("NLP2ENV_MCP", "").strip()
    if forced:
        return forced
    for name in ("nlp2env-mcp",):
        found = shutil.which(name)
        if found:
            return found
    root = os.getenv("NLP2ENV_ROOT", "").strip()
    if root:
        for rel in ("venv/bin/nlp2env-mcp", ".venv/bin/nlp2env-mcp"):
            candidate = Path(root).expanduser() / rel
            if candidate.is_file():
                return str(candidate)
    raise FileNotFoundError(
        "nlp2env-mcp not found — pip install nlp2env[mcp] or set NLP2ENV_MCP"
    )


async def _call_tool_async(
    tool: str,
    arguments: dict[str, Any] | None,
    *,
    env_file: str | None,
) -> dict[str, Any]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = os.environ.copy()
    if env_file:
        env["NLP2ENV_ENV_FILE"] = env_file
    params = StdioServerParameters(command=_find_mcp_command(), args=[], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool, arguments or {})
            text = "".join(b.text for b in result.content if hasattr(b, "text"))
            return json.loads(text)


def mcp_call(
    tool: str,
    arguments: dict[str, Any] | None = None,
    *,
    env_file: str | None = None,
) -> dict[str, Any]:
    return asyncio.run(_call_tool_async(tool, arguments, env_file=env_file))


def assert_ok(payload: dict[str, Any], label: str = "") -> dict[str, Any]:
    if not payload.get("success"):
        raise RuntimeError(f"{label} failed: {payload}")
    return payload


def mcp_available() -> bool:
    # The adapter needs both sides of MCP: the stdio server executable and the
    # Python client imported by ``_call_tool_async``.  They may come from
    # different virtual environments, so finding only the executable is not
    # sufficient and previously made the optional E2E test fail at runtime.
    if importlib.util.find_spec("mcp") is None:
        return False
    try:
        result = subprocess.run(
            [_find_mcp_command(), "--help"],
            capture_output=True,
            timeout=5,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return False

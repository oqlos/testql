"""WebSocket mixin for TestQL — WS_CONNECT, WS_SEND, WS_RECEIVE, WS_CLOSE."""

from __future__ import annotations

import asyncio
from typing import Any

from testql.base import StepResult, StepStatus
from ._parser import OqlLine


class WebSocketMixin:
    """Mixin for WebSocket testing support."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_ws_connections"):
            cls._ws_connections: dict[str, Any] = {}
        if not hasattr(cls, "_ws_messages"):
            cls._ws_messages: dict[str, list[str]] = {}

    def _get_ws_context(self):
        if not hasattr(self, "_ws_connections"):
            self._ws_connections = {}
        if not hasattr(self, "_ws_messages"):
            self._ws_messages = {}
        return self._ws_connections, self._ws_messages

    def _cmd_ws_connect(self, args: str, line: OqlLine) -> None:
        """WS_CONNECT url [alias]"""
        parts = args.strip().split()
        if not parts:
            return
        
        url = parts[0].strip("\"'")
        alias = parts[1] if len(parts) > 1 else "default"
        
        connections, _ = self._get_ws_context()
        
        if self.dry_run:
            self.out.step("🔌", f"WS_CONNECT {url} (alias: {alias}) [dry-run]")
            self.results.append(StepResult(name=f"WS_CONNECT {alias}", status=StepStatus.PASSED))
            return

        try:
            import websockets
            async def connect():
                return await websockets.connect(url)
            
            # Using a simple loop run for synchronous call in mixin
            ws = asyncio.run(connect())
            connections[alias] = ws
            self.out.step("🔌", f"Connected to {url} (alias: {alias})")
            self.results.append(StepResult(name=f"WS_CONNECT {alias}", status=StepStatus.PASSED))
        except Exception as e:
            self.out.error(f"WS_CONNECT failed: {e}")
            self.results.append(StepResult(name=f"WS_CONNECT {alias}", status=StepStatus.ERROR, message=str(e)))

    def _cmd_ws_send(self, args: str, line: OqlLine) -> None:
        """WS_SEND alias message"""
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            # Maybe use default alias
            alias = "default"
            msg = parts[0] if parts else ""
        else:
            alias = parts[0]
            msg = parts[1].strip("\"'")

        connections, _ = self._get_ws_context()
        if alias not in connections and not self.dry_run:
            self.out.error(f"WS_SEND: Alias '{alias}' not connected")
            return

        if self.dry_run:
            self.out.step("📤", f"WS_SEND [{alias}]: {msg} [dry-run]")
            self.results.append(StepResult(name=f"WS_SEND {alias}", status=StepStatus.PASSED))
            return

        try:
            ws = connections[alias]
            asyncio.run(ws.send(msg))
            self.out.step("📤", f"Sent: {msg}")
            self.results.append(StepResult(name=f"WS_SEND {alias}", status=StepStatus.PASSED))
        except Exception as e:
            self.out.error(f"WS_SEND failed: {e}")
            self.results.append(StepResult(name=f"WS_SEND {alias}", status=StepStatus.ERROR, message=str(e)))

    def _ws_do_receive(self, ws, alias: str, timeout: float, messages: dict) -> None:
        """Perform the actual async receive and record the result step."""
        async def recv():
            return await asyncio.wait_for(ws.recv(), timeout=timeout)

        msg = asyncio.run(recv())
        messages.setdefault(alias, []).append(msg)
        self.out.step("📥", f"Received: {msg[:60]}...")
        self.results.append(StepResult(
            name=f"WS_RECEIVE {alias}", status=StepStatus.PASSED, value=msg
        ))

    def _cmd_ws_receive(self, args: str, line: OqlLine) -> None:
        """WS_RECEIVE alias [timeout_ms]"""
        parts = args.strip().split()
        alias = parts[0] if parts else "default"
        timeout = int(parts[1]) / 1000 if len(parts) > 1 else 5.0

        connections, messages = self._get_ws_context()
        if alias not in connections and not self.dry_run:
            self.out.error(f"WS_RECEIVE: Alias '{alias}' not connected")
            return

        if self.dry_run:
            self.out.step("📥", f"WS_RECEIVE [{alias}] [dry-run]")
            self.results.append(StepResult(name=f"WS_RECEIVE {alias}", status=StepStatus.PASSED))
            return

        try:
            self._ws_do_receive(connections[alias], alias, timeout, messages)
        except asyncio.TimeoutError:
            self.out.error(f"WS_RECEIVE timeout ({timeout}s)")
            self.results.append(StepResult(name=f"WS_RECEIVE {alias}", status=StepStatus.FAILED, message="Timeout"))
        except Exception as e:
            self.out.error(f"WS_RECEIVE failed: {e}")
            self.results.append(StepResult(name=f"WS_RECEIVE {alias}", status=StepStatus.ERROR, message=str(e)))

    def _cmd_ws_assert_msg(self, args: str, line: OqlLine) -> None:
        """WS_ASSERT_MSG alias expected_pattern"""
        parts = args.strip().split(None, 1)
        if len(parts) < 2:
            return
        alias = parts[0]
        expected = parts[1].strip("\"'")

        _, messages = self._get_ws_context()
        msgs = messages.get(alias, [])
        
        last_msg = msgs[-1] if msgs else None
        
        if self.dry_run:
            self.out.step("⚖️", f"ASSERT WS [{alias}] contains '{expected}' [dry-run]")
            return

        if not last_msg:
             self.out.fail(f"No messages received for alias '{alias}'")
             self.results.append(StepResult(name=f"ASSERT WS {alias}", status=StepStatus.FAILED))
             return

        if expected in last_msg:
            self.out.ok(f"WS message matches: {expected}")
            self.results.append(StepResult(name=f"ASSERT WS {alias}", status=StepStatus.PASSED))
        else:
            self.out.fail(f"WS message MISMATCH. Expected '{expected}', got '{last_msg[:60]}'")
            self.results.append(StepResult(name=f"ASSERT WS {alias}", status=StepStatus.FAILED))

    def _cmd_ws_close(self, args: str, line: OqlLine) -> None:
        """WS_CLOSE [alias]"""
        alias = args.strip() or "default"
        connections, _ = self._get_ws_context()
        
        if alias not in connections and not self.dry_run:
            return

        if self.dry_run:
            self.out.step("🔌", f"WS_CLOSE [{alias}] [dry-run]")
            return

        try:
            ws = connections.pop(alias)
            asyncio.run(ws.close())
            self.out.step("🔌", f"Closed WS alias '{alias}'")
        except Exception as e:
            self.out.warn(f"WS_CLOSE error: {e}")

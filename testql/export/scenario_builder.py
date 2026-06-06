"""Compose TestTOON scenarios from structured sections."""

from __future__ import annotations

from typing import Any


def _csv(value: Any) -> str:
    text = str(value if value is not None else "-").strip()
    return text.replace(",", ";") or "-"


class ScenarioBuilder:
    """Fluent builder for *.testql.toon.yaml text."""

    def __init__(
        self,
        *,
        name: str,
        scenario_type: str = "e2e",
        version: str = "1.0",
        meta: dict[str, str] | None = None,
    ) -> None:
        self._lines: list[str] = [
            f"# SCENARIO: {name}",
            f"# TYPE: {scenario_type}",
            f"# VERSION: {version}",
        ]
        if meta:
            for key, value in meta.items():
                self._lines.append(f"# {key.upper()}: {value}")

    def environment(self, rows: dict[str, Any]) -> ScenarioBuilder:
        items = [(k, _csv(v)) for k, v in rows.items()]
        self._lines.append("")
        self._lines.append(f"ENVIRONMENT[{len(items)}]{{key, value}}:")
        for key, value in items:
            self._lines.append(f"  {key},  {value}")
        return self

    def config(self, rows: dict[str, Any]) -> ScenarioBuilder:
        items = [(k, _csv(v)) for k, v in rows.items()]
        self._lines.append("")
        self._lines.append(f"CONFIG[{len(items)}]{{key, value}}:")
        for key, value in items:
            self._lines.append(f"  {key},  {value}")
        return self

    def context(self, rows: dict[str, Any]) -> ScenarioBuilder:
        items = [(k, _csv(v)) for k, v in rows.items()]
        self._lines.append("")
        self._lines.append(f"CONTEXT[{len(items)}]{{key, value}}:")
        for key, value in items:
            self._lines.append(f"  {key},  {value}")
        return self

    def commands(self, commands: list[str]) -> ScenarioBuilder:
        self._lines.append("")
        self._lines.append(f"COMMANDS[{len(commands)}]{{command}}:")
        for cmd in commands:
            self._lines.append(f"  {cmd}")
        return self

    def gui(self, rows: list[dict[str, Any]]) -> ScenarioBuilder:
        self._lines.append("")
        self._lines.append(f"GUI[{len(rows)}]{{action, selector, value, wait_ms}}:")
        for row in rows:
            action = _csv(row.get("action", ""))
            selector = _csv(row.get("selector") or row.get("target") or "-")
            value = _csv(row.get("value") or row.get("text") or "-")
            wait_ms = _csv(row.get("wait_ms") or "-")
            self._lines.append(f"  {action},  {selector},  {value},  {wait_ms}")
        return self

    def flow(self, rows: list[dict[str, Any]]) -> ScenarioBuilder:
        self._lines.append("")
        self._lines.append(f"FLOW[{len(rows)}]{{command, target, value}}:")
        for row in rows:
            command = _csv(row.get("command") or row.get("action") or "LOG")
            target = _csv(row.get("target") or row.get("selector") or "-")
            value = _csv(row.get("value") or row.get("text") or "-")
            self._lines.append(f"  {command},  {target},  {value}")
        return self

    def shell(self, commands: list[str], *, exit_code: int | None = None) -> ScenarioBuilder:
        self._lines.append("")
        if exit_code is not None:
            self._lines.append(f"SHELL[{len(commands)}]{{command, exit_code}}:")
            for cmd in commands:
                self._lines.append(f"  {_csv(cmd)},  {exit_code}")
        else:
            self._lines.append(f"SHELL[{len(commands)}]{{command}}:")
            for cmd in commands:
                self._lines.append(f"  {_csv(cmd)}")
        return self

    def wait(self, ms: int) -> ScenarioBuilder:
        self._lines.append("")
        self._lines.append("WAIT[1]{ms}:")
        self._lines.append(f"  {ms}")
        return self

    def build(self) -> str:
        return "\n".join(self._lines).rstrip() + "\n"

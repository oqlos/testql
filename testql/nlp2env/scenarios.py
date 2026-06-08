"""Load nlp2env PROMPTS / ASSERT_ENV sections from TestTOON text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADER_RE = re.compile(r"^([A-Z_]+)(?:\[(\d+)\])?\{([^}]*)\}:\s*$")
_META_RE = re.compile(r"^#\s*([A-Z_]+):\s*(.+)$")
_NLP2ENV_SECTIONS = frozenset({"PROMPTS", "PROMPT_FIELDS", "ASSERT_ENV", "CONFIG"})


@dataclass
class PromptScenario:
    prompt_id: str
    fields: dict[str, str] = field(default_factory=dict)
    expects: list[str] = field(default_factory=list)

    @property
    def nl(self) -> str:
        return self.fields.get("nl", "")

    @property
    def source(self) -> str:
        return self.fields.get("source", "inline").lower()

    @property
    def tool(self) -> str:
        return self.fields.get("tool", "")

    @property
    def after(self) -> str:
        return self.fields.get("after", "")

    @property
    def assert_configured(self) -> bool:
        return self.fields.get("assert_configured", "").lower() in {"1", "true", "yes"}

    def inline_arguments(self) -> dict[str, str]:
        skip = {"nl", "source", "tool", "after", "assert_configured", "lang", "id"}
        return {k: v for k, v in self.fields.items() if k not in skip and v}


def _strip_quoted(line: str) -> str:
    out: list[str] = []
    in_quote: str | None = None
    prev = ""
    for ch in line:
        if in_quote:
            if ch == in_quote and prev != "\\":
                in_quote = None
            prev = ch
            continue
        if ch in ('"', "'"):
            in_quote = ch
            prev = ch
            continue
        out.append(ch)
        prev = ch
    return "".join(out)


def _detect_sep(line: str) -> str:
    return "|" if "|" in _strip_quoted(line) else ","


def _split_row(line: str, sep: str, maxsplit: int = -1) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    in_quote: str | None = None
    prev = ""
    splits = 0
    for ch in line:
        if in_quote:
            buf.append(ch)
            if ch == in_quote and prev != "\\":
                in_quote = None
            prev = ch
            continue
        if ch in ('"', "'"):
            in_quote = ch
            buf.append(ch)
            prev = ch
            continue
        if ch == sep and (maxsplit < 0 or splits < maxsplit):
            parts.append("".join(buf))
            buf = []
            splits += 1
            prev = ch
            continue
        buf.append(ch)
        prev = ch
    parts.append("".join(buf))
    return parts


def _parse_value(raw: str) -> str:
    val = raw.strip()
    if val == "-":
        return ""
    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
        return val[1:-1].replace('\\"', '"').replace("\\'", "'")
    return val


def _parse_nlp2env_toon(text: str) -> dict[str, object]:
    """Lenient parser for nlp2env tabular sections (rows may be unindented)."""
    meta: dict[str, str] = {}
    sections: dict[str, dict[str, object]] = {}
    current_name: str | None = None
    current_cols: list[str] = []

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        meta_match = _META_RE.match(stripped)
        if meta_match:
            meta[meta_match.group(1).lower()] = meta_match.group(2).strip()
            continue
        if stripped.startswith("#"):
            continue
        header = _HEADER_RE.match(stripped)
        if header:
            current_name = header.group(1)
            current_cols = [c.strip() for c in header.group(3).split(",") if c.strip()]
            sections[current_name] = {"columns": current_cols, "rows": []}
            continue
        if current_name is None or current_name not in _NLP2ENV_SECTIONS:
            continue
        line = stripped
        sep = _detect_sep(line)
        cells = [_parse_value(c) for c in _split_row(line, sep, len(current_cols) - 1)]
        while len(cells) < len(current_cols):
            cells.append("")
        rows = sections[current_name]["rows"]
        assert isinstance(rows, list)
        rows.append(dict(zip(current_cols, cells[: len(current_cols)])))

    return {"meta": meta, "sections": sections}


def scenarios_from_parsed(parsed: dict[str, object]) -> list[PromptScenario]:
    sections = parsed.get("sections", {})
    assert isinstance(sections, dict)
    prompts = sections.get("PROMPTS")
    if not prompts:
        raise ValueError("Brak sekcji PROMPTS w pliku TestTOON")

    prompt_rows = prompts.get("rows", [])
    prompt_cols = prompts.get("columns", [])
    assert isinstance(prompt_rows, list)
    assert isinstance(prompt_cols, list)

    fields_section = sections.get("PROMPT_FIELDS")
    assert_section = sections.get("ASSERT_ENV")

    extra_fields: dict[str, dict[str, str]] = {}
    if isinstance(fields_section, dict):
        for row in fields_section.get("rows", []):
            if not isinstance(row, dict):
                continue
            pid = str(row.get("prompt_id", "")).strip()
            key = str(row.get("key", "")).strip()
            val = str(row.get("value", "")).strip()
            if pid and key:
                extra_fields.setdefault(pid, {})[key] = val

    expects: dict[str, list[str]] = {}
    if isinstance(assert_section, dict):
        for row in assert_section.get("rows", []):
            if not isinstance(row, dict):
                continue
            pid = str(row.get("prompt_id", "")).strip()
            expect = str(row.get("expect", "")).strip()
            if pid and expect:
                expects.setdefault(pid, []).append(expect)

    id_col = "id" if "id" in prompt_cols else (prompt_cols[0] if prompt_cols else "id")
    scenarios: list[PromptScenario] = []
    for row in prompt_rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get(id_col, "")).strip()
        if not pid:
            continue
        fields = {k: str(v).strip() for k, v in row.items() if k != id_col and v not in (None, "-", "")}
        fields.update(extra_fields.get(pid, {}))
        scenarios.append(PromptScenario(prompt_id=pid, fields=fields, expects=expects.get(pid, [])))
    return scenarios


def load_scenarios(text: str, *, source_name: str = "") -> list[PromptScenario]:
    _ = source_name
    return scenarios_from_parsed(_parse_nlp2env_toon(text))


def load_scenarios_file(path: Path | str) -> list[PromptScenario]:
    p = Path(path)
    return load_scenarios(p.read_text(encoding="utf-8"), source_name=p.name)


def scenario_count(text: str, *, source_name: str = "") -> int:
    try:
        return len(load_scenarios(text, source_name=source_name))
    except ValueError:
        return 0

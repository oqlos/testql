"""Lightweight `.proto` schema loader.

The official `protobuf` package does **not** ship a `.proto` parser — that
lives in the `protoc` compiler. Phase 3 ships a deliberately small regex-based
parser that handles the common surface (proto3 messages with scalar / repeated
fields). When `protoc` is available, callers can opt into a richer
`FileDescriptorSet`-backed flow in a later phase.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


SCALAR_TYPES: tuple[str, ...] = (
    "double", "float",
    "int32", "int64", "uint32", "uint64", "sint32", "sint64",
    "fixed32", "fixed64", "sfixed32", "sfixed64",
    "bool", "string", "bytes",
)


@dataclass
class FieldDef:
    name: str
    type: str
    number: int
    label: str = "optional"  # optional | required | repeated (proto3 implies optional)
    default: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name, "type": self.type, "number": self.number,
            "label": self.label, "default": self.default,
        }


@dataclass
class MessageDef:
    name: str
    fields: list[FieldDef] = field(default_factory=list)

    def field_by_name(self, name: str) -> Optional[FieldDef]:
        for f in self.fields:
            if f.name == name:
                return f
        return None

    def field_by_number(self, number: int) -> Optional[FieldDef]:
        for f in self.fields:
            if f.number == number:
                return f
        return None

    def to_dict(self) -> dict:
        return {"name": self.name, "fields": [f.to_dict() for f in self.fields]}


@dataclass
class ProtoFile:
    syntax: str = "proto3"
    package: str = ""
    messages: list[MessageDef] = field(default_factory=list)

    def message(self, name: str) -> Optional[MessageDef]:
        for m in self.messages:
            if m.name == name:
                return m
        return None

    def to_dict(self) -> dict:
        return {
            "syntax": self.syntax, "package": self.package,
            "messages": [m.to_dict() for m in self.messages],
        }


# ── Regex-based parser ──────────────────────────────────────────────────────

_SYNTAX_RE = re.compile(r'syntax\s*=\s*"(?P<v>[^"]+)"\s*;', re.IGNORECASE)
_PACKAGE_RE = re.compile(r"package\s+(?P<p>[A-Za-z_][\w.]*)\s*;")
_MESSAGE_HEAD_RE = re.compile(r"message\s+(?P<name>[A-Za-z_][\w]*)\s*\{")
_FIELD_RE = re.compile(
    r"(?:(?P<label>optional|required|repeated)\s+)?"
    r"(?P<type>[A-Za-z_][\w.]*)\s+"
    r"(?P<name>[A-Za-z_][\w]*)\s*=\s*"
    r"(?P<number>\d+)\s*"
    r"(?:\[\s*default\s*=\s*(?P<default>[^\]]+?)\s*\])?\s*;"
)


def _strip_comments(text: str) -> str:
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return text


def _scan_balanced_braces(text: str, start: int) -> Optional[str]:
    depth = 1
    i = start
    while i < len(text):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
        i += 1
    return None


def _parse_field(match: "re.Match[str]") -> FieldDef:
    label = match.group("label") or "optional"
    return FieldDef(
        name=match.group("name"),
        type=match.group("type"),
        number=int(match.group("number")),
        label=label,
        default=(match.group("default").strip() if match.group("default") else None),
    )


def _parse_message(name: str, body: str) -> MessageDef:
    fields = [_parse_field(m) for m in _FIELD_RE.finditer(body)]
    return MessageDef(name=name, fields=fields)


def _iter_messages(text: str):
    for m in _MESSAGE_HEAD_RE.finditer(text):
        body = _scan_balanced_braces(text, m.end())
        if body is not None:
            yield m.group("name"), body


def parse_proto(text: str) -> ProtoFile:
    """Parse a `.proto` source string into a `ProtoFile`."""
    cleaned = _strip_comments(text)
    syntax_m = _SYNTAX_RE.search(cleaned)
    package_m = _PACKAGE_RE.search(cleaned)
    pf = ProtoFile(
        syntax=syntax_m.group("v") if syntax_m else "proto3",
        package=package_m.group("p") if package_m else "",
    )
    for name, body in _iter_messages(cleaned):
        pf.messages.append(_parse_message(name, body))
    return pf


def load_proto_file(path: str | Path) -> ProtoFile:
    p = Path(path)
    return parse_proto(p.read_text(encoding="utf-8"))


__all__ = [
    "SCALAR_TYPES",
    "FieldDef", "MessageDef", "ProtoFile",
    "parse_proto", "load_proto_file",
]

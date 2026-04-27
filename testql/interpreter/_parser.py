"""OQL parser — tokenises source into OqlLine / OqlScript AST."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OqlLine:
    number: int
    command: str
    args: str
    raw: str


@dataclass
class OqlScript:
    filename: str = ""
    lines: list[OqlLine] = field(default_factory=list)


def parse_oql(source: str, filename: str = "<string>") -> OqlScript:
    """Parse OQL source into a flat command list, stripping comments."""
    script = OqlScript(filename=filename)
    for i, raw in enumerate(source.split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        script.lines.append(OqlLine(number=i, command=cmd, args=args, raw=line))
    return script

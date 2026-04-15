"""IQL parser — tokenises source into IqlLine / IqlScript AST."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class IqlLine:
    number: int
    command: str
    args: str
    raw: str


@dataclass
class IqlScript:
    filename: str = ""
    lines: list[IqlLine] = field(default_factory=list)


def parse_iql(source: str, filename: str = "<string>") -> IqlScript:
    """Parse IQL source into a flat command list, stripping comments."""
    script = IqlScript(filename=filename)
    for i, raw in enumerate(source.split("\n"), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        cmd = parts[0].upper()
        args = parts[1] if len(parts) > 1 else ""
        script.lines.append(IqlLine(number=i, command=cmd, args=args, raw=line))
    return script

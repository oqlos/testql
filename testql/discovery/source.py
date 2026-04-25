from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SourceKind(Enum):
    PATH = "path"
    URL = "url"
    DESCRIPTOR = "descriptor"


@dataclass(frozen=True)
class ArtifactSource:
    location: str
    kind: SourceKind = SourceKind.PATH

    @classmethod
    def from_value(cls, value: str | Path) -> "ArtifactSource":
        text = str(value)
        if text.startswith(("http://", "https://")):
            return cls(text, SourceKind.URL)
        if ":" in text and not Path(text).exists():
            return cls(text, SourceKind.DESCRIPTOR)
        return cls(text, SourceKind.PATH)

    @property
    def path(self) -> Path:
        return Path(self.location)

    def to_dict(self) -> dict:
        return {"kind": self.kind.value, "location": self.location}

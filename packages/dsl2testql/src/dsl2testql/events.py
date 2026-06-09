"""EventStore — protobuf + jsonl."""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from dsl2testql.pb_codec import encode_protobuf, envelope_to_dict, result_to_pb
from dsl2testql.result import DslResult
from dsl2testql.v1 import result_pb2

StoreFormat = Literal["protobuf", "jsonl"]


@dataclass
class DslEvent:
    id: str
    ts_unix: int
    command: dict[str, Any]
    result: dict[str, Any]
    correlation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EventStore:
    def __init__(self, path: Path | str, *, fmt: StoreFormat | None = None) -> None:
        self.path = Path(path)
        if fmt is not None:
            self.fmt = fmt
        elif self.path.suffix == ".pb":
            self.fmt = "protobuf"
        else:
            self.fmt = "jsonl"

    def append(self, command: dict[str, Any], result: dict[str, Any], *, correlation_id: str = "") -> DslEvent:
        event = DslEvent(id=str(uuid.uuid4()), ts_unix=int(time.time()), command=command, result=result, correlation_id=correlation_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.fmt == "protobuf":
            pb = result_pb2.DslEvent()
            pb.id = event.id
            pb.ts_unix = event.ts_unix
            pb.correlation_id = correlation_id
            pb.command.ParseFromString(encode_protobuf(command, correlation_id=correlation_id))
            dsl_result = DslResult(
                ok=bool(result.get("ok")),
                command=str(result.get("command", "")),
                action=str(result.get("action", "")),
                output=str(result.get("output", "")),
                data=dict(result.get("data") or {}),
                error=result.get("error"),
                event_id=event.id,
            )
            pb.result.CopyFrom(result_to_pb(dsl_result))
            data = pb.SerializeToString()
            with self.path.open("ab") as fh:
                fh.write(len(data).to_bytes(4, "big"))
                fh.write(data)
        else:
            row = event.to_dict()
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return event

    def replay(self) -> list[DslEvent]:
        if not self.path.is_file():
            return []
        if self.fmt == "protobuf":
            events: list[DslEvent] = []
            data = self.path.read_bytes()
            offset = 0
            while offset + 4 <= len(data):
                size = int.from_bytes(data[offset : offset + 4], "big")
                offset += 4
                chunk = data[offset : offset + size]
                offset += size
                pb = result_pb2.DslEvent()
                pb.ParseFromString(chunk)
                events.append(
                    DslEvent(
                        id=pb.id,
                        ts_unix=int(pb.ts_unix),
                        command=envelope_to_dict(pb.command),
                        result={"ok": pb.result.ok, "command": pb.result.command, "action": pb.result.action, "output": pb.result.output, "error": pb.result.error or None},
                        correlation_id=pb.correlation_id,
                    )
                )
            return events
        return [DslEvent(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]


def default_event_store(manifest_file: str = "app.testql.less", *, prefer_pb: bool = True) -> EventStore:
    stem = Path(manifest_file).name.replace("app.", "").replace(".less", "")
    if prefer_pb:
        return EventStore(Path(f"app.{stem}.events.pb"), fmt="protobuf")
    return EventStore(Path(f"app.{stem}.events.jsonl"), fmt="jsonl")

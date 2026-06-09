"""Text DSL codec + protobuf helpers."""

from __future__ import annotations

from dsl2testql.grammar import parse_line, to_text
from dsl2testql.schema_registry import validate_command_dict


def encode_text(line: str) -> tuple[dict, list[str]]:
    cmd = parse_line(line)
    if cmd is None:
        return {}, ["empty command"]
    return cmd, validate_command_dict(cmd)


def roundtrip_text(line: str) -> str:
    cmd = parse_line(line)
    if cmd is None:
        raise ValueError("empty command")
    errors = validate_command_dict(cmd)
    if errors:
        raise ValueError("; ".join(errors))
    return to_text(cmd)


def encode_protobuf(line: str, *, default_file: str = "", correlation_id: str = "") -> bytes:
    from dsl2testql.pb_codec import encode_text_to_protobuf

    return encode_text_to_protobuf(line, default_file=default_file, correlation_id=correlation_id)


def decode_protobuf(data: bytes) -> str:
    from dsl2testql.pb_codec import decode_protobuf_to_text

    return decode_protobuf_to_text(data)

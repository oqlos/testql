"""Test listing utilities for suite command."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import click
import yaml

if TYPE_CHECKING:
    pass


def _parse_testtoon_header(content: str) -> dict | None:
    """Parse # SCENARIO: / # TYPE: header comments."""
    if not (content.startswith("# SCENARIO:") or "# TYPE:" in content[:200]):
        return None

    meta: dict = {"name": "", "type": "unknown", "tags": []}
    for line in content.splitlines()[:10]:
        if line.startswith("# SCENARIO:"):
            meta["name"] = line[len("# SCENARIO:"):].strip()
        elif line.startswith("# TYPE:"):
            meta["type"] = line[len("# TYPE:"):].strip()
    return meta


def _parse_yaml_meta_block(content: str, yaml_module) -> dict | None:
    """Extract and parse YAML meta: block from content."""
    if "meta:" not in content:
        return None

    meta_lines: list[str] = []
    in_meta = False

    for line in content.split("\n"):
        if line.strip() == "meta:":
            in_meta = True
            continue
        if in_meta:
            if line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                break
            meta_lines.append(line)

    if not meta_lines:
        return None

    parsed = yaml_module.safe_load("meta:\n" + "\n".join(meta_lines))
    return parsed.get("meta") if parsed and "meta" in parsed else None


def parse_meta(tf: Path, yaml_module) -> dict:
    """Parse test file metadata."""
    meta: dict = {"name": tf.stem, "type": "unknown", "tags": []}

    try:
        content = tf.read_text()
        header = _parse_testtoon_header(content)
        if header is not None:
            meta.update({k: v for k, v in header.items() if v})
            return meta

        yaml_meta = _parse_yaml_meta_block(content, yaml_module)
        if yaml_meta:
            meta.update(yaml_meta)
    except Exception:
        pass

    return meta


def filter_tests(
    raw_files: list[Path],
    target_path: Path,
    test_type: str,
    tag: str | None,
    yaml_module,
) -> list[dict]:
    """Parse meta and apply type/tag filters."""
    tests = []
    for tf in raw_files:
        meta = parse_meta(tf, yaml_module)
        if test_type != "all" and meta.get("type") != test_type:
            continue
        if tag and tag not in meta.get("tags", []):
            continue

        tests.append({
            "file": str(tf.relative_to(target_path)),
            "name": meta.get("name", tf.stem),
            "type": meta.get("type", "unknown"),
            "tags": meta.get("tags", []),
        })
    return tests


def render_test_list(tests: list[dict], fmt: str) -> None:
    """Render test list in requested format."""
    if fmt == "json":
        print(json.dumps(tests, indent=2))
    elif fmt == "simple":
        for t in tests:
            click.echo(t["file"])
    else:
        click.echo(f"{'File':<55} {'Type':<14} {'Tags'}")
        click.echo("-" * 80)
        for t in tests:
            tags_str = ", ".join(t["tags"]) if t["tags"] else "-"
            click.echo(f"{t['file']:<55} {t['type']:<14} {tags_str}")
        click.echo(f"\n{len(tests)} test file(s) found.")

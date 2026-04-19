"""Helper functions for the echo command."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from testql.echo_schemas import ProjectEcho


def _collect_toon_directory(toon_file_path: Path, project_echo: "ProjectEcho") -> None:
    """Collect API contract data from all toon files in *toon_file_path* directory."""
    from testql.toon_parser import parse_toon_file

    toon_files = [
        Path(root) / f
        for root, _dirs, files in os.walk(toon_file_path)
        for f in files
        if f.endswith(".testql.toon.yaml") or f.endswith(".testtoon")
    ]
    for tf in toon_files:
        contract = parse_toon_file(tf)
        project_echo.api_contract.endpoints.extend(contract.endpoints)
        project_echo.api_contract.asserts.extend(contract.asserts)
        if contract.base_url and not project_echo.api_contract.base_url:
            project_echo.api_contract.base_url = contract.base_url
    click.echo(f"📄 Parsed {len(toon_files)} toon file(s)")


def collect_toon_data(toon_path: str, project_echo: "ProjectEcho") -> None:
    """Collect data from toon test files."""
    from testql.toon_parser import parse_toon_file

    toon_file_path = Path(toon_path)
    if toon_file_path.is_dir():
        _collect_toon_directory(toon_file_path, project_echo)
    elif toon_file_path.exists():
        project_echo.api_contract = parse_toon_file(toon_file_path)
        click.echo(f"📄 Parsed toon file: {toon_file_path}")
    else:
        click.echo(f"⚠️  Toon path not found: {toon_path}")


def collect_doql_data(doql_path: str, project_echo: "ProjectEcho") -> None:
    """Collect data from doql LESS file."""
    from testql.doql_parser import parse_doql_file

    doql_file_path = Path(doql_path)
    if doql_file_path.exists():
        project_echo.system_model = parse_doql_file(doql_file_path)
        click.echo(f"📄 Parsed doql file: {doql_file_path}")
    else:
        click.echo(f"⚠️  Doql path not found: {doql_path}")


def render_echo(project_echo: "ProjectEcho", fmt: str, project_path_obj: Path) -> str:
    """Render project echo in specified format."""
    if fmt == "json":
        return json.dumps(project_echo.to_dict(), indent=2)
    if fmt == "sumd":
        from testql.sumd_generator import generate_sumd
        return generate_sumd(project_echo, project_path_obj)
    return project_echo.to_text()

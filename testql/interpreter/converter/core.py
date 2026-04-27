"""Core conversion logic for OQL/TQL to TestTOON."""

from __future__ import annotations

from pathlib import Path

from .dispatcher import dispatch
from .models import Section
from .parsers import parse_commands, detect_scenario_type, extract_scenario_name
from .renderer import build_config_section, render_sections, build_header, SKIP_COMMANDS


def convert_oql_to_testtoon(source: str, filename: str = "<string>") -> str:
    """Convert OQL/TQL source text to TestTOON format."""
    # Phase 1: tokenise
    commands, comments = parse_commands(source)

    # Phase 2: detect metadata
    scenario_name = extract_scenario_name(comments, filename)
    scenario_type = detect_scenario_type(commands)

    # Phase 3: group into sections
    sections: list[Section] = []
    config = build_config_section(commands)
    if config:
        sections.append(config)

    filtered = [(c, a) for c, a in commands if c not in SKIP_COMMANDS]
    i = 0
    while i < len(filtered):
        i, section = dispatch(filtered, i)
        sections.append(section)

    # Phase 4: render
    header = build_header(scenario_name, scenario_type)
    return header + render_sections(sections)


def convert_file(src: Path) -> Path:
    """Convert a single .tql/.oql file to .testql.toon.yaml."""
    source = src.read_text(encoding='utf-8')
    stem = src.stem
    dest = src.parent / f'{stem}.testql.toon.yaml'
    result = convert_oql_to_testtoon(source, src.name)
    dest.write_text(result, encoding='utf-8')
    return dest


def convert_directory(dir_path: Path) -> list[Path]:
    """Recursively convert all .tql and .oql files in a directory."""
    converted = []
    for pattern in ('**/*.tql', '**/*.oql'):
        for f in sorted(dir_path.rglob(pattern.split('/')[-1])):
            if f.suffix in ('.tql', '.oql'):
                dest = convert_file(f)
                converted.append(dest)
                print(f'  {f.relative_to(dir_path)} → {dest.name}')
    return converted

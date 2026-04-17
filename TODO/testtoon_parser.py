"""
TestTOON Parser — tabelaryczny format testów inspirowany TOON
Użycie: python testtoon_parser.py pss7000-flow.testtoon
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Optional

HEADER_RE = re.compile(r'^([A-Z_]+)(?:\[(\d+)\])?\{([^}]*)\}:\s*$')
META_RE   = re.compile(r'^#\s*([A-Z_]+):\s*(.+)$')


@dataclass
class Section:
    type: str
    columns: list
    rows: list = field(default_factory=list)
    expected_count: Optional[int] = None

    def to_dicts(self) -> list:
        return self.rows

    def validate(self) -> list:
        errors = []
        if self.expected_count is not None and len(self.rows) != self.expected_count:
            errors.append(
                f"  {self.type}[{self.expected_count}]: "
                f"zadeklarowano {self.expected_count}, znaleziono {len(self.rows)}"
            )
        return errors


def detect_separator(line: str) -> str:
    """Użyj | jeśli wiersz zawiera |, inaczej ,"""
    return '|' if '|' in line else ','


def parse_value(v: str):
    """Parsuj wartości: -, liczby, {json}, tablice [1,2], stringi"""
    v = v.strip()
    if v == '-':
        return None
    if v.startswith('[') and v.endswith(']'):
        inner = v[1:-1]
        return [parse_value(x) for x in inner.split(',')]
    if v.startswith('{') and v.endswith('}'):
        result = {}
        for pair in v[1:-1].split(','):
            if ':' in pair:
                k, val = pair.split(':', 1)
                result[k.strip()] = parse_value(val)
        return result
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v.strip('"')


def parse_testtoon(text: str) -> dict:
    meta, sections, current = {}, [], None

    for raw in text.splitlines():
        # Pusta linia
        if not raw.strip():
            continue

        # Metadane nagłówka
        m = META_RE.match(raw.strip())
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
            continue

        # Komentarz
        if raw.strip().startswith('#'):
            continue

        # Nagłówek sekcji: NAVIGATE[3]{path, wait_ms}:
        m = HEADER_RE.match(raw.strip())
        if m:
            cols = [c.strip() for c in m.group(3).split(',') if c.strip()]
            current = Section(
                type=m.group(1),
                columns=cols,
                expected_count=int(m.group(2)) if m.group(2) else None
            )
            sections.append(current)
            continue

        # Wiersz danych (musi mieć wcięcie)
        if current and raw.startswith('  '):
            line = raw.strip()
            sep = detect_separator(line)
            parts = line.split(sep, len(current.columns) - 1)
            row = {
                col: parse_value(val)
                for col, val in zip(current.columns, parts)
                if val.strip() != '-' or True  # zachowaj None dla -
            }
            current.rows.append(row)

    return {'meta': meta, 'sections': sections}


def validate(parsed: dict) -> list:
    errors = []
    for s in parsed['sections']:
        errors.extend(s.validate())
    return errors


def print_parsed(parsed: dict):
    print(f"SCENARIO: {parsed['meta'].get('scenario', '?')}")
    print(f"TYPE:     {parsed['meta'].get('type', '?')}")
    print()
    for s in parsed['sections']:
        count = f"[{s.expected_count}]" if s.expected_count else ""
        print(f"{s.type}{count}  columns={s.columns}:")
        for row in s.rows:
            clean = {k: v for k, v in row.items() if v is not None}
            print(f"  {clean}")
    errors = validate(parsed)
    if errors:
        print("\nWALIDATION ERRORS:")
        for e in errors:
            print(e)
    else:
        print("\n✓ Validation passed")


if __name__ == "__main__":
    file = sys.argv[1] if len(sys.argv) > 1 else "pss7000-full-flow.testtoon"
    text = open(file).read()
    result = parse_testtoon(text)
    print_parsed(result)

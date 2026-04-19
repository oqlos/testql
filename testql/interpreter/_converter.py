#!/usr/bin/env python3
"""
Convert IQL/TQL scripts to TestTOON format (*.testql.toon.yaml).

This is a backward-compatible re-export. New code should use:
    from testql.interpreter.converter import convert_iql_to_testtoon

Usage:
    python -m testql.interpreter._converter path/to/file.tql
    python -m testql.interpreter._converter --batch testql/scenarios/
"""

from __future__ import annotations

import sys
from pathlib import Path

# Re-export from new structured package
from .converter import (
    convert_iql_to_testtoon,
    convert_file,
    convert_directory,
    Row,
    Section,
)

__all__ = [
    "convert_iql_to_testtoon",
    "convert_file",
    "convert_directory",
    "Row",
    "Section",
]


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Convert IQL/TQL to TestTOON format')
    parser.add_argument('path', help='File or directory to convert')
    parser.add_argument('--batch', action='store_true', help='Recursively convert directory')
    parser.add_argument('--delete-originals', action='store_true', help='Delete .tql/.iql after conversion')
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_file():
        dest = convert_file(target)
        print(f'Converted: {target} → {dest}')
    elif target.is_dir() or args.batch:
        print(f'Converting directory: {target}')
        converted = convert_directory(target)
        print(f'\nConverted {len(converted)} files')
        if args.delete_originals:
            count = 0
            for f in target.rglob('*'):
                if f.suffix in ('.tql', '.iql'):
                    f.unlink()
                    count += 1
            print(f'Deleted {count} original files')
    else:
        print(f'Error: {target} is not a file or directory', file=sys.stderr)
        sys.exit(1)

"""Lexicon loaders for the natural-language adapter.

Each language's intent vocabulary lives in a sibling YAML file (`pl.yaml`,
`en.yaml`, ...). `load_lexicon(lang)` returns the parsed dict; `available()`
lists supported language codes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_LEXICON_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def load_lexicon(lang: str) -> dict:
    """Return the lexicon dict for `lang` (e.g. "pl", "en").

    Raises:
        FileNotFoundError: when no lexicon for `lang` is bundled.
    """
    path = _LEXICON_DIR / f"{lang}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no NL lexicon for language {lang!r} (looked in {path})")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data


def available() -> list[str]:
    """Return the list of language codes for which a lexicon is bundled."""
    return sorted(p.stem for p in _LEXICON_DIR.glob("*.yaml"))


__all__ = ["load_lexicon", "available"]

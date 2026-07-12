"""SQL dialect resolution + optional `sqlglot`-backed transpilation.

The adapter must work without `sqlglot`. When `sqlglot` is installed (via the
`sql` extra), `transpile()` becomes available; otherwise it raises a clear
`SqlglotMissing` error.
"""

from __future__ import annotations

from typing import Optional

# Canonical dialect names → sqlglot dialect ids.
SUPPORTED_DIALECTS: tuple[str, ...] = (
    "postgres", "postgresql",
    "sqlite",
    "mysql", "mariadb",
    "mssql", "tsql",
    "oracle",
    "bigquery",
    "snowflake",
    "duckdb",
)

DEFAULT_DIALECT = "sqlite"

# Common aliases users might write in `# DIALECT: ...` headers.
_ALIASES = {
    "postgresql": "postgres",
    "pg": "postgres",
    "tsql": "mssql",
    "mariadb": "mysql",
}


class SqlglotMissing(RuntimeError):
    """Raised when an operation requires sqlglot but it isn't installed."""


def normalize_dialect(name: Optional[str]) -> str:
    """Return the canonical dialect identifier (lowercase, alias-resolved).

    Unknown dialects are returned unchanged (lowercased) so callers can opt
    into custom names without losing them.
    """
    if not name:
        return DEFAULT_DIALECT
    lowered = name.strip().lower()
    return _ALIASES.get(lowered, lowered)


def is_supported(name: Optional[str]) -> bool:
    """Return True if `name` resolves to a sqlglot-known dialect."""
    return normalize_dialect(name) in {normalize_dialect(d) for d in SUPPORTED_DIALECTS}


def has_sqlglot() -> bool:
    """Return True iff sqlglot is importable in the current environment."""
    try:
        import sqlglot  # noqa: F401
    except ImportError:
        return False
    return True


def transpile(sql: str, source: Optional[str], target: str) -> str:
    """Transpile `sql` between dialects using sqlglot.

    Raises:
        SqlglotMissing: when sqlglot is not installed.
    """
    if not has_sqlglot():
        raise SqlglotMissing("sqlglot is required for transpilation; install testql[sql]")
    import sqlglot
    src = normalize_dialect(source) if source else None
    dst = normalize_dialect(target)
    out = sqlglot.transpile(sql, read=src, write=dst)
    return out[0] if out else sql


__all__ = [
    "DEFAULT_DIALECT",
    "SUPPORTED_DIALECTS",
    "SqlglotMissing",
    "has_sqlglot",
    "is_supported",
    "normalize_dialect",
    "transpile",
]

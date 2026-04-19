"""CLI commands: testql suite, testql list — test suite execution and listing.

This is a backward-compatible re-export. New code should use:
    from testql.commands.suite import suite, list_tests
"""

from __future__ import annotations

# Re-export from new structured package
from .suite import suite, list_tests

__all__ = ["suite", "list_tests"]

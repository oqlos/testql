"""Test file API call pattern detector.

Infers API endpoints by analyzing HTTP call patterns in test files.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class TestEndpointDetector(BaseEndpointDetector):
    """Detect API calls in test files to infer endpoints."""

    HTTP_PATTERNS = [
        r'["\'](GET|POST|PUT|DELETE|PATCH)["\']\s*,\s*["\']([^"\']+)["\']',
        r'\.get\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.post\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.put\s*\(\s*["\']([^"\']+)["\']\s*\)',
        r'\.delete\s*\(\s*["\']([^"\']+)["\']\s*\)',
    ]

    def detect(self) -> list[EndpointInfo]:
        """Infer endpoints from test API calls."""
        self.endpoints = []
        test_files = self._find_files('**/test*.py')

        for test_file in test_files[:50]:
            try:
                self._analyze_test_file(test_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_test_file(self, test_file: Path) -> None:
        """Analyze test file for API calls."""
        content = test_file.read_text()

        for pattern in self.HTTP_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                method, path = self._extract_method_path(match, content)
                if path and path.startswith('/api/'):
                    self.endpoints.append(EndpointInfo(
                        path=path,
                        method=method.upper(),
                        source_file=test_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='rest',
                        framework='inferred-from-tests',
                    ))

    def _extract_method_path(self, match: re.Match, content: str) -> tuple[str, str]:
        """Extract HTTP method and path from regex match."""
        groups = match.groups()
        if len(groups) == 2:
            return groups[0], groups[1]

        # Method inferred from function name (e.g., .get(), .post())
        method_match = re.search(
            r'\.(get|post|put|delete|patch)',
            content[:match.start()],
            re.IGNORECASE
        )
        method = method_match.group(1).upper() if method_match else 'GET'
        return method, groups[0]

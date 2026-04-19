"""Express.js endpoint detector for JavaScript/TypeScript files."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class ExpressDetector(BaseEndpointDetector):
    """Detect Express.js routes from JavaScript/TypeScript files."""

    ROUTE_PATTERNS = [
        # app.get('/path', handler) or router.post('/path', handler)
        r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
        # app.route('/path').get().post()
        r"\.route\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\.(get|post|put|delete|patch)",
    ]

    def detect(self) -> list[EndpointInfo]:
        """Detect Express routes."""
        self.endpoints = []
        js_files = self._find_files('**/*.js') + self._find_files('**/*.ts')

        for js_file in js_files[:50]:
            try:
                self._analyze_express_file(js_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_express_file(self, js_file: Path) -> None:
        """Analyze Express routes in JS/TS file."""
        content = js_file.read_text()

        for pattern in self.ROUTE_PATTERNS:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                method, path = self._extract_method_path(match)
                if method and path:
                    self.endpoints.append(EndpointInfo(
                        path=path,
                        method=method.upper(),
                        source_file=js_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='rest',
                        framework='express',
                    ))

    def _extract_method_path(self, match: re.Match) -> tuple[str | None, str | None]:
        """Extract HTTP method and path from regex match."""
        groups = match.groups()
        if len(groups) == 2:
            # Pattern 1: (method, path)
            return groups[0], groups[1]
        # Pattern 2: (path, method) - reordered
        return groups[1], groups[0] if len(groups) > 1 else (None, None)

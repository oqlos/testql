"""Django URL pattern detector."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class DjangoDetector(BaseEndpointDetector):
    """Detect Django URL patterns."""

    def detect(self) -> list[EndpointInfo]:
        """Detect Django URL patterns from urls.py files."""
        self.endpoints = []
        urls_files = self._find_files('**/urls.py')

        for urls_file in urls_files:
            try:
                self._analyze_urls_py(urls_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_urls_py(self, urls_file: Path) -> None:
        """Analyze Django urls.py file."""
        content = urls_file.read_text()

        # Pattern for path() and re_path() calls
        patterns = [
            (r"path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)", 'path'),
            (r"re_path\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)", 're_path'),
            (r"url\s*\(\s*['\"]([^'\"]+)['\"]\s*,\s*([^,)]+)", 'url'),
        ]

        for pattern, ptype in patterns:
            for match in re.finditer(pattern, content):
                path, view = match.groups()
                if not path.startswith('admin/'):  # Skip admin
                    self.endpoints.append(EndpointInfo(
                        path=f"/{path.lstrip('/')}",
                        method='GET',
                        source_file=urls_file,
                        line_number=content[:match.start()].count('\n') + 1,
                        endpoint_type='rest',
                        framework='django',
                        handler_name=view.strip(),
                    ))

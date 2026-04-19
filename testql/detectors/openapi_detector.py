"""OpenAPI/Swagger specification endpoint detector."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from .base import BaseEndpointDetector
from .models import EndpointInfo


class OpenAPIDetector(BaseEndpointDetector):
    """Detect endpoints from OpenAPI/Swagger specifications."""

    SPEC_PATTERNS = [
        '**/openapi*.yaml',
        '**/openapi*.json',
        '**/swagger*.yaml',
        '**/swagger*.json',
        '**/*spec*.yaml',
        '**/*spec*.json',
    ]

    def detect(self) -> list[EndpointInfo]:
        """Parse OpenAPI 2.0/3.0 specs."""
        self.endpoints = []
        spec_files: list[Path] = []

        for pattern in self.SPEC_PATTERNS:
            spec_files.extend(self._find_files(pattern))

        for spec_file in spec_files:
            try:
                self._parse_spec(spec_file)
            except Exception:
                continue

        return self.endpoints

    def _parse_spec(self, spec_file: Path) -> None:
        """Parse OpenAPI specification."""
        content = spec_file.read_text()

        if spec_file.suffix == '.json':
            spec = json.loads(content)
        else:
            spec = yaml.safe_load(content)

        if not spec or 'paths' not in spec:
            return

        base_path = self._extract_base_path(spec)

        for path, methods in spec['paths'].items():
            if not isinstance(methods, dict):
                continue

            for method, details in methods.items():
                if method.startswith('x-') or method == 'parameters':
                    continue

                full_path = base_path + path
                endpoint = EndpointInfo(
                    path=full_path,
                    method=method.upper(),
                    source_file=spec_file,
                    line_number=0,
                    endpoint_type='rest',
                    framework='openapi',
                    handler_name=details.get('operationId'),
                    summary=details.get('summary'),
                    description=details.get('description'),
                    parameters=details.get('parameters', []),
                    tags=details.get('tags', []),
                    deprecated=details.get('deprecated', False),
                )
                self.endpoints.append(endpoint)

    def _extract_base_path(self, spec: dict) -> str:
        """Extract base path from OpenAPI spec."""
        # OpenAPI 2.0
        if 'basePath' in spec:
            return spec['basePath']
        # OpenAPI 3.0
        servers = spec.get('servers', [{}])
        if servers and isinstance(servers, list):
            return servers[0].get('url', '')
        return ''

"""OpenAPI Spec Generator from Detected Endpoints.

Generates OpenAPI 3.0 specifications from detected endpoints,
useful for documentation, client generation, and contract testing.
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from .endpoint_detector import EndpointInfo, UnifiedEndpointDetector


@dataclass
class OpenAPISpec:
    """OpenAPI specification container."""
    openapi: str = "3.0.3"
    info: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)
    components: dict = field(default_factory=dict)
    servers: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "openapi": self.openapi,
            "info": self.info,
            "servers": self.servers,
            "paths": self.paths,
            "components": self.components,
        }

    def to_json(self, indent: int = 2) -> str:
        """Generate JSON output."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_yaml(self) -> str:
        """Generate YAML output."""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)


class OpenAPIGenerator:
    """Generate OpenAPI specs from detected endpoints."""

    # Common response schemas
    DEFAULT_RESPONSES = {
        "200": {
            "description": "Success",
            "content": {
                "application/json": {
                    "schema": {"type": "object"}
                }
            }
        },
        "201": {
            "description": "Created",
            "content": {
                "application/json": {
                    "schema": {"type": "object"}
                }
            }
        },
        "204": {
            "description": "No Content"
        },
        "400": {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "detail": {"type": "string"}
                        }
                    }
                }
            }
        },
        "401": {"description": "Unauthorized"},
        "404": {"description": "Not Found"},
        "500": {"description": "Internal Server Error"},
    }

    # Path parameter patterns
    PATH_PARAM_PATTERNS = [
        (r'\{([^}]+)\}', True),  # FastAPI style: {param}
        (r'<([^>]+)>', False),   # Flask style: <param>
        (r':([a-zA-Z_][a-zA-Z0-9_]*)', False),  # Express style: :param
    ]

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.spec = OpenAPISpec()

    def generate(self, title: str | None = None, version: str = "1.0.0") -> OpenAPISpec:
        """Generate OpenAPI spec from detected endpoints."""
        # Detect endpoints
        detector = UnifiedEndpointDetector(self.project_path)
        endpoints = detector.detect_all()

        # Build spec
        self.spec.info = {
            "title": title or f"{self.project_path.name} API",
            "version": version,
            "description": f"Auto-generated OpenAPI spec for {self.project_path.name}",
        }

        self.spec.servers = [
            {"url": "http://localhost:8101", "description": "Local development"},
            {"url": "/", "description": "Relative"},
        ]

        # Group endpoints by path
        paths: dict[str, dict] = {}
        for ep in endpoints:
            if ep.endpoint_type != 'rest':
                continue  # Skip GraphQL, WebSocket for now

            path = self._normalize_path(ep.path)
            method = ep.method.lower()

            if path not in paths:
                paths[path] = {}

            # Build operation
            operation = self._build_operation(ep)
            paths[path][method] = operation

        self.spec.paths = paths

        # Add common schemas
        self.spec.components = {
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"},
                        "message": {"type": "string"},
                        "code": {"type": "integer"},
                    }
                },
                "HealthCheck": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["ok", "error"]},
                        "version": {"type": "string"},
                        "timestamp": {"type": "string", "format": "date-time"},
                    }
                },
            }
        }

        return self.spec

    def _normalize_path(self, path: str) -> str:
        """Normalize path for OpenAPI (ensure leading /)."""
        if not path.startswith('/'):
            path = '/' + path
        return path

    def _build_operation(self, ep: EndpointInfo) -> dict:
        """Build OpenAPI operation from endpoint."""
        operation = {
            "operationId": ep.handler_name or f"{ep.method.lower()}_{ep.path.replace('/', '_').strip('_')}",
            "summary": ep.summary or f"{ep.method} {ep.path}",
        }

        if ep.description:
            operation["description"] = ep.description

        # Add tags based on path
        tags = self._infer_tags(ep)
        if tags:
            operation["tags"] = tags

        # Add parameters
        parameters = self._extract_parameters(ep)
        if parameters:
            operation["parameters"] = parameters

        # Add request body for POST/PUT/PATCH
        if ep.method in ('POST', 'PUT', 'PATCH'):
            operation["requestBody"] = self._build_request_body(ep)

        # Add responses
        operation["responses"] = self._build_responses(ep)

        return operation

    def _infer_tags(self, ep: EndpointInfo) -> list[str]:
        """Infer tags from path."""
        path_parts = ep.path.strip('/').split('/')
        tags = []

        # Common API path patterns
        if len(path_parts) >= 2:
            if path_parts[0] in ('api', 'v1', 'v2', 'v3'):
                if len(path_parts) > 1:
                    tags.append(path_parts[1])
            else:
                tags.append(path_parts[0])

        # Add framework as tag
        if ep.framework and ep.framework != 'unknown':
            tags.append(ep.framework)

        return list(set(tags)) if tags else []

    def _extract_parameters(self, ep: EndpointInfo) -> list[dict]:
        """Extract path and query parameters."""
        parameters = []

        # Path parameters from URL pattern
        import re
        path_params = re.findall(r'\{([^}]+)\}', ep.path)
        for param in path_params:
            param_schema = {"type": "string"}
            if 'id' in param.lower():
                param_schema = {"type": "string"}  # Could be UUID or string ID
            elif 'int' in param.lower() or param.endswith('_id'):
                param_schema = {"type": "integer"}

            parameters.append({
                "name": param,
                "in": "path",
                "required": True,
                "schema": param_schema,
            })

        # Use endpoint parameters if available
        for p in ep.parameters:
            if isinstance(p, dict):
                param_in = p.get('in', 'query')
                if param_in == 'path' and not any(param["name"] == p.get('name') for param in parameters):
                    parameters.append({
                        "name": p.get('name', 'unknown'),
                        "in": "path",
                        "required": True,
                        "schema": {"type": p.get('type', 'string').lower()},
                    })
                elif param_in == 'query':
                    parameters.append({
                        "name": p.get('name', 'unknown'),
                        "in": "query",
                        "required": p.get('required', False),
                        "schema": {"type": p.get('type', 'string').lower()},
                    })

        return parameters

    def _build_request_body(self, ep: EndpointInfo) -> dict:
        """Build request body schema."""
        # Try to infer schema from handler name
        schema = {"type": "object"}

        if ep.handler_name:
            name_lower = ep.handler_name.lower()
            if 'create' in name_lower or 'post' in name_lower:
                schema["properties"] = {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                }
            elif 'update' in name_lower or 'put' in name_lower:
                schema["properties"] = {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "data": {"type": "object"},
                }

        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": schema
                }
            }
        }

    def _build_responses(self, ep: EndpointInfo) -> dict:
        """Build responses based on method."""
        responses = {}

        # Primary response
        if ep.method == 'DELETE':
            responses["204"] = self.DEFAULT_RESPONSES["204"]
        elif ep.method == 'POST':
            responses["201"] = self.DEFAULT_RESPONSES["201"]
            responses["400"] = self.DEFAULT_RESPONSES["400"]
        else:
            responses["200"] = self.DEFAULT_RESPONSES["200"]

        # Common error responses
        responses["401"] = self.DEFAULT_RESPONSES["401"]
        responses["404"] = self.DEFAULT_RESPONSES["404"]
        responses["500"] = self.DEFAULT_RESPONSES["500"]

        return responses

    def save(self, output_path: Path | None = None, format: str = "yaml") -> Path:
        """Save generated spec to file."""
        if output_path is None:
            output_path = self.project_path / f"openapi.{format}"

        if format == "json":
            output_path.write_text(self.spec.to_json())
        else:
            output_path.write_text(self.spec.to_yaml())

        return output_path


class ContractTestGenerator:
    """Generate contract tests from OpenAPI specs."""

    def __init__(self, spec: OpenAPISpec | dict | Path):
        if isinstance(spec, OpenAPISpec):
            self.spec = spec.to_dict()
        elif isinstance(spec, dict):
            self.spec = spec
        else:
            self.spec = self._load_spec(Path(spec))

    def _load_spec(self, path: Path) -> dict:
        """Load spec from file."""
        content = path.read_text()
        if path.suffix == '.json':
            return json.loads(content)
        return yaml.safe_load(content)

    def generate_contract_tests(self, output_file: Path) -> Path:
        """Generate TestQL contract tests from OpenAPI spec."""
        lines = [
            "# SCENARIO: API Contract Tests",
            "# Auto-generated from OpenAPI spec",
            "# TYPE: contract",
            "",
            "CONFIG[3]{key, value}:",
            "  base_url, ${api_url:-http://localhost:8101}",
            "  timeout_ms, 10000",
            "  strict_validation, true",
            "",
        ]

        paths = self.spec.get('paths', {})
        api_calls = []

        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ('get', 'post', 'put', 'patch', 'delete'):
                    expected_status = self._get_expected_status(method, operation)
                    summary = operation.get('summary', f'{method.upper()} {path}')
                    api_calls.append((method.upper(), path, expected_status, summary))

        if api_calls:
            lines.append(f"API[{len(api_calls)}]{{method, endpoint, expected_status}}:")
            for method, path, status, summary in api_calls[:30]:
                lines.append(f"  {method}, {path}, {status}  # {summary[:50]}")
            lines.append("")

        # Add schema validation assertions
        lines.append("# Contract Validation")
        lines.append("ASSERT[3]{field, operator, expected}:")
        lines.append("  content_type, ==, application/json")
        lines.append("  schema_valid, ==, true")
        lines.append("  status, <, 500")
        lines.append("")

        # Add response time check
        lines.append("PERFORMANCE[1]{metric, threshold}:")
        lines.append("  response_time_ms, <, 1000")

        content = '\n'.join(lines)
        output_file.write_text(content)
        return output_file

    def _get_expected_status(self, method: str, operation: dict) -> int:
        """Get expected status code from operation."""
        responses = operation.get('responses', {})
        for code in ['200', '201', '204']:
            if code in responses:
                return int(code)
        return 200 if method == 'get' else 201

    def validate_response(self, endpoint: str, method: str, response: dict) -> list[str]:
        """Validate a response against the spec."""
        errors = []

        # Find operation in spec
        paths = self.spec.get('paths', {})
        if endpoint not in paths:
            errors.append(f"Endpoint {endpoint} not found in spec")
            return errors

        operation = paths[endpoint].get(method.lower())
        if not operation:
            errors.append(f"Method {method} not found for {endpoint}")
            return errors

        # Validate status code
        status_code = str(response.get('status', 200))
        responses = operation.get('responses', {})
        if status_code not in responses:
            errors.append(f"Unexpected status code: {status_code}")

        # TODO: Validate response schema
        # TODO: Validate content-type

        return errors


def generate_openapi_spec(project_path: str | Path, output: Path | None = None, format: str = "yaml") -> Path:
    """Convenience function to generate OpenAPI spec."""
    generator = OpenAPIGenerator(project_path)
    generator.generate()
    return generator.save(output, format)


def generate_contract_tests_from_spec(spec_path: Path, output: Path) -> Path:
    """Generate contract tests from existing OpenAPI spec."""
    generator = ContractTestGenerator(spec_path)
    return generator.generate_contract_tests(output)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        path = sys.argv[1]
        generator = OpenAPIGenerator(path)
        spec = generator.generate()
        print(spec.to_yaml())

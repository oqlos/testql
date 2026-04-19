"""GraphQL schema and resolver endpoint detector."""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class GraphQLDetector(BaseEndpointDetector):
    """Detect GraphQL schemas and resolvers."""

    def detect(self) -> list[EndpointInfo]:
        """Detect GraphQL endpoints."""
        self.endpoints = []

        # Look for GraphQL schema files
        schema_files = (
            self._find_files('**/*.graphql') +
            self._find_files('**/schema.graphql')
        )

        for schema_file in schema_files[:20]:
            try:
                self._analyze_schema(schema_file)
            except Exception:
                continue

        # Look for Python GraphQL (graphene, strawberry)
        py_files = self._find_files('**/schema*.py')
        for py_file in py_files[:20]:
            try:
                self._analyze_python_graphql(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_schema(self, schema_file: Path) -> None:
        """Analyze GraphQL schema file."""
        content = schema_file.read_text()

        # Find Query and Mutation types
        type_patterns = [
            (r'type\s+Query\s*\{([^}]+)\}', 'query'),
            (r'type\s+Mutation\s*\{([^}]+)\}', 'mutation'),
        ]

        for pattern, gql_type in type_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                fields = match.group(1)
                for field_match in re.finditer(r'(\w+)\s*\(', fields):
                    field_name = field_match.group(1)
                    self.endpoints.append(EndpointInfo(
                        path='/graphql',
                        method='POST',
                        source_file=schema_file,
                        line_number=0,
                        endpoint_type='graphql',
                        framework='graphql',
                        handler_name=field_name,
                        summary=f'GraphQL {gql_type}: {field_name}',
                    ))

    def _analyze_python_graphql(self, py_file: Path) -> None:
        """Analyze Python GraphQL schemas (graphene)."""
        content = py_file.read_text()

        # Check for graphene or strawberry
        if 'graphene.ObjectType' not in content and 'strawberry.type' not in content:
            return

        # Find field definitions
        field_pattern = r'(\w+)\s*=\s*graphene\.(String|Int|Field|List)'
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            self.endpoints.append(EndpointInfo(
                path='/graphql',
                method='POST',
                source_file=py_file,
                line_number=content[:match.start()].count('\n') + 1,
                endpoint_type='graphql',
                framework='graphene',
                handler_name=field_name,
            ))

"""Flask endpoint detector including Blueprint support."""

from __future__ import annotations

import ast
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class FlaskDetector(BaseEndpointDetector):
    """Detect Flask endpoints including Blueprints."""

    def detect(self) -> list[EndpointInfo]:
        """Detect Flask routes and blueprints."""
        self.endpoints = []
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:100]:
            try:
                self._analyze_flask_file(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_flask_file(self, py_file: Path) -> None:
        """Analyze Flask file for routes."""
        content = py_file.read_text()
        tree = ast.parse(content)
        blueprints: dict[str, str] = {}  # name -> prefix

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                self._detect_blueprint(node, blueprints)
            elif isinstance(node, ast.FunctionDef):
                self._analyze_flask_route(node, py_file, content, blueprints)

    def _detect_blueprint(self, node: ast.Assign, blueprints: dict[str, str]) -> None:
        """Detect Flask Blueprint assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id == 'Blueprint':
                    prefix = self._extract_blueprint_prefix(call)
                    blueprints[target.id] = prefix

    def _extract_blueprint_prefix(self, call: ast.Call) -> str:
        """Extract url_prefix from Blueprint constructor."""
        for kw in call.keywords:
            if kw.arg == 'url_prefix' and isinstance(kw.value, ast.Constant):
                return kw.value.value
        return ''

    def _analyze_flask_route(
        self,
        node: ast.FunctionDef,
        py_file: Path,
        content: str,
        blueprints: dict[str, str]
    ) -> None:
        """Analyze @app.route and @bp.route decorators."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                path, methods = self._extract_flask_route_info(decorator, blueprints)
                if path:
                    for method in methods:
                        endpoint = EndpointInfo(
                            path=path,
                            method=method,
                            source_file=py_file,
                            line_number=node.lineno,
                            endpoint_type='rest',
                            framework='flask',
                            handler_name=node.name,
                        )
                        self.endpoints.append(endpoint)

    def _extract_flask_route_info(
        self,
        decorator: ast.Call,
        blueprints: dict[str, str]
    ) -> tuple[str | None, list[str]]:
        """Extract path and methods from Flask route decorator."""
        if isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
            path = self._extract_route_path(decorator)
            methods = self._extract_route_methods(decorator)
            path = self._apply_blueprint_prefix(decorator, path, blueprints)
            return path, methods
        return None, []

    def _extract_route_path(self, decorator: ast.Call) -> str | None:
        """Extract path from @route decorator."""
        if decorator.args and isinstance(decorator.args[0], ast.Constant):
            return decorator.args[0].value
        return None

    def _extract_route_methods(self, decorator: ast.Call) -> list[str]:
        """Extract HTTP methods from @route decorator kwargs."""
        methods = ['GET']  # Default
        for kw in decorator.keywords:
            if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                methods = []
                for elt in kw.value.elts:
                    if isinstance(elt, ast.Constant):
                        methods.append(elt.value.strip('"\''))
        return methods

    def _apply_blueprint_prefix(
        self,
        decorator: ast.Call,
        path: str | None,
        blueprints: dict[str, str]
    ) -> str | None:
        """Apply blueprint prefix to route path."""
        if path and isinstance(decorator.func.value, ast.Name):
            bp_name = decorator.func.value.id
            if bp_name in blueprints:
                return blueprints[bp_name] + path
        return path

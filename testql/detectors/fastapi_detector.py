"""FastAPI endpoint detector using AST analysis."""

from __future__ import annotations

import ast
from pathlib import Path

from .base import BaseEndpointDetector
from .models import EndpointInfo


class FastAPIDetector(BaseEndpointDetector):
    """Detect FastAPI endpoints using AST analysis."""

    HTTP_METHODS = {'get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'websocket'}

    def detect(self) -> list[EndpointInfo]:
        """Detect all FastAPI endpoints including routers."""
        self.endpoints = []
        py_files = self._find_files('**/*.py')

        for py_file in py_files[:100]:  # Limit for performance
            try:
                self._analyze_file(py_file)
            except Exception:
                continue

        return self.endpoints

    def _analyze_file(self, py_file: Path) -> None:
        """Analyze a single Python file for FastAPI patterns."""
        content = py_file.read_text()
        tree = ast.parse(content)

        routers: dict[str, str] = {}  # name -> prefix
        app_routers: list[tuple[str, str]] = []  # (router_name, prefix)

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                self._detect_router_assignment(node, routers)
                self._detect_app_assignment(node)
            elif isinstance(node, ast.Call):
                prefix = self._extract_include_router(node)
                if prefix:
                    app_routers.append(prefix)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._analyze_route_handler(node, py_file, content, routers)

    def _detect_router_assignment(self, node: ast.Assign, routers: dict[str, str]) -> None:
        """Detect APIRouter instance assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Call):
                call = node.value
                if isinstance(call.func, ast.Name) and call.func.id == 'APIRouter':
                    prefix = self._extract_router_prefix(call)
                    routers[target.id] = prefix

    def _extract_router_prefix(self, call: ast.Call) -> str:
        """Extract prefix from APIRouter constructor."""
        for kw in call.keywords:
            if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                return kw.value.value
        return ''

    def _detect_app_assignment(self, node: ast.Assign) -> None:
        """Detect FastAPI app instance."""
        pass  # Currently informational only

    def _extract_include_router(self, node: ast.Call) -> tuple[str, str] | None:
        """Extract router info from include_router call."""
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'include_router':
            prefix = ''
            for kw in node.keywords:
                if kw.arg == 'prefix' and isinstance(kw.value, ast.Constant):
                    prefix = kw.value.value
            return ('router', prefix)
        return None

    def _analyze_route_handler(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        py_file: Path,
        content: str,
        routers: dict[str, str]
    ) -> None:
        """Analyze a function decorated with HTTP method decorators."""
        for decorator in node.decorator_list:
            method, path = self._extract_route_info(decorator)
            if method and path:
                router_prefix = self._get_router_prefix(decorator, routers)
                full_path = router_prefix + path
                params = self._extract_parameters(node)

                endpoint = EndpointInfo(
                    path=full_path,
                    method=method.upper(),
                    source_file=py_file,
                    line_number=node.lineno,
                    endpoint_type='rest',
                    framework='fastapi',
                    handler_name=node.name,
                    parameters=params,
                    summary=self._extract_docstring(node),
                )
                self.endpoints.append(endpoint)

    def _extract_route_info(self, decorator: ast.expr) -> tuple[str | None, str | None]:
        """Extract HTTP method and path from route decorator."""
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            attr = decorator.func
            method = attr.attr.lower()
            if method in self.HTTP_METHODS:
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    return method, decorator.args[0].value
        return None, None

    def _get_router_prefix(self, decorator: ast.expr, routers: dict[str, str]) -> str:
        """Get prefix from router for route decorators."""
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            router_name = None
            if isinstance(decorator.func.value, ast.Name):
                router_name = decorator.func.value.id
            if router_name and router_name in routers:
                return routers[router_name]
        return ''

    def _extract_parameters(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[dict]:
        """Extract function parameters for API docs."""
        params = []
        for arg in node.args.args:
            if arg.arg not in ('self', 'cls'):
                param_type = self._get_annotation_name(arg.annotation)
                params.append({
                    'name': arg.arg,
                    'type': param_type,
                    'in': 'query' if param_type in ('int', 'str', 'float', 'bool') else 'body'
                })
        return params

    def _get_annotation_name(self, annotation: ast.expr | None) -> str:
        """Get type name from annotation."""
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
            return annotation.value
        return 'any'

    def _extract_docstring(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
        """Extract docstring from function."""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                return node.body[0].value.value.strip().split('\n')[0][:100]
        return None

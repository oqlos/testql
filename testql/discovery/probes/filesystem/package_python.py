from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from testql.discovery.probes.base import BaseProbe, ProbeResult
from testql.discovery.source import ArtifactSource


class PythonPackageProbe(BaseProbe):
    name = "filesystem.package_python"
    artifact_types = ("python_pkg",)
    cost = "medium"
    manifest_names = ("pyproject.toml", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "environment.yml")

    def probe(self, source: ArtifactSource) -> ProbeResult:
        evidence = []
        metadata: dict[str, Any] = {}
        roots = self.source_roots(source)
        manifests = self._find_manifests(roots)
        requirements = self._find_requirements(roots)
        python_files = self._find_python_files(roots)
        if not manifests and not requirements and not python_files:
            return self.no_match()
        for path in manifests + requirements:
            evidence.append(self.evidence("file", path, "python package marker"))
        if python_files and not manifests and not requirements:
            evidence.append(self.evidence("file_glob", roots[0], f"{len(python_files)} Python files"))
        metadata.update(self._read_metadata(manifests, requirements))
        types = ["python_pkg"]
        if self._looks_like_fastapi(python_files, metadata):
            types.append("fastapi")
            metadata.setdefault("frameworks", []).append("fastapi")
        confidence = self._confidence(manifests, requirements, python_files, metadata)
        return self.result(confidence, types, evidence, metadata)

    def _find_manifests(self, roots: list[Path]) -> list[Path]:
        found = []
        for root in roots:
            if root.is_file():
                continue
            for name in self.manifest_names:
                path = root / name
                if path.exists():
                    found.append(path)
        return found

    def _find_requirements(self, roots: list[Path]) -> list[Path]:
        found = []
        for root in roots:
            if root.is_dir():
                found.extend(sorted(root.glob("requirements*.txt")))
        return found

    def _find_python_files(self, roots: list[Path]) -> list[Path]:
        files = []
        for root in roots:
            if root.is_file() and root.suffix == ".py":
                files.append(root)
            elif root.is_dir():
                files.extend(path for path in root.rglob("*.py") if not _excluded(path))
        return files[:200]

    def _read_metadata(self, manifests: list[Path], requirements: list[Path]) -> dict[str, Any]:
        metadata: dict[str, Any] = {"dependencies": []}
        for path in manifests:
            text = path.read_text(errors="ignore")
            if path.name == "pyproject.toml":
                metadata.update(_parse_pyproject(text))
            elif path.name == "setup.cfg":
                metadata.update(_parse_setup_cfg(text))
            elif path.name == "setup.py":
                metadata.update(_parse_setup_py(text))
        for path in requirements:
            metadata["dependencies"].extend(_parse_requirements(path.read_text(errors="ignore")))
        metadata["dependencies"] = _dedupe_deps(metadata.get("dependencies", []))
        return {key: value for key, value in metadata.items() if value not in (None, "", [], {})}

    def _looks_like_fastapi(self, python_files: list[Path], metadata: dict[str, Any]) -> bool:
        deps = {item.get("name", "").lower() for item in metadata.get("dependencies", [])}
        if "fastapi" in deps:
            return True
        for path in python_files[:100]:
            text = path.read_text(errors="ignore")
            if "from fastapi import" in text or "FastAPI(" in text:
                return True
        return False

    def _confidence(self, manifests: list[Path], requirements: list[Path], python_files: list[Path], metadata: dict[str, Any]) -> int:
        if any(path.name == "pyproject.toml" for path in manifests) and metadata.get("name") and metadata.get("version"):
            return 95
        if manifests and metadata.get("name"):
            return 80
        if manifests or requirements:
            return 60
        if python_files:
            return 25
        return 0


def _parse_pyproject(text: str) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    project = _section(text, "project")
    poetry = _section(text, "tool.poetry")
    metadata["name"] = _quoted_value(project, "name") or _quoted_value(poetry, "name")
    metadata["version"] = _quoted_value(project, "version") or _quoted_value(poetry, "version")
    metadata["description"] = _quoted_value(project, "description") or _quoted_value(poetry, "description")
    metadata["license"] = _quoted_value(project, "license") or _quoted_value(poetry, "license")
    metadata["dependencies"] = _parse_pyproject_dependencies(text)
    return {key: value for key, value in metadata.items() if value not in (None, "", [], {})}


def _parse_setup_cfg(text: str) -> dict[str, Any]:
    metadata = _section(text, "metadata")
    return {
        key: value for key, value in {
            "name": _plain_value(metadata, "name"),
            "version": _plain_value(metadata, "version"),
            "description": _plain_value(metadata, "description"),
            "license": _plain_value(metadata, "license"),
        }.items() if value
    }


def _parse_setup_py(text: str) -> dict[str, Any]:
    return {
        key: value for key, value in {
            "name": _call_kw(text, "name"),
            "version": _call_kw(text, "version"),
            "description": _call_kw(text, "description"),
        }.items() if value
    }


def _parse_pyproject_dependencies(text: str) -> list[dict[str, str]]:
    deps = []
    match = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S)
    if match:
        for dep in re.findall(r'["\']([^"\']+)["\']', match.group(1)):
            deps.append(_dep(dep))
    poetry_deps = _section(text, "tool.poetry.dependencies")
    for line in poetry_deps.splitlines():
        if "=" in line and not line.strip().startswith("python"):
            name, value = line.split("=", 1)
            deps.append({"name": name.strip(), "version": value.strip().strip("\"'"), "scope": "runtime"})
    return _dedupe_deps(deps)


def _parse_requirements(text: str) -> list[dict[str, str]]:
    deps = []
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", "-")):
            deps.append(_dep(line))
    return deps


def _dep(value: str) -> dict[str, str]:
    name = re.split(r"[<>=~!\[]", value, maxsplit=1)[0].strip()
    version = value[len(name):].strip() or None
    item = {"name": name, "scope": "runtime"}
    if version:
        item["version"] = version
    return item


def _section(text: str, name: str) -> str:
    match = re.search(rf"^\[{re.escape(name)}\]\s*$(.*?)(?=^\[|\Z)", text, re.M | re.S)
    return match.group(1) if match else ""


def _quoted_value(text: str, key: str) -> str | None:
    match = re.search(rf'^\s*{re.escape(key)}\s*=\s*["\']([^"\']+)["\']', text, re.M)
    return match.group(1) if match else None


def _plain_value(text: str, key: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+)$", text, re.M)
    return match.group(1).strip() if match else None


def _call_kw(text: str, key: str) -> str | None:
    match = re.search(rf'{re.escape(key)}\s*=\s*["\']([^"\']+)["\']', text)
    return match.group(1) if match else None


def _dedupe_deps(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    output = []
    for item in items:
        name = item.get("name", "").lower()
        if name and name not in seen:
            seen.add(name)
            output.append(item)
    return output


def _excluded(path: Path) -> bool:
    return any(part in {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"} for part in path.parts)

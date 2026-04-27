"""Config files (Makefile, Taskfile.yml, docker-compose.yml, buf.yaml) → TestPlan IR.

Generates shell test scenarios from build system and configuration files.
"""

from __future__ import annotations

import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testql.ir import (
    Assertion,
    ScenarioMetadata,
    ShellStep,
    TestPlan,
)

from .base import BaseSource, SourceLike


def _load_file(source: SourceLike) -> str:
    """Load file content."""
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    elif "\n" not in source and Path(source).is_file():
        return Path(source).read_text(encoding="utf-8")
    return str(source)


def _parse_makefile(content: str, file_path: Path) -> list[dict[str, Any]]:
    """Parse Makefile and extract targets including included .mk files."""
    targets = []
    
    # Find include directives and load them
    include_pattern = r'^include\s+(.+)'
    for match in re.finditer(include_pattern, content, re.MULTILINE):
        include_path = match.group(1).strip()
        # Resolve glob patterns
        if '*' in include_path:
            for mk_file in file_path.parent.glob(include_path):
                if mk_file.is_file():
                    content += '\n' + mk_file.read_text()
        else:
            mk_file = file_path.parent / include_path
            if mk_file.exists():
                content += '\n' + mk_file.read_text()
    
    # Find .PHONY targets
    phony_pattern = r'\.PHONY:\s+(.+)'
    phony_matches = re.findall(phony_pattern, content)
    phony_targets = [t.strip() for match in phony_matches for t in match.split()]
    
    # Find target definitions
    target_pattern = r'^([a-zA-Z0-9_-]+):\s*(?:##\s*(.+))?'
    for match in re.finditer(target_pattern, content, re.MULTILINE):
        target_name = match.group(1)
        comment = match.group(2) or ""
        
        # Get target commands (next lines until next target or empty line)
        lines_after = content[match.end():].split('\n')
        commands = []
        for line in lines_after[:10]:  # Max 10 lines
            stripped = line.strip()
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                if not stripped:
                    break
                continue
            # Check if it's a command (starts with tab or whitespace, or has @, -, +)
            if line.startswith('\t') or line.startswith(' ') or stripped.startswith(('@', '-', '+')):
                # Remove @, -, + prefixes
                cmd = stripped.lstrip('@-+')
                if cmd:
                    commands.append(cmd)
            elif ':' in stripped and not any(c in stripped for c in ['=', ':=']):
                # Likely another target definition
                break
        
        if target_name not in ['.PHONY', '.DEFAULT_GOAL']:
            targets.append({
                'name': target_name,
                'comment': comment,
                'commands': commands,
                'is_phony': target_name in phony_targets
            })
    
    return targets


def _parse_taskfile(content: str) -> list[dict[str, Any]]:
    """Parse Taskfile.yml and extract tasks."""
    data = yaml.safe_load(content) or {}
    tasks = data.get('tasks', {})
    result = []
    for name, task in tasks.items():
        cmds = task.get('cmds', [])
        # Flatten dict commands to strings
        flat_cmds = []
        for cmd in cmds:
            if isinstance(cmd, dict):
                flat_cmds.append(cmd.get('cmd', ''))
            else:
                flat_cmds.append(str(cmd))
        result.append({
            'name': name,
            'comment': task.get('desc', ''),
            'commands': flat_cmds,
            'is_phony': True
        })
    return result


def _parse_docker_compose(content: str) -> list[dict[str, Any]]:
    """Parse docker-compose.yml and extract services."""
    data = yaml.safe_load(content) or {}
    services = data.get('services', {})
    return [
        {
            'name': name,
            'comment': f"Docker service: {service.get('image', 'unknown')}",
            'commands': [f"docker-compose up -d {name}"],
            'is_phony': True
        }
        for name, service in services.items()
    ]


def _parse_buf_yaml(content: str) -> list[dict[str, Any]]:
    """Parse buf.yaml and extract commands."""
    return [
        {
            'name': 'buf',
            'comment': f"Protobuf config",
            'commands': ['buf build', 'buf lint', 'buf format -w'],
            'is_phony': True
        }
    ]


def _filter_commands(commands: list[str], target_name: str) -> list[str]:
    """Filter and clean commands for testing."""
    filtered = []
    for cmd in commands:
        # Skip multi-line commands (contain newlines)
        if '\n' in cmd or ';' in cmd:
            continue
        # Remove template variables {{...}}
        cmd = re.sub(r'\{\{[^}]+\}\}', '', cmd)
        # Replace common variables
        cmd = cmd.replace('${COMPOSE_CMD}', 'docker-compose')
        # Skip empty commands after cleaning
        if not cmd.strip() or len(cmd.strip()) < 3:
            continue
        # Skip commands that are just echo statements (unless validation related)
        if cmd.strip().startswith('echo') and not any(k in target_name for k in ['validate', 'check', 'test']):
            continue
        filtered.append(cmd.strip())
    return filtered


@dataclass
class ConfigSource(BaseSource):
    """Makefile, Taskfile.yml, docker-compose.yml, buf.yaml → TestPlan."""

    name: str = "config"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (
        "Makefile",
        "makefile",
        "Taskfile.yml",
        "taskfile.yml",
        "docker-compose.yml",
        "docker-compose.yaml",
        "docker-compose.dev.yml",
        "docker-compose.prod.yml",
        "buf.yaml",
        "buf.gen.yaml",
    ))

    def load(self, source: SourceLike) -> TestPlan:
        """Translate config file into a TestPlan with shell steps."""
        if isinstance(source, str) and "\n" not in source:
            source_path = Path(source)
        else:
            source_path = Path("config")  # fallback
        
        content = _load_file(source)
        file_name = source_path.name
        
        # Parse based on file type
        targets = []
        if file_name in ['Makefile', 'makefile']:
            targets = _parse_makefile(content, source_path)
        elif file_name in ['Taskfile.yml', 'taskfile.yml']:
            targets = _parse_taskfile(content)
        elif 'docker-compose' in file_name:
            targets = _parse_docker_compose(content)
        elif 'buf.yaml' in file_name or 'buf.gen.yaml' in file_name:
            targets = _parse_buf_yaml(content)
        else:
            # Try to detect type
            if 'targets:' in content or 'tasks:' in content:
                targets = _parse_taskfile(content)
            elif 'services:' in content:
                targets = _parse_docker_compose(content)
            else:
                targets = _parse_makefile(content, source_path)
        
        # Create TestPlan
        plan = TestPlan(metadata=ScenarioMetadata(
            name=f"{file_name} tests",
            type="shell",
            extra={"source": "config", "file": file_name},
        ))
        
        plan.config["project_dir"] = str(source_path.parent)
        plan.config["timeout_ms"] = 60000
        plan.config["fail_fast"] = False
        
        # Add shell steps for key targets
        step_count = 0
        for target in targets[:10]:  # Limit to 10 targets
            if not target['commands']:
                continue
            
            filtered_commands = _filter_commands(target['commands'], target['name'])
            if not filtered_commands:
                continue
            
            # Use first command
            command = filtered_commands[0]
            plan.steps.append(ShellStep(
                command=f"cd {source_path.parent} && {command}",
                expect_exit_code=0,
                name=f"{target['name']}: {target['comment']}",
            ))
            step_count += 1
        
        # Add assertions
        plan.assertions = [
            Assertion(field="exit_code", op="==", expected=0),
            Assertion(field="output", op="not_contains", expected="Error"),
        ]
        
        return plan


__all__ = ["ConfigSource"]

"""Convert OQL/CQL scenario files into Unified IR for TestQL.

Parses OQL (Object Query Language) and CQL (Command Query Language) scenario files
to IQL commands for hardware/firmware testing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from testql.ir import TestPlan, ScenarioMetadata

from .base import BaseSource, SourceLike


@dataclass
class OqlCommand:
    """Represents a single OQL/CQL command."""
    command: str
    target: str
    args: dict[str, Any] = field(default_factory=dict)
    raw_line: str = ""
    line_number: int = 0


@dataclass
class ParsedScenario:
    """Represents a parsed OQL/CQL scenario file."""
    name: str
    source_file: Path
    config: dict[str, str] = field(default_factory=dict)
    setup_commands: list[OqlCommand] = field(default_factory=list)
    test_commands: list[OqlCommand] = field(default_factory=list)
    assertions: list[OqlCommand] = field(default_factory=list)
    cleanup_commands: list[OqlCommand] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class OqlParser:
    """Parse OQL/CQL scenario files.

    OQL (Object Query Language) and CQL (Command Query Language) are commonly
    used in hardware/firmware testing for configuring devices and running tests.

    Common commands:
    - SET <key> <value> - Set configuration
    - READ <target> - Read value from device
    - WRITE <target> <value> - Write value to device
    - CHECK <target> <expected> - Check/assert value
    - WAIT <ms> - Wait for milliseconds
    - POLL <target> <timeout> - Poll until condition met
    - EXEC <command> - Execute shell command
    - LOG <message> - Log message
    """

    # Command patterns
    COMMAND_PATTERNS = {
        'SET': r'^SET\s+["\']?([^"\']+)["\']?\s+["\']?([^"\']*)["\']?',
        'READ': r'^(READ|GET)\s+["\']?([^"\']+)["\']?',
        'WRITE': r'^(WRITE|PUT)\s+["\']?([^"\']+)["\']?\s+["\']?([^"\']*)["\']?',
        'CHECK': r'^(CHECK|ASSERT|VERIFY)\s+["\']?([^"\']+)["\']?\s*(?:==|=|!=|<=|>=|<|>)?\s*["\']?([^"\']*)["\']?',
        'WAIT': r'^WAIT\s+(\d+)',
        'POLL': r'^POLL\s+["\']?([^"\']+)["\']?\s+(\d+)',
        'EXEC': r'^EXEC\s+["\']?(.+)["\']?$',
        'LOG': r'^LOG\s+["\']?(.+)["\']?$',
        'CALL': r'^CALL\s+["\']?([^"\']+)["\']?\s*(?:WITH)?\s*(.*)',
        'SEQUENCE': r'^SEQUENCE\s+["\']?([^"\']+)["\']?',
        'END': r'^END',
    }

    def parse_file(self, file_path: Path | str) -> ParsedScenario | None:
        """Parse an OQL/CQL scenario file."""
        path = Path(file_path) if isinstance(file_path, str) else file_path
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IOError):
            return None

        scenario = ParsedScenario(
            name=path.stem,
            source_file=path,
        )

        lines = content.split('\n')
        in_sequence = False
        current_sequence_name = ""

        for line_num, raw_line in enumerate(lines, 1):
            line = raw_line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('//'):
                # Extract metadata from comments
                if ':' in line:
                    meta_match = re.match(r'[#//]\s*(\w+):\s*(.+)', line)
                    if meta_match:
                        scenario.metadata[meta_match.group(1).lower()] = meta_match.group(2).strip()
                continue

            # Parse commands
            cmd = self._parse_command(line, line_num, raw_line)
            if not cmd:
                continue

            # Handle SEQUENCE blocks
            if cmd.command == 'SEQUENCE':
                in_sequence = True
                current_sequence_name = cmd.target
                continue

            if cmd.command == 'END':
                in_sequence = False
                current_sequence_name = ""
                continue

            # Categorize commands
            if cmd.command == 'SET':
                scenario.config[cmd.target] = cmd.args.get('value', '')
            elif cmd.command in ('LOG', 'EXEC', 'WAIT'):
                scenario.test_commands.append(cmd)
            elif cmd.command in ('READ', 'WRITE', 'CALL', 'POLL'):
                scenario.test_commands.append(cmd)
            elif cmd.command == 'CHECK':
                scenario.assertions.append(cmd)
            elif cmd.command in ('CLEANUP', 'RESET', 'STOP'):
                scenario.cleanup_commands.append(cmd)
            else:
                scenario.test_commands.append(cmd)

        return scenario

    def _parse_command(self, line: str, line_num: int, raw_line: str) -> OqlCommand | None:
        """Parse a single command line."""
        for cmd_type, pattern in self.COMMAND_PATTERNS.items():
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                if cmd_type == 'SET' and len(groups) >= 2:
                    return OqlCommand(
                        command='SET',
                        target=groups[0],
                        args={'value': groups[1]},
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type in ('READ',) and len(groups) >= 1:
                    return OqlCommand(
                        command='READ',
                        target=groups[0] if len(groups) == 1 else groups[1],
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'WRITE' and len(groups) >= 2:
                    return OqlCommand(
                        command='WRITE',
                        target=groups[0],
                        args={'value': groups[1] if len(groups) > 1 else ''},
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'CHECK' and len(groups) >= 1:
                    return OqlCommand(
                        command='CHECK',
                        target=groups[0] if len(groups) == 1 else groups[1],
                        args={'expected': groups[2] if len(groups) > 2 else ''},
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'WAIT' and len(groups) >= 1:
                    return OqlCommand(
                        command='WAIT',
                        target=groups[0],
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'POLL' and len(groups) >= 2:
                    return OqlCommand(
                        command='POLL',
                        target=groups[0],
                        args={'timeout': groups[1]},
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'EXEC' and len(groups) >= 1:
                    return OqlCommand(
                        command='EXEC',
                        target=groups[0],
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'LOG' and len(groups) >= 1:
                    return OqlCommand(
                        command='LOG',
                        target=groups[0],
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'CALL' and len(groups) >= 1:
                    return OqlCommand(
                        command='CALL',
                        target=groups[0],
                        args={'params': groups[1] if len(groups) > 1 else ''},
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'SEQUENCE' and len(groups) >= 1:
                    return OqlCommand(
                        command='SEQUENCE',
                        target=groups[0],
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )
                elif cmd_type == 'END':
                    return OqlCommand(
                        command='END',
                        target='',
                        raw_line=raw_line.strip(),
                        line_number=line_num
                    )

        # Unknown command - treat as generic
        parts = line.split(None, 1)
        if parts:
            return OqlCommand(
                command=parts[0].upper(),
                target=parts[1] if len(parts) > 1 else '',
                raw_line=raw_line.strip(),
                line_number=line_num
            )

        return None


@dataclass
class OqlSource(BaseSource):
    """Source adapter for OQL/CQL scenario files."""

    name: str = "oql"
    file_extensions: tuple[str, ...] = field(default_factory=lambda: (".oql", ".cql", ".tql"))

    def load(self, source: SourceLike) -> TestPlan:
        """Load OQL/CQL file and convert to TestPlan IR."""
        scenarios = self.ingest(source)

        # Convert first scenario to TestPlan
        if scenarios:
            scenario = scenarios[0]
            metadata = ScenarioMetadata(
                name=scenario.get('metadata', {}).get('name', 'oql-scenario'),
                type=scenario.get('metadata', {}).get('type', 'hardware'),
            )
            return TestPlan(
                metadata=metadata,
                config=scenario.get('config', {}),
                steps=[],
            )

        return TestPlan(metadata=ScenarioMetadata(name="empty", type="hardware"))

    def ingest(self, path: SourceLike) -> list[dict]:
        """Ingest OQL/CQL files and convert to Unified IR."""
        file_path = Path(path) if isinstance(path, str) else path
        if not file_path.exists():
            return []

        parser = OqlParser()

        if file_path.is_file():
            scenario = parser.parse_file(file_path)
            scenarios = [scenario] if scenario else []
        else:
            scenarios = []
            for ext in ['*.oql', '*.cql', '*.tql']:
                for scenario_file in file_path.rglob(ext):
                    scenario = parser.parse_file(scenario_file)
                    if scenario:
                        scenarios.append(scenario)

        # Convert to Unified IR
        return [self._to_unified_ir(s) for s in scenarios if s]

    def _to_unified_ir(self, scenario: ParsedScenario) -> dict:
        """Convert ParsedScenario to Unified IR format."""
        ir = {
            'metadata': {
                'name': scenario.name,
                'type': self._detect_scenario_type(scenario),
                'source': str(scenario.source_file),
                **scenario.metadata,
            },
            'config': scenario.config,
            'setup': [],
            'steps': [],
            'assertions': [],
            'teardown': [],
        }

        # Convert test commands
        for cmd in scenario.test_commands:
            iql_cmd = self._convert_command(cmd)
            if iql_cmd:
                ir['steps'].append(iql_cmd)

        # Convert assertions
        for cmd in scenario.assertions:
            iql_cmd = self._convert_command(cmd)
            if iql_cmd:
                ir['assertions'].append(iql_cmd)

        # Convert cleanup
        for cmd in scenario.cleanup_commands:
            iql_cmd = self._convert_command(cmd)
            if iql_cmd:
                ir['teardown'].append(iql_cmd)

        return ir

    def _detect_scenario_type(self, scenario: ParsedScenario) -> str:
        """Detect scenario type from commands and metadata."""
        # Check metadata
        scenario_type = scenario.metadata.get('type', '').lower()
        if scenario_type:
            return scenario_type

        # Detect from commands
        all_commands = scenario.test_commands + scenario.assertions
        for cmd in all_commands:
            cmd_lower = cmd.command.lower()
            if cmd_lower in ('encoder_on', 'encoder_off', 'hardware'):
                return 'hardware'
            if cmd_lower in ('navigate', 'click', 'input'):
                return 'gui'
            if cmd_lower in ('get', 'post', 'put', 'delete'):
                return 'api'

        return 'integration'

    def _convert_command(self, cmd: OqlCommand) -> dict | None:
        """Convert OQL command to IQL format."""
        command_map = {
            'SET': self._convert_set,
            'READ': self._convert_read,
            'WRITE': self._convert_write,
            'CHECK': self._convert_check,
            'WAIT': self._convert_wait,
            'POLL': self._convert_poll,
            'EXEC': self._convert_exec,
            'LOG': self._convert_log,
            'CALL': self._convert_call,
        }

        converter = command_map.get(cmd.command)
        if converter:
            return converter(cmd)

        # Unknown command - pass through as-is
        return {
            'command': cmd.command,
            'args': cmd.target,
            'raw': cmd.raw_line,
        }

    def _convert_set(self, cmd: OqlCommand) -> dict:
        """Convert SET command to CONFIG."""
        return {
            'command': 'SET',
            'key': cmd.target,
            'value': cmd.args.get('value', ''),
        }

    def _convert_read(self, cmd: OqlCommand) -> dict:
        """Convert READ command to appropriate IQL command."""
        target = cmd.target.lower()
        if 'encoder' in target:
            return {'command': 'ENCODER_STATUS', 'target': target}
        elif 'hardware' in target:
            return {'command': 'HARDWARE', 'action': 'check', 'peripheral': target}
        else:
            return {'command': 'GET', 'target': cmd.target}

    def _convert_write(self, cmd: OqlCommand) -> dict:
        """Convert WRITE command to appropriate IQL command."""
        target = cmd.target.lower()
        value = cmd.args.get('value', '')

        if 'encoder' in target:
            if value == 'on':
                return {'command': 'ENCODER_ON'}
            elif value == 'off':
                return {'command': 'ENCODER_OFF'}
            elif 'scroll' in target:
                return {'command': 'ENCODER_SCROLL', 'delta': value}
            elif 'click' in target:
                return {'command': 'ENCODER_CLICK'}
        elif 'hardware' in target:
            return {'command': 'HARDWARE', 'action': 'configure', 'peripheral': target, 'value': value}

        return {'command': 'SET', 'key': cmd.target, 'value': value}

    def _convert_check(self, cmd: OqlCommand) -> dict:
        """Convert CHECK command to assertion."""
        target = cmd.target.lower()
        expected = cmd.args.get('expected', '')

        if 'status' in target:
            return {'command': 'ASSERT_STATUS', 'expected': expected}

        return {'command': 'ASSERT_JSON', 'path': target, 'operator': '==', 'expected': expected}

    def _convert_wait(self, cmd: OqlCommand) -> dict:
        """Convert WAIT command."""
        return {'command': 'WAIT', 'ms': int(cmd.target)}

    def _convert_poll(self, cmd: OqlCommand) -> dict:
        """Convert POLL command to WAIT_FOR."""
        return {'command': 'WAIT_FOR', 'target': cmd.target, 'timeout_ms': int(cmd.args.get('timeout', 5000))}

    def _convert_exec(self, cmd: OqlCommand) -> dict:
        """Convert EXEC command to SHELL."""
        return {'command': 'SHELL', 'command_line': cmd.target}

    def _convert_log(self, cmd: OqlCommand) -> dict:
        """Convert LOG command."""
        return {'command': 'LOG', 'message': cmd.target}

    def _convert_call(self, cmd: OqlCommand) -> dict:
        """Convert CALL command to API or function call."""
        return {'command': 'CALL', 'function': cmd.target, 'params': cmd.args.get('params', '')}

    def to_iql(self, ir: dict) -> list[str]:
        """Convert Unified IR to IQL commands."""
        lines = []

        # Header
        meta = ir.get('metadata', {})
        lines.append(f"# SCENARIO: {meta.get('name', 'Unnamed')}")
        lines.append(f"# TYPE: {meta.get('type', 'integration')}")
        lines.append("# GENERATED: true (from OQL/CQL)")
        lines.append("")

        # Config
        config = ir.get('config', {})
        if config:
            lines.append(f"CONFIG[{len(config)}]{{key, value}}:")
            for k, v in config.items():
                lines.append(f"  {k}, {v}")
            lines.append("")

        # Steps
        for step in ir.get('steps', []):
            cmd = step.get('command', '')
            if cmd == 'ENCODER_STATUS':
                lines.append("ENCODER_STATUS")
            elif cmd == 'ENCODER_ON':
                lines.append("ENCODER_ON")
            elif cmd == 'ENCODER_OFF':
                lines.append("ENCODER_OFF")
            elif cmd == 'ENCODER_SCROLL':
                lines.append(f"ENCODER_SCROLL {step.get('delta', 1)}")
            elif cmd == 'ENCODER_CLICK':
                lines.append("ENCODER_CLICK")
            elif cmd == 'HARDWARE':
                action = step.get('action', 'check')
                peripheral = step.get('peripheral', '')
                lines.append(f"HARDWARE {action} {peripheral}")
            elif cmd == 'WAIT':
                lines.append(f"WAIT {step.get('ms', 100)}")
            elif cmd == 'SHELL':
                lines.append(f'SHELL "{step.get("command_line", "")}"')
            elif cmd == 'LOG':
                lines.append(f'LOG "{step.get("message", "")}"')

        # Assertions
        assertions = ir.get('assertions', [])
        if assertions:
            lines.append("")
            for assertion in assertions:
                cmd = assertion.get('command', '')
                if cmd == 'ASSERT_STATUS':
                    lines.append(f"ASSERT_STATUS {assertion.get('expected', 200)}")
                elif cmd == 'ASSERT_JSON':
                    path = assertion.get('path', '')
                    expected = assertion.get('expected', '')
                    lines.append(f'ASSERT_JSON {path} == "{expected}"')

        return lines

"""Convert OQL/CQL scenario files into Unified IR for TestQL.

Parses OQL (Object Query Language) and CQL (Command Query Language) scenario files
to OQL commands for hardware/firmware testing.
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
                return self._create_command_from_match(cmd_type, match.groups(), line_num, raw_line)

        return self._parse_generic_command(line, line_num, raw_line)

    def _create_command_from_match(self, cmd_type: str, groups: tuple, line_num: int, raw_line: str) -> OqlCommand | None:
        """Create OqlCommand from regex match groups."""
        handlers = {
            'SET': self._parse_set_command,
            'READ': self._parse_read_command,
            'WRITE': self._parse_write_command,
            'CHECK': self._parse_check_command,
            'WAIT': self._parse_wait_command,
            'POLL': self._parse_poll_command,
            'EXEC': self._parse_exec_command,
            'LOG': self._parse_log_command,
            'CALL': self._parse_call_command,
            'SEQUENCE': self._parse_sequence_command,
            'END': self._parse_end_command,
        }
        
        handler = handlers.get(cmd_type)
        if handler:
            return handler(groups, line_num, raw_line)
        return None

    def _parse_set_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse SET command."""
        return OqlCommand(
            command='SET',
            target=groups[0],
            args={'value': groups[1]},
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_read_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse READ command."""
        return OqlCommand(
            command='READ',
            target=groups[0] if len(groups) == 1 else groups[1],
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_write_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse WRITE command."""
        return OqlCommand(
            command='WRITE',
            target=groups[0],
            args={'value': groups[1] if len(groups) > 1 else ''},
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_check_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse CHECK command."""
        return OqlCommand(
            command='CHECK',
            target=groups[0] if len(groups) == 1 else groups[1],
            args={'expected': groups[2] if len(groups) > 2 else ''},
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_wait_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse WAIT command."""
        return OqlCommand(
            command='WAIT',
            target=groups[0],
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_poll_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse POLL command."""
        return OqlCommand(
            command='POLL',
            target=groups[0],
            args={'timeout': groups[1]},
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_exec_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse EXEC command."""
        return OqlCommand(
            command='EXEC',
            target=groups[0],
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_log_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse LOG command."""
        return OqlCommand(
            command='LOG',
            target=groups[0],
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_call_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse CALL command."""
        return OqlCommand(
            command='CALL',
            target=groups[0],
            args={'params': groups[1] if len(groups) > 1 else ''},
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_sequence_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse SEQUENCE command."""
        return OqlCommand(
            command='SEQUENCE',
            target=groups[0],
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_end_command(self, groups: tuple, line_num: int, raw_line: str) -> OqlCommand:
        """Parse END command."""
        return OqlCommand(
            command='END',
            target='',
            raw_line=raw_line.strip(),
            line_number=line_num
        )

    def _parse_generic_command(self, line: str, line_num: int, raw_line: str) -> OqlCommand | None:
        """Parse unknown/generic command."""
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
            oql_cmd = self._convert_command(cmd)
            if oql_cmd:
                ir['steps'].append(oql_cmd)

        # Convert assertions
        for cmd in scenario.assertions:
            oql_cmd = self._convert_command(cmd)
            if oql_cmd:
                ir['assertions'].append(oql_cmd)

        # Convert cleanup
        for cmd in scenario.cleanup_commands:
            oql_cmd = self._convert_command(cmd)
            if oql_cmd:
                ir['teardown'].append(oql_cmd)

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
        """Convert OQL command to OQL format."""
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
        """Convert READ command to appropriate OQL command."""
        target = cmd.target.lower()
        if 'encoder' in target:
            return {'command': 'ENCODER_STATUS', 'target': target}
        elif 'hardware' in target:
            return {'command': 'HARDWARE', 'action': 'check', 'peripheral': target}
        else:
            return {'command': 'GET', 'target': cmd.target}

    def _convert_write(self, cmd: OqlCommand) -> dict:
        """Convert WRITE command to appropriate OQL command."""
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

    def to_oql(self, ir: dict) -> list[str]:
        """Convert Unified IR to OQL commands."""
        lines = []
        
        lines.extend(self._build_oql_header(ir))
        lines.extend(self._build_oql_config(ir))
        lines.extend(self._build_oql_steps(ir))
        lines.extend(self._build_oql_assertions(ir))
        
        return lines

    def _build_oql_header(self, ir: dict) -> list[str]:
        """Build OQL header section."""
        meta = ir.get('metadata', {})
        return [
            f"# SCENARIO: {meta.get('name', 'Unnamed')}",
            f"# TYPE: {meta.get('type', 'integration')}",
            "# GENERATED: true (from OQL/CQL)",
            "",
        ]

    def _build_oql_config(self, ir: dict) -> list[str]:
        """Build OQL config section."""
        config = ir.get('config', {})
        if not config:
            return []
        
        lines = [f"CONFIG[{len(config)}]{{key, value}}:"]
        for k, v in config.items():
            lines.append(f"  {k}, {v}")
        lines.append("")
        return lines

    def _build_oql_steps(self, ir: dict) -> list[str]:
        """Build OQL steps section."""
        lines = []
        for step in ir.get('steps', []):
            cmd = step.get('command', '')
            line = self._render_step_to_oql(cmd, step)
            if line:
                lines.append(line)
        return lines

    def _render_step_to_oql(self, cmd: str, step: dict) -> str | None:
        """Render a single step to OQL command."""
        renderers = {
            'ENCODER_STATUS': lambda s: "ENCODER_STATUS",
            'ENCODER_ON': lambda s: "ENCODER_ON",
            'ENCODER_OFF': lambda s: "ENCODER_OFF",
            'ENCODER_SCROLL': lambda s: f"ENCODER_SCROLL {s.get('delta', 1)}",
            'ENCODER_CLICK': lambda s: "ENCODER_CLICK",
            'HARDWARE': self._render_hardware_step,
            'WAIT': lambda s: f"WAIT {s.get('ms', 100)}",
            'SHELL': lambda s: f'SHELL "{s.get("command_line", "")}"',
            'LOG': lambda s: f'LOG "{s.get("message", "")}"',
        }
        
        renderer = renderers.get(cmd)
        return renderer(step) if renderer else None

    def _render_hardware_step(self, step: dict) -> str:
        """Render HARDWARE step to OQL."""
        action = step.get('action', 'check')
        peripheral = step.get('peripheral', '')
        return f"HARDWARE {action} {peripheral}"

    def _build_oql_assertions(self, ir: dict) -> list[str]:
        """Build OQL assertions section."""
        assertions = ir.get('assertions', [])
        if not assertions:
            return []
        
        lines = [""]
        for assertion in assertions:
            cmd = assertion.get('command', '')
            line = self._render_assertion_to_oql(cmd, assertion)
            if line:
                lines.append(line)
        return lines

    def _render_assertion_to_oql(self, cmd: str, assertion: dict) -> str | None:
        """Render a single assertion to OQL."""
        if cmd == 'ASSERT_STATUS':
            return f"ASSERT_STATUS {assertion.get('expected', 200)}"
        elif cmd == 'ASSERT_JSON':
            path = assertion.get('path', '')
            expected = assertion.get('expected', '')
            return f'ASSERT_JSON {path} == "{expected}"'
        return None

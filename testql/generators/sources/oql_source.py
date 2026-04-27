"""Convert OQL/CQL scenario files into Unified IR for TestQL.

Parses OQL (Object Query Language) and CQL (Command Query Language) scenario files
to OQL commands for hardware/firmware testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from testql.ir import TestPlan, ScenarioMetadata

from .base import BaseSource, SourceLike
from .oql_models import ParsedScenario
from .oql_parser import OqlParser

# Backward compatibility: re-export classes that were moved
from .oql_models import OqlCommand  # noqa: F401


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

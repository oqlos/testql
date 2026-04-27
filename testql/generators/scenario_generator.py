"""Scenario test generation mixin.

This module provides specialized generator for tests derived from OQL/CQL scenarios.
"""

from __future__ import annotations

from pathlib import Path

from .sources.oql_source import OqlParser


class ScenarioGeneratorMixin:
    """Mixin for generating tests from OQL/CQL scenarios."""

    def _generate_from_scenarios(self: "TestGenerator", output_dir: Path) -> Path | None:
        """Generate tests from existing OQL/CQL scenarios."""
        scenario_files = self.profile.discovered_files.get('scenarios_oql', [])
        if not scenario_files:
            return None

        parser = OqlParser()
        all_scenarios = []
        for sf in scenario_files[:10]:
            try:
                scenario = parser.parse_file(sf)
                if scenario:
                    all_scenarios.append(scenario)
            except Exception:
                continue

        if not all_scenarios:
            return None

        sections = [
            "# SCENARIO: Auto-generated from OQL/CQL Scenarios",
            "# TYPE: hardware",
            "# GENERATED: true",
            "",
        ]

        # Generate CONFIG
        all_config = {'generated_from': 'oql_scenarios', 'timeout_ms': '10000'}
        for scenario in all_scenarios:
            all_config.update(scenario.config)

        sections.append(f"CONFIG[{len(all_config)}]{{key, value}}:")
        for k, v in all_config.items():
            sections.append(f"  {k}, {v}")
        sections.append("")

        # Convert commands
        all_steps = []
        for scenario in all_scenarios:
            for cmd in scenario.test_commands:
                oql = self._convert_oql_command(cmd)
                if oql:
                    all_steps.append(oql)

        if all_steps:
            sections.append(f"# Converted {len(all_steps)} commands")
            for step in all_steps[:25]:
                sections.append(step)
            sections.append("")

        content = '\n'.join(sections)
        output_file = output_dir / 'generated-from-scenarios.testql.toon.yaml'
        output_file.write_text(content)

        return output_file

    def _convert_oql_command(self, cmd) -> str | None:
        """Convert OQL command to OQL."""
        cmd_type = cmd.command.upper()
        if cmd_type == 'WAIT':
            return f"WAIT {cmd.target}"
        elif cmd_type == 'ENCODER_ON':
            return "ENCODER_ON"
        elif cmd_type == 'ENCODER_OFF':
            return "ENCODER_OFF"
        elif cmd_type == 'ENCODER_STATUS':
            return "ENCODER_STATUS"
        elif cmd_type == 'LOG':
            return f'LOG "{cmd.target}"'
        elif cmd_type == 'EXEC':
            return f'SHELL "{cmd.target}"'
        return None

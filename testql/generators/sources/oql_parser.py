"""Parser for OQL/CQL scenario files."""

from __future__ import annotations

import re
from pathlib import Path

from .oql_models import OqlCommand, ParsedScenario


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
        content = self._read_file_content(path)
        if content is None:
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
            if self._should_skip_line(line):
                self._extract_metadata_from_comment(line, scenario)
                continue

            # Parse commands
            cmd = self._parse_command(line, line_num, raw_line)
            if not cmd:
                continue

            # Handle SEQUENCE blocks
            in_sequence, current_sequence_name = self._handle_sequence_block(
                cmd, in_sequence, current_sequence_name
            )
            if cmd.command in ('SEQUENCE', 'END'):
                continue

            # Categorize commands
            self._categorize_command(cmd, scenario)

        return scenario

    def _read_file_content(self, path: Path) -> str | None:
        """Read file content with error handling."""
        try:
            return path.read_text(encoding='utf-8')
        except (UnicodeDecodeError, IOError):
            return None

    def _should_skip_line(self, line: str) -> bool:
        """Check if line should be skipped (comment or empty)."""
        return not line or line.startswith('#') or line.startswith('//')

    def _extract_metadata_from_comment(self, line: str, scenario: ParsedScenario) -> None:
        """Extract metadata from comment lines."""
        if ':' in line:
            meta_match = re.match(r'[#//]\s*(\w+):\s*(.+)', line)
            if meta_match:
                scenario.metadata[meta_match.group(1).lower()] = meta_match.group(2).strip()

    def _handle_sequence_block(self, cmd: OqlCommand, in_sequence: bool, current_sequence_name: str) -> tuple[bool, str]:
        """Handle SEQUENCE/END block commands."""
        if cmd.command == 'SEQUENCE':
            return True, cmd.target
        elif cmd.command == 'END':
            return False, ""
        return in_sequence, current_sequence_name

    def _categorize_command(self, cmd: OqlCommand, scenario: ParsedScenario) -> None:
        """Categorize command into appropriate scenario section."""
        if cmd.command == 'SET':
            scenario.config[cmd.target] = cmd.args.get('value', '')
        elif cmd.command in ('LOG', 'EXEC', 'WAIT', 'READ', 'WRITE', 'CALL', 'POLL'):
            scenario.test_commands.append(cmd)
        elif cmd.command == 'CHECK':
            scenario.assertions.append(cmd)
        elif cmd.command in ('CLEANUP', 'RESET', 'STOP'):
            scenario.cleanup_commands.append(cmd)
        else:
            scenario.test_commands.append(cmd)

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

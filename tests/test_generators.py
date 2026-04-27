"""Tests for testql/generators modules."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testql.generators.base import BaseAnalyzer, TestPattern, ProjectProfile
from testql.generators.analyzers import ProjectAnalyzer
from testql.generators.generators import APIGeneratorMixin, PythonTestGeneratorMixin, ScenarioGeneratorMixin


class TestBaseAnalyzer:
    def test_init(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        assert analyzer.project_path == tmp_path
        assert isinstance(analyzer.profile, ProjectProfile)
        assert analyzer.profile.name == tmp_path.name

    def test_get_exclude_dirs(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        exclude = analyzer._get_exclude_dirs()
        assert 'venv' in exclude
        assert '__pycache__' in exclude
        assert '.git' in exclude

    def test_should_exclude_path_venv(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        venv_path = tmp_path / 'venv' / 'lib' / 'site.py'
        assert analyzer._should_exclude_path(venv_path)

    def test_should_exclude_path_src(self, tmp_path):
        analyzer = BaseAnalyzer(tmp_path)
        src_path = tmp_path / 'src' / 'app.py'
        assert not analyzer._should_exclude_path(src_path)


class TestProjectAnalyzerDetectType:
    def test_detect_python_api_fastapi(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool.poetry]\nfastapi = "^0.100"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-api'

    def test_detect_python_api_flask(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[dependencies]\nflask = "*"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-api'

    def test_detect_python_cli(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool]\nclick = "^8"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-cli'

    def test_detect_python_lib(self, tmp_path):
        (tmp_path / 'pyproject.toml').write_text('[tool.poetry]\nname = "mylib"')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'python-lib'

    def test_detect_hardware(self, tmp_path):
        (tmp_path / 'hardware').mkdir()
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'hardware'

    def test_detect_mixed_default(self, tmp_path):
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'mixed'

    def test_detect_web_frontend(self, tmp_path):
        (tmp_path / 'package.json').write_text('{}')
        (tmp_path / 'vite.config.js').write_text('')
        (tmp_path / 'index.html').write_text('')
        (tmp_path / 'playwright.config.js').write_text('')
        analyzer = ProjectAnalyzer(tmp_path)
        assert analyzer.detect_project_type() == 'web-frontend'

    def test_detect_web_frontend_missing_e2e_markers(self, tmp_path):
        # Has frontend markers but no e2e markers => falls through to next check
        (tmp_path / 'package.json').write_text('{}')
        (tmp_path / 'vite.config.js').write_text('')
        (tmp_path / 'index.html').write_text('')
        analyzer = ProjectAnalyzer(tmp_path)
        # No e2e marker means _detect_web_frontend returns None
        result = analyzer._detect_web_frontend(
            frozenset(['package.json', 'vite.config.js', 'index.html'])
        )
        assert result is None


class TestTestPattern:
    def test_defaults(self):
        pattern = TestPattern(
            name='test_login',
            target='/api/login',
            pattern_type='api',
            commands=[],
            assertions=[],
        )
        assert pattern.name == 'test_login'
        assert pattern.metadata == {}

    def test_metadata(self):
        pattern = TestPattern(
            name='test',
            target='target',
            pattern_type='unit',
            commands=[{'cmd': 'get'}],
            assertions=[{'assert': 'status'}],
            metadata={'author': 'tester'},
        )
        assert pattern.metadata['author'] == 'tester'


class TestOqlScenarioConversion:
    def test_oql_scenario_conversion(self, tmp_path):
        """Test conversion of OQL scenarios to OQL."""
        class TestGenerator(ScenarioGeneratorMixin):
            def __init__(self):
                self.profile = MagicMock()
                self.profile.discovered_files = {}
        
        generator = TestGenerator()
        
        # Create a mock OQL parser
        mock_scenario = MagicMock()
        mock_scenario.config = {'timeout_ms': '5000', 'base_url': 'http://localhost:8000'}
        
        mock_cmd1 = MagicMock()
        mock_cmd1.command = 'WAIT'
        mock_cmd1.target = '1000'
        
        mock_cmd2 = MagicMock()
        mock_cmd2.command = 'LOG'
        mock_cmd2.target = 'Test message'
        
        mock_cmd3 = MagicMock()
        mock_cmd3.command = 'ENCODER_ON'
        mock_cmd3.target = ''
        
        mock_scenario.test_commands = [mock_cmd1, mock_cmd2, mock_cmd3]
        
        with patch('testql.generators.scenario_generator.OqlParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_file.return_value = mock_scenario
            mock_parser_class.return_value = mock_parser
            
            generator.profile.discovered_files = {'scenarios_oql': ['test.oql']}
            
            output_dir = tmp_path / 'output'
            output_dir.mkdir()
            
            result = generator._generate_from_scenarios(output_dir)
            
            assert result is not None
            assert result.exists()
            
            content = result.read_text()
            assert 'WAIT 1000' in content
            assert 'LOG "Test message"' in content
            assert 'ENCODER_ON' in content

    def test_convert_oql_command_wait(self):
        """Test OQL WAIT command conversion."""
        class TestGenerator(ScenarioGeneratorMixin):
            pass
        
        generator = TestGenerator()
        
        cmd = MagicMock()
        cmd.command = 'WAIT'
        cmd.target = '500'
        
        result = generator._convert_oql_command(cmd)
        assert result == 'WAIT 500'

    def test_convert_oql_command_encoder(self):
        """Test OQL ENCODER commands conversion."""
        class TestGenerator(ScenarioGeneratorMixin):
            pass
        
        generator = TestGenerator()
        
        # Test ENCODER_ON
        cmd = MagicMock()
        cmd.command = 'ENCODER_ON'
        assert generator._convert_oql_command(cmd) == 'ENCODER_ON'
        
        # Test ENCODER_OFF
        cmd.command = 'ENCODER_OFF'
        assert generator._convert_oql_command(cmd) == 'ENCODER_OFF'
        
        # Test ENCODER_STATUS
        cmd.command = 'ENCODER_STATUS'
        assert generator._convert_oql_command(cmd) == 'ENCODER_STATUS'

    def test_convert_oql_command_unknown(self):
        """Test conversion of unknown OQL commands."""
        class TestGenerator(ScenarioGeneratorMixin):
            pass
        
        generator = TestGenerator()
        
        cmd = MagicMock()
        cmd.command = 'UNKNOWN_CMD'
        cmd.target = 'test'
        
        result = generator._convert_oql_command(cmd)
        assert result is None


class TestGeneratorConfig:
    def test_build_api_test_config(self):
        """Test building API test configuration."""
        class TestGenerator(APIGeneratorMixin):
            pass
        
        generator = TestGenerator()
        config = generator._build_api_test_config(['FastAPI'])
        
        assert len(config) > 0
        assert any('base_url' in line for line in config)
        assert any('timeout_ms' in line for line in config)
        assert any('retry_count' in line for line in config)
        assert any('retry_backoff_ms' in line for line in config)

    def test_build_api_test_header(self):
        """Test building API test header."""
        class TestGenerator(APIGeneratorMixin):
            pass
        
        generator = TestGenerator()
        header = generator._build_api_test_header(['FastAPI', 'Flask'])
        
        assert len(header) > 0
        assert any('Auto-generated' in line for line in header)
        assert any('api' in line for line in header)

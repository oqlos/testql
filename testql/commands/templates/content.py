"""Test content builder for generating TestQL test files."""

from __future__ import annotations


class TestContentBuilder:
    """Builds test content for different test types."""

    @classmethod
    def build(
        cls,
        test_type: str,
        name: str,
        meta_module: str,
        tags: list[str]
    ) -> str:
        """Build test content based on type."""
        builders = {
            "gui": cls._build_gui,
            "api": cls._build_api,
            "mixed": cls._build_mixed,
            "performance": cls._build_performance,
            "workflow": cls._build_workflow,
            "encoder": cls._build_encoder,
        }
        builder = builders.get(test_type, cls._build_encoder)
        return builder(name, meta_module, tags)

    @staticmethod
    def _build_meta_header(name: str, test_type: str, meta_module: str, tags: list[str]) -> str:
        """Build common meta header."""
        return f'''meta:
  name: "{test_type.capitalize()} Test: {name}"
  type: {test_type}
  module: {meta_module}
  tags: {tags}
  generated: true
'''

    @staticmethod
    def _build_standard_vars() -> str:
        """Build standard variable definitions."""
        return '''
SET base_url = "${base_url:-http://localhost:8100}"
SET api_url = "${api_url:-http://localhost:8101}"
SET encoder_url = "${encoder_url:-http://localhost:8105}"
'''

    @classmethod
    def _build_gui(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build GUI test content."""
        route = f"/{meta_module.replace('-', '/')}"
        if meta_module == "general":
            route = "/"

        return f'''{cls._build_meta_header(name, "gui", meta_module, tags)}
SET base_url = "${{base_url:-http://localhost:8100}}"
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# Setup
NAVIGATE "${{base_url}}{route}"
WAIT 500

# Main test steps
# TODO: Add your test steps here

# Cleanup
LOG "GUI test {name} completed"
'''

    @classmethod
    def _build_api(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build API test content."""
        return f'''{cls._build_meta_header(name, "api", meta_module, tags)}
SET api_url = "${{api_url:-http://localhost:8101}}"

# API calls
# GET "${{api_url}}/api/{meta_module}/list"
# ASSERT_STATUS 200

# Cleanup
LOG "API test {name} completed"
'''

    @classmethod
    def _build_mixed(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build mixed (GUI + API) test content."""
        return f'''{cls._build_meta_header(name, "mixed", meta_module, tags)}
SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# === GUI Verification ===
NAVIGATE "${{base_url}}/{meta_module}/detail/${{entity_id}}"
WAIT 300
ASSERT_SELECTOR "[data-testid='detail-view']" "exists"

LOG "Mixed test {name} completed"
'''

    @classmethod
    def _build_performance(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build performance test content."""
        return f'''{cls._build_meta_header(name, "performance", meta_module, tags + ["performance"])}
SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"

# Warmup
NAVIGATE "${{base_url}}/{meta_module}"
WAIT 1000

# Measure load time
TIMESTAMP start_load
NAVIGATE "${{base_url}}/{meta_module}"
WAIT_FOR_SELECTOR "[data-loaded='true']" timeout=5000
TIMESTAMP end_load

CALC load_time = end_load - start_load
LOG "Load time: ${{load_time}}ms"

ASSERT ${{load_time}} < 2000 "Page load should be under 2s"

LOG "Performance test {name} completed"
'''

    @classmethod
    def _build_workflow(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build workflow test content."""
        return f'''{cls._build_meta_header(name, "workflow", meta_module, tags)}
SET base_url = "${{base_url:-http://localhost:8100}}"
SET api_url = "${{api_url:-http://localhost:8101}}"

workflow:
  name: "{name}"
  steps:
    - name: "Step 1: Setup"
      action: SETUP

    - name: "Step 2: Action"
      action: EXECUTE

    - name: "Step 3: Verify"
      action: ASSERT

    - name: "Step 4: Cleanup"
      action: TEARDOWN

LOG "Workflow test {name} completed"
'''

    @classmethod
    def _build_encoder(cls, name: str, meta_module: str, tags: list[str]) -> str:
        """Build encoder test content (default)."""
        return f'''{cls._build_meta_header(name, "encoder", meta_module, tags)}
SET encoder_url = "${{encoder_url:-http://localhost:8105}}"

# Setup
ENCODER_ON
WAIT 200
ENCODER_STATUS
ASSERT_ENCODER "active"

# Cleanup
ENCODER_OFF
LOG "Encoder test {name} completed"
'''

#!/usr/bin/env python3
"""
Encoder Mode Coverage Matrix Generator
Generates comprehensive test matrix for all encoder possibilities in C2004
"""

import json
from typing import Dict, List, Any


class EncoderCoverageMatrix:
    """Generate and validate encoder mode test coverage matrix."""

    def __init__(self):
        self.modules = [
            "connect-id",
            "connect-data",
            "connect-reports",
            "connect-manager",
            "connect-config",
            "connect-scenario",
            "connect-template",
            "connect-test",
            "connect-protocol",
        ]

        self.keyboard_shortcuts = {
            "toggle": "Ctrl+E",
            "deactivate": "Escape",
            "navigateUp": "ArrowUp",
            "navigateDown": "ArrowDown",
            "accept": "Enter",
            "cancel": "Backspace",
            "nextSection": "Tab",
            "prevSection": "Shift+Tab",
            "pageNext": "PageDown",
            "pagePrev": "PageUp",
        }

        self.navigation_modes = [
            "keyboard",
            "encoder",
        ]

        self.actions = [
            "activate",
            "navigate_menu",
            "select_item",
            "navigate_within_page",
            "navigate_up",
            "confirm_selection",
            "cancel",
            "switch_section",
            "page_scroll",
            "deactivate",
        ]

        self.config_options = {
            "wheelThreshold": [480, 360, 600],
            "wheelResetMs": [180, 150, 200],
            "wheelLineUnit": [10, 5, 15],
            "clickConfirmDelayMs": [240, 200, 300],
        }

    def generate_module_matrix(self) -> Dict[str, Any]:
        """Generate test matrix for all modules."""
        matrix = {
            "total_modules": len(self.modules),
            "modules": {},
        }

        for module in self.modules:
            matrix["modules"][module] = {
                "encoder_mode_url": f"http://localhost:8100/{module}?mode=encoder",
                "keyboard_mode_url": f"http://localhost:8100/{module}?mode=keyboard",
                "default_url": f"http://localhost:8100/{module}",
                "tested": False,
                "shortcuts_applicable": list(self.keyboard_shortcuts.keys()),
            }

        return matrix

    def generate_shortcuts_matrix(self) -> Dict[str, Any]:
        """Generate test matrix for all keyboard shortcuts."""
        matrix = {
            "total_shortcuts": len(self.keyboard_shortcuts),
            "shortcuts": {},
        }

        for name, key in self.keyboard_shortcuts.items():
            matrix["shortcuts"][name] = {
                "key": key,
                "tested": False,
                "test_scenarios": [],
            }

        # Define test scenarios for each shortcut
        matrix["shortcuts"]["toggle"]["test_scenarios"] = [
            "activate_encoder_from_default",
            "toggle_encoder_on_off",
        ]

        matrix["shortcuts"]["navigateDown"]["test_scenarios"] = [
            "navigate_menu_items",
            "navigate_table_rows",
            "navigate_form_fields",
        ]

        matrix["shortcuts"]["navigateUp"]["test_scenarios"] = [
            "navigate_back_in_menu",
            "navigate_back_in_table",
        ]

        matrix["shortcuts"]["accept"]["test_scenarios"] = [
            "select_menu_item",
            "confirm_action",
            "submit_form",
        ]

        matrix["shortcuts"]["cancel"]["test_scenarios"] = [
            "cancel_action",
            "clear_input",
        ]

        matrix["shortcuts"]["nextSection"]["test_scenarios"] = [
            "tab_to_next_field",
            "tab_to_next_section",
        ]

        matrix["shortcuts"]["prevSection"]["test_scenarios"] = [
            "shift_tab_to_prev",
        ]

        matrix["shortcuts"]["pageNext"]["test_scenarios"] = [
            "scroll_page_down",
            "next_page_in_table",
        ]

        matrix["shortcuts"]["pagePrev"]["test_scenarios"] = [
            "scroll_page_up",
            "prev_page_in_table",
        ]

        matrix["shortcuts"]["deactivate"]["test_scenarios"] = [
            "escape_encoder_mode",
            "close_modal",
        ]

        return matrix

    def generate_actions_matrix(self) -> Dict[str, Any]:
        """Generate test matrix for all actions."""
        matrix = {
            "total_actions": len(self.actions),
            "actions": {},
        }

        for action in self.actions:
            matrix["actions"][action] = {
                "tested": False,
                "required_shortcuts": [],
                "test_modules": [],
            }

        # Map actions to shortcuts
        matrix["actions"]["activate"]["required_shortcuts"] = ["toggle"]
        matrix["actions"]["navigate_menu"]["required_shortcuts"] = ["navigateDown", "navigateUp"]
        matrix["actions"]["select_item"]["required_shortcuts"] = ["accept"]
        matrix["actions"]["navigate_within_page"]["required_shortcuts"] = ["navigateDown", "navigateUp"]
        matrix["actions"]["navigate_up"]["required_shortcuts"] = ["navigateUp"]
        matrix["actions"]["confirm_selection"]["required_shortcuts"] = ["accept"]
        matrix["actions"]["cancel"]["required_shortcuts"] = ["cancel", "deactivate"]
        matrix["actions"]["switch_section"]["required_shortcuts"] = ["nextSection", "prevSection"]
        matrix["actions"]["page_scroll"]["required_shortcuts"] = ["pageNext", "pagePrev"]
        matrix["actions"]["deactivate"]["required_shortcuts"] = ["deactivate"]

        return matrix

    def generate_config_matrix(self) -> Dict[str, Any]:
        """Generate test matrix for configuration options."""
        matrix = {
            "config_options": self.config_options,
            "total_combinations": 1,
        }

        for key, values in self.config_options.items():
            matrix["total_combinations"] *= len(values)

        matrix["selected_test_configs"] = [
            {
                "name": "default",
                "wheelThreshold": 480,
                "wheelResetMs": 180,
                "wheelLineUnit": 10,
                "clickConfirmDelayMs": 240,
            },
            {
                "name": "fast",
                "wheelThreshold": 360,
                "wheelResetMs": 150,
                "wheelLineUnit": 5,
                "clickConfirmDelayMs": 200,
            },
            {
                "name": "slow",
                "wheelThreshold": 600,
                "wheelResetMs": 200,
                "wheelLineUnit": 15,
                "clickConfirmDelayMs": 300,
            },
        ]

        return matrix

    def generate_comprehensive_matrix(self) -> Dict[str, Any]:
        """Generate complete coverage matrix."""
        return {
            "encoder_coverage_matrix": {
                "version": "1.0",
                "generated_for": "C2004 Encoder Mode",
                "modules": self.generate_module_matrix(),
                "shortcuts": self.generate_shortcuts_matrix(),
                "actions": self.generate_actions_matrix(),
                "config": self.generate_config_matrix(),
                "summary": {
                    "total_modules": len(self.modules),
                    "total_shortcuts": len(self.keyboard_shortcuts),
                    "total_actions": len(self.actions),
                    "total_config_combinations": len(self.config_options["wheelThreshold"]) *
                                                 len(self.config_options["wheelResetMs"]) *
                                                 len(self.config_options["wheelLineUnit"]) *
                                                 len(self.config_options["clickConfirmDelayMs"]),
                    "minimum_test_scenarios": self._calculate_minimum_scenarios(),
                },
            }
        }

    def _calculate_minimum_scenarios(self) -> int:
        """Calculate minimum number of test scenarios needed for full coverage."""
        # Each module needs to be tested
        module_tests = len(self.modules)

        # Each shortcut needs at least 1 test
        shortcut_tests = len(self.keyboard_shortcuts)

        # Each action needs at least 1 test
        action_tests = len(self.actions)

        # At least 3 config variations
        config_tests = 3

        # Total unique scenarios (some overlap)
        return module_tests + action_tests + config_tests

    def print_matrix_report(self):
        """Print formatted coverage matrix report."""
        matrix = self.generate_comprehensive_matrix()

        print("=" * 80)
        print("ENCODER MODE COVERAGE MATRIX - C2004")
        print("=" * 80)
        print()

        # Summary
        summary = matrix["encoder_coverage_matrix"]["summary"]
        print("📊 SUMMARY")
        print(f"  • Total Modules to Test: {summary['total_modules']}")
        print(f"  • Total Keyboard Shortcuts: {summary['total_shortcuts']}")
        print(f"  • Total Actions: {summary['total_actions']}")
        print(f"  • Config Combinations: {summary['total_config_combinations']}")
        print(f"  • Minimum Test Scenarios: {summary['minimum_test_scenarios']}")
        print()

        # Modules
        print("📦 MODULES COVERAGE MATRIX")
        print(f"{'Module':<25} {'Encoder URL':<50} {'Status'}")
        print("-" * 80)
        for module, data in matrix["encoder_coverage_matrix"]["modules"]["modules"].items():
            status = "✓" if data["tested"] else "○"
            print(f"{module:<25} {data['encoder_mode_url']:<50} {status}")
        print()

        # Keyboard Shortcuts
        print("⌨️  KEYBOARD SHORTCUTS COVERAGE MATRIX")
        print(f"{'Shortcut':<20} {'Key':<20} {'Scenarios':<15} {'Status'}")
        print("-" * 80)
        for name, data in matrix["encoder_coverage_matrix"]["shortcuts"]["shortcuts"].items():
            status = "✓" if data["tested"] else "○"
            scenarios = len(data["test_scenarios"])
            print(f"{name:<20} {data['key']:<20} {scenarios:<15} {status}")
        print()

        # Actions
        print("🎯 ACTIONS COVERAGE MATRIX")
        print(f"{'Action':<25} {'Required Shortcuts':<40} {'Status'}")
        print("-" * 80)
        for action, data in matrix["encoder_coverage_matrix"]["actions"]["actions"].items():
            status = "✓" if data["tested"] else "○"
            shortcuts = ", ".join(data["required_shortcuts"])
            print(f"{action:<25} {shortcuts:<40} {status}")
        print()

        # Config Options
        print("⚙️  CONFIGURATION OPTIONS MATRIX")
        for key, values in matrix["encoder_coverage_matrix"]["config"]["config_options"].items():
            print(f"  • {key}: {values}")
        print(f"  • Total Combinations: {matrix['encoder_coverage_matrix']['config']['total_combinations']}")
        print()

        print("🧪 RECOMMENDED TEST CONFIGS")
        for config in matrix["encoder_coverage_matrix"]["config"]["selected_test_configs"]:
            print(f"  • {config['name']}: threshold={config['wheelThreshold']}, "
                  f"reset={config['wheelResetMs']}ms, line={config['wheelLineUnit']}, "
                  f"delay={config['clickConfirmDelayMs']}ms")
        print()

        print("=" * 80)

        return matrix

    def export_to_json(self, filename: str = "encoder_coverage_matrix.json"):
        """Export matrix to JSON file."""
        matrix = self.generate_comprehensive_matrix()
        with open(filename, 'w') as f:
            json.dump(matrix, f, indent=2)
        print(f"✓ Matrix exported to: {filename}")


if __name__ == "__main__":
    generator = EncoderCoverageMatrix()
    matrix = generator.print_matrix_report()
    generator.export_to_json("/home/tom/github/oqlos/testql/encoder_coverage_matrix.json")

"""Execute TYPE: nlp2env TestTOON scenarios (NL → MCP → .env)."""

from .scenarios import PromptScenario, load_scenarios, load_scenarios_file, scenario_count

__all__ = [
    "Nlp2EnvRunner",
    "PromptScenario",
    "load_scenarios",
    "load_scenarios_file",
    "run_nlp2env_file",
    "scenario_count",
]


def __getattr__(name: str):
    if name == "Nlp2EnvRunner":
        from .runner import Nlp2EnvRunner

        return Nlp2EnvRunner
    if name == "run_nlp2env_file":
        from .runner import run_nlp2env_file

        return run_nlp2env_file
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

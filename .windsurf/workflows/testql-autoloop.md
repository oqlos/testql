---
description: Run one TestQL autoloop iteration using Windsurf (Cascade) as the LLM
---

# TestQL Autoloop — Windsurf Edition

No aider, no Docker, no OpenRouter needed. Windsurf/Cascade is the LLM.

## Iteration steps

1. Read current state.
   - Read `.testql/autoloop-state.json` to get `iteration`, `last_decision`, `open_failures`.
   - Read `.testql/schemas/llm-decision.schema.json` to know required output format.

2. Generate topology.
   - Run: `venv/bin/python3.13 -m testql topology . --format json`
   - Save output to `.testql/reports/topology.json`.

3. Run test scenarios.
   - Run: `venv/bin/python3.13 -m testql run testql-scenarios/generated-api-smoke.testql.toon.yaml --output json`
   - Save output to `.testql/reports/test-run.json`.

4. Cascade makes the decision.
   - Read `.testql/reports/topology.json` and `.testql/reports/test-run.json`.
   - Choose one of: `fix_code` | `fix_test` | `generate_more_tests` | `infra_blocked` | `stabilize_done`.
   - Apply minimal code or test changes if needed.
   - Write decision JSON to `.testql/reports/llm-decision.json` matching `.testql/schemas/llm-decision.schema.json`.

5. Validate decision JSON.
   - Run: `venv/bin/python3.13 -m jsonschema -i .testql/reports/llm-decision.json .testql/schemas/llm-decision.schema.json`

6. Update autoloop state.
   - Increment `iteration` in `.testql/autoloop-state.json`.
   - Set `last_decision` to the chosen decision value.

7. Check stop condition.
   - Stop if `decision == stabilize_done`.
   - Stop if `iteration >= max_iterations` (default 8).
   - Otherwise ask user to invoke `/testql-autoloop` again for next iteration.

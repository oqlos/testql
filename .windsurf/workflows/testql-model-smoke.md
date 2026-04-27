---
description: Smoke test Windsurf MCP loop with KIMI and SWE models
---

# TestQL Model Smoke — Windsurf Edition

Windsurf/Cascade is the LLM. No aider, no Docker, no OpenRouter key required.

## Step 1 — Bootstrap

// turbo
1. Create reports directory: `mkdir -p .testql/reports`

## Step 2 — Generate topology

// turbo
2. Run topology: `venv/bin/python3.13 -m testql topology . --format json > .testql/reports/topology.json`

## Step 3 — Run smoke scenario

// turbo
3. Run scenario: `venv/bin/python3.13 -m testql run testql-scenarios/generated-api-smoke.testql.toon.yaml --output json > .testql/reports/test-run.json`

## Step 4 — Cascade acts as KIMI 2.6

4. Read `.testql/reports/topology.json` and `.testql/reports/test-run.json`.
   Analyze results and write `.testql/reports/llm-decision.kimi.json` matching `.testql/schemas/llm-decision.schema.json`.
   Use model persona: KIMI 2.6 — analytical, high confidence, detail-oriented.

## Step 5 — Validate KIMI decision

// turbo
5. Validate: `venv/bin/python3.13 -m jsonschema -i .testql/reports/llm-decision.kimi.json .testql/schemas/llm-decision.schema.json`

## Step 6 — Cascade acts as SWE 1.6

6. Read same inputs again.
   Write `.testql/reports/llm-decision.swe.json` matching `.testql/schemas/llm-decision.schema.json`.
   Use model persona: SWE 1.6 — engineering-focused, conservative, code-quality driven.

## Step 7 — Validate SWE decision

// turbo
7. Validate: `venv/bin/python3.13 -m jsonschema -i .testql/reports/llm-decision.swe.json .testql/schemas/llm-decision.schema.json`

## Step 8 — Compare outputs

// turbo
8. Compare: `venv/bin/python3.13 -c "import json; k=json.load(open('.testql/reports/llm-decision.kimi.json')); s=json.load(open('.testql/reports/llm-decision.swe.json')); [print(f'{f}: KIMI={k.get(f)!r}  SWE={s.get(f)!r}') for f in ['decision','reason_code','confidence','risk_score']]"`

## Expected result

Both files validate against schema. Both contain:
`decision`, `reason_code`, `summary`, `next_actions`, `topology_focus`, `metrics`, `confidence`, `risk_score`

Decision must be one of: `fix_code`, `fix_test`, `generate_more_tests`, `infra_blocked`, `stabilize_done`

## Troubleshooting

- `testql` binary hangs — use `venv/bin/python3.13 -m testql` (check_and_upgrade skips in non-TTY)
- Schema mismatch — read `.testql/schemas/llm-decision.schema.json` for exact required fields

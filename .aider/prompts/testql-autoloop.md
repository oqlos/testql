You are running inside aider for the TestQL repository.

Goal:
Implement and execute one stabilization iteration using the local workflow and state files.

Required behavior:
1) Read `.windsurf/workflows/testql-autoloop.md` first.
2) Read `.testql/autoloop-state.json` and increment `iteration` by 1.
3) Run topology + generate + dry-run steps exactly as defined in workflow.
4) Write machine-readable decision JSON to `.testql/reports/llm-decision.json`.
5) Ensure output matches `.testql/schemas/llm-decision.schema.json`.
6) If infra is down, set `decision=infra_blocked` and do not modify source code.
7) Otherwise choose exactly one scoped improvement and stop.

Output constraints:
- Keep edits minimal and localized.
- Prefer deterministic commands and dry-run mode when uncertain.
- Do not commit changes automatically.

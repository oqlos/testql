# Project Echo (AI Context)

This example demonstrates generating AI-friendly project metadata by combining
TestTOON scenarios with DOQL system models.

## Files

- `app.doql.less` — System model in DOQL LESS format
- `api-contract.testql.toon.yaml` — API contract test scenarios
- `run.sh` — Generate the echo output

## Usage

```bash
# Generate text output (human-readable)
./run.sh text

# Generate JSON output (for LLM consumption)
./run.sh json

# Save to file
./run.sh json > ai-context.json
```

## Output Layers

| Layer | Source | Content |
|-------|--------|---------|
| **API Contract** | `*.testql.toon.yaml` | Endpoints, methods, assertions |
| **System Model** | `*.doql.less` | Entities, workflows, interfaces |
| **Unified Context** | Combined | Complete project metadata for AI |

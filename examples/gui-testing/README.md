# GUI Testing with TestQL

This example demonstrates Playwright-based GUI testing using TestQL's IQL syntax.

## Files

- `login-form.iql` — Navigate and interact with a login form
- `search-workflow.iql` — Search and assertion workflow
- `run.sh` — Execute the scenarios in dry-run mode

## Usage

```bash
# Dry-run (no browser required)
./run.sh --dry-run

# Full execution (requires Playwright)
./run.sh
```

## Concepts demonstrated

- **Navigation**: `NAVIGATE`, `WAIT`
- **Interaction**: `CLICK`, `INPUT`
- **Assertions**: `ASSERT_VISIBLE`, `ASSERT_TEXT`
- **Variables**: `SET` and `${var}` interpolation

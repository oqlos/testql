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

- **Navigation**: `GUI_START`, `WAIT`
- **Interaction**: `GUI_CLICK`, `GUI_INPUT`
- **Assertions**: `GUI_ASSERT_VISIBLE`, `GUI_ASSERT_TEXT`
- **Variables**: `SET` and `${var}` interpolation

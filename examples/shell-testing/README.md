# Shell Command Testing with TestQL

This example demonstrates testing shell commands and CLI tools using TestQL.

## Files

- `basic-commands.oql` — Run shell commands and assert exit codes
- `file-operations.oql` — File system operations with assertions
- `run.sh` — Execute the scenarios

## Usage

```bash
./run.sh
```

## Concepts demonstrated

- **Shell execution**: `SHELL`, `EXEC`, `RUN`
- **Exit code assertions**: `ASSERT_EXIT_CODE`
- **Dry-run safe**: examples use `ASSERT_EXIT_CODE` instead of stdout checks

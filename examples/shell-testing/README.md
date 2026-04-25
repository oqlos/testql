# Shell Command Testing with TestQL

This example demonstrates testing shell commands and CLI tools using TestQL.

## Files

- `basic-commands.iql` — Run shell commands and assert exit codes
- `file-operations.iql` — File system operations with assertions
- `run.sh` — Execute the scenarios

## Usage

```bash
./run.sh
```

## Concepts demonstrated

- **Shell execution**: `SHELL`, `EXEC`, `RUN`
- **Exit code assertions**: `ASSERT_EXIT_CODE`
- **Output assertions**: `ASSERT_CONTAINS`

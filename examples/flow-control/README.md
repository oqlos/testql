# Flow Control and Variables with TestQL

This example demonstrates variable management, logging, and script composition.

## Files

- `variables.iql` — SET, GET, interpolation
- `include-demo.iql` — INCLUDE other scripts
- `run.sh` — Execute the scenarios

## Usage

```bash
make dry-run    # Validate without executing
make run        # Full execution
```

## Concepts demonstrated

- `SET` / `GET` — Variable storage and retrieval
- `${var}` / `$var` — Variable interpolation
- `LOG` — Structured logging
- `WAIT` — Pauses and timeouts
- `INCLUDE` — Script composition

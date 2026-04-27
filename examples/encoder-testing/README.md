# Hardware Encoder Testing with TestQL

This example demonstrates testing hardware encoder interfaces using TestQL commands.

## Files

- `basic-encoder.oql` — Basic encoder lifecycle
- `complex-sequence.oql` — Multi-step encoder workflow
- `run.sh` — Execute the scenarios

## Usage

```bash
# Dry-run (no hardware required)
make dry-run

# Full execution (requires encoder hardware)
make run
```

## Concepts demonstrated

- `ENCODER_ON` / `ENCODER_OFF` — Activate/deactivate encoder mode
- `ENCODER_FOCUS` — Select column
- `ENCODER_SCROLL` — Scroll steps
- `ENCODER_CLICK` / `ENCODER_DBLCLICK` — Confirm/cancel
- `ENCODER_PAGE_NEXT` / `ENCODER_PAGE_PREV` — Navigation
- `ENCODER_STATUS` — Query state

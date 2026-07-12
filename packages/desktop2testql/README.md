# desktop2testql

Native desktop control backend for [TestQL](../../README.md) — powers the
interpreter's `DESKTOP_*` commands on Linux (X11 / Wayland).

## What it provides

- **Window management** — list, focus, launch, terminate (`wmctrl`/`xdotool`).
- **Input control** — click coordinates, type text, send key combos.
- **Screenshots** — full-screen and per-window capture with multiple
  fallbacks (grim, vdisplay, mss).
- **Vision assertions** — OCR text lookup, layout element counting, scene
  description (img2nl / imgl).

TestQL core keeps the `DESKTOP_*` DSL commands and resolves this backend
lazily: without the package installed the commands raise a clear
"install desktop2testql" error, and everything else works normally.

## Install

```bash
pip install desktop2testql            # backend (uses host tools)
pip install desktop2testql[control]   # + pyautogui/mss/opencv/pynput
pip install desktop2testql[vision]    # + img2nl/imgl/vdisplay/pytesseract
```

Host tools (`wmctrl`, `xdotool`, `wtype`, `ydotool`, `grim`) come from system
packages.

## Development

```bash
pip install -e packages/desktop2testql
pytest packages/desktop2testql/tests
```

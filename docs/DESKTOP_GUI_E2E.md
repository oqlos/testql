# Native Desktop GUI E2E (Linux)

TestQL can probe and test the **real OS desktop** on Linux — monitors, windows, screenshots, OCR layout, and mouse/keyboard — without Playwright and without GNOME screenshot portal permissions.

Integration stack:

| Package | Role |
|---------|------|
| **testql** | `DESKTOP_*` OQL commands |
| **vdisplay** | Monitor/window discovery, Xvfb virtual display |
| **img2nl** | Heuristic scene description (blank vs real UI) |
| **imgl** | OCR + semantic UI layout, click-by-label |

## Installation

```bash
cd ~/github/oqlos/testql
python -m venv .venv && source .venv/bin/activate

pip install -e ".[desktop,vision]" \
  -e ~/github/wronai/vdisplay[pillow] \
  -e ~/github/wronai/img2nl[analyze,similarity,opencv,scan] \
  -e ~/github/semcod/imgl
```

System packages (Debian/Ubuntu):

```bash
sudo apt install xvfb x11-apps xdotool xrandr tesseract-ocr tesseract-ocr-pol
# Optional for input on Wayland:
sudo apt install wtype ydotool
```

## Quick start

```bash
source .venv/bin/activate
export DISPLAY=:0   # required on GNOME Wayland + XWayland

# Run all desktop E2E scenarios (~3 min)
bash examples/desktop/run-all.sh

# Or individually:
testql run examples/desktop/gui-e2e-inspect.oql
testql run examples/desktop/gui-e2e-interact.oql
testql run examples/desktop/gui-e2e-multi-monitor.oql
```

## Screenshot: mirror → vdisplay → xwd

On **GNOME/Wayland**, direct tools (`grim`, `gnome-screenshot`, root `scrot`) often return a **black image** (no portal permission).

TestQL workaround (`testql/desktop/vdisplay_capture.py`):

```
1. vdisplay lists windows on selected monitor
2. xwd -id <window> captures each app window (works without portal)
3. Windows composited onto monitor-sized canvas
4. Canvas shown on VirtualDisplaySession (Xvfb :99+)
5. xwd captures from virtual display → PNG
6. img2nl validates scene; imgl runs OCR/layout
```

Capture metadata is written next to the PNG: `shot.png.vdisplay.json`

Example meta:

```json
{
  "method": "vdisplay_mirror_virtual",
  "monitor": "DP-2",
  "virtual_display": ":100",
  "window_count": 1,
  "scene_class": "general"
}
```

### Monitor selection

```testql
DESKTOP_CAPTURE "shot.png"              # primary monitor
DESKTOP_CAPTURE "shot.png" primary
DESKTOP_CAPTURE "shot.png" DP-2
DESKTOP_CAPTURE "shot.png" 0            # monitor index
```

Empty monitors (no app windows) still capture as `flat_monochrome` background.

## DESKTOP_* commands

### Discovery

| Command | Description |
|---------|-------------|
| `DESKTOP_MONITORS` | List monitors (vdisplay / xrandr) |
| `DESKTOP_LIST` | List open windows (xdotool / wmctrl) |
| `DESKTOP_INSPECT ["file.png"]` | Full probe: monitors + windows + capture + img2nl + imgl |

### Capture & vision

| Command | Description |
|---------|-------------|
| `DESKTOP_CAPTURE "file.png" [monitor]` | Mirror capture via vdisplay→Xvfb |
| `DESKTOP_DESCRIBE "file.png"` | img2nl scene summary (no vision LLM) |
| `DESKTOP_ANALYZE "file.png" [out.json]` | imgl OCR + layout JSON |
| `DESKTOP_ASSERT_TEXT "needle" ["file.png"]` | Assert OCR text visible |
| `DESKTOP_ASSERT_ELEMENTS min ["file.png"]` | Assert minimum imgl element count |
| `DESKTOP_CLICK_TEXT "label" ["file.png"]` | imgl find → coordinate click |

### Interaction

| Command | Description |
|---------|-------------|
| `DESKTOP_FOCUS "title"` | Focus window by title substring |
| `DESKTOP_ASSERT_WINDOW "title"` | Assert window exists |
| `DESKTOP_CLICK x y` | Click coordinates (ydotool / xdotool) |
| `DESKTOP_TYPE "text"` | Type into focused window (wtype / xdotool) |
| `DESKTOP_KEY Return` | Send key combo |
| `DESKTOP_LAUNCH "/path/app"` | Launch native app |
| `DESKTOP_STOP` | Terminate apps launched in session |

## Example scenarios

| File | Steps | ~Time | Side effects |
|------|-------|-------|--------------|
| `gui-e2e-inspect.oql` | Discovery + capture + analyze | ~80s | None |
| `gui-e2e-interact.oql` | Assert window, capture, assert elements, focus | ~52s | Focus only |
| `gui-e2e-multi-monitor.oql` | Capture DP-2, DP-1, HDMI-1 | ~65s | None |
| `gui-e2e-click.oql` | Assert + click by OCR label | — | **Mouse click** |
| `gui-e2e-vision-demo.oql` | OCR demo on static PNG | ~12s | None |
| `e2e-smoke.oql` | Minimal window list + capture | — | None |

## Example: interaction flow

```testql
DESKTOP_ASSERT_WINDOW "Toolbox"
DESKTOP_CAPTURE "shot.png" primary
DESKTOP_ASSERT_ELEMENTS 1 "shot.png"
DESKTOP_ANALYZE "shot.png" "shot.imgl.json"
DESKTOP_FOCUS "Toolbox"
```

Capture **before** focus — focused window may yield sparser OCR.

For text-specific asserts (when UI is stable):

```testql
DESKTOP_ASSERT_TEXT "Gateway" "shot.png"
DESKTOP_CLICK_TEXT "Gateway" "shot.png"   # has side effects
```

## Python API

```python
from testql.desktop.vdisplay_capture import capture_via_vdisplay, capture_monitor_mirror_virtual
from testql.desktop import vision as v

result = capture_monitor_mirror_virtual("shot.png", monitor="primary")
print(result.method, result.virtual_display, result.window_count)

layout = v.analyze_layout("shot.png")
print(layout["element_count"], layout["text_samples"])
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Black / `empty_dark_screen` PNG | grim/scrot root capture on Wayland | Use `DESKTOP_CAPTURE` (auto vdisplay mirror) |
| `gnome-screenshot` timeout | No portal permission | Expected — testql skips it on Wayland |
| `no windows captured` | No XWayland apps on monitor | Open an app on that monitor |
| DP-1/HDMI `flat_monochrome` | No app windows there | Normal for empty monitors |
| `DESKTOP_ASSERT_TEXT` fails | OCR text changed / not visible | Use `DESKTOP_ASSERT_ELEMENTS` instead |
| Missing `xwd` | x11-apps not installed | `sudo apt install x11-apps` |
| Missing Xvfb | xvfb not installed | `sudo apt install xvfb` |

## Architecture

```
testql/interpreter/_desktop.py     DESKTOP_* command handlers
testql/desktop/backend.py          wmctrl/xdotool/wtype + screenshot orchestration
testql/desktop/vdisplay_capture.py mirror→Xvfb capture pipeline
testql/desktop/vision.py           img2nl + imgl + vdisplay discovery wrappers
testql/desktop/catalog.py          MCP/nlp2uri command metadata
```

## See also

- [examples/desktop/README.md](../examples/desktop/README.md) — scenario index
- [testql-spec.md](./testql-spec.md) — DESKTOP command reference
- [vdisplay README](https://github.com/wronai/vdisplay) — virtual display orchestration
- [imgl README](https://github.com/semcod/imgl) — screenshot layout + OCR
- [img2nl README](https://github.com/wronai/img2nl) — heuristic image→NL

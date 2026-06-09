# Desktop E2E examples

Native Linux desktop tests using **testql + vdisplay + img2nl + imgl**.

Requires `DISPLAY=:0` on GNOME/Wayland (XWayland). See [docs/DESKTOP_GUI_E2E.md](../../docs/DESKTOP_GUI_E2E.md) for full setup.

## Run all (~3 min)

```bash
cd ~/github/oqlos/testql
source .venv/bin/activate
DISPLAY=:0 bash examples/desktop/run-all.sh
```

## Scenarios

| File | Description |
|------|-------------|
| [gui-e2e-inspect.oql](gui-e2e-inspect.oql) | Monitors, windows, mirror capture, img2nl, imgl |
| [gui-e2e-interact.oql](gui-e2e-interact.oql) | Assert Toolbox window, capture, assert elements, focus |
| [gui-e2e-multi-monitor.oql](gui-e2e-multi-monitor.oql) | Capture DP-2, DP-1, HDMI-1 |
| [gui-e2e-click.oql](gui-e2e-click.oql) | Assert + click by OCR (**side effect**) |
| [gui-e2e-vision-demo.oql](gui-e2e-vision-demo.oql) | OCR demo on static PNG (imgl sample) |
| [e2e-smoke.oql](e2e-smoke.oql) | Minimal smoke: list + assert window + capture |
| [list-windows.oql](list-windows.oql) | Window enumeration only |

TestTOON variants: `gui-e2e-inspect.testql.toon.yaml`, `gui-e2e-interact.testql.toon.yaml`

## Artifacts

Successful captures produce:

- `*.png` — screenshot
- `*.png.vdisplay.json` — capture method, monitor, virtual display
- `*.imgl.json` — imgl layout (when `DESKTOP_ANALYZE` writes output path)

## Typical output

```
📸 DESKTOP_CAPTURE → "interact-shot.png" [vdisplay_mirror_virtual @ :100, 1 windows]
✅ DESKTOP_ASSERT_ELEMENTS 4 >= 1
🧩 DESKTOP_ANALYZE: 1 windows, 4 elements
```

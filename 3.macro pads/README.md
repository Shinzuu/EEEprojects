# 3×5 Macropad — Raspberry Pi Pico, direct-wired, Vial-remappable

A 15-key USB macropad built from parts available at Bangladeshi online shops, hosted on a Raspberry Pi Pico (RP2040), and remappable live in Chrome at [vial.rocks](https://vial.rocks).

| | |
|---|---|
| Layout | 3 rows × 5 columns |
| Switches | B3F-4055 tactile (12 × 12 × 7.3 mm), 15× from udvabony.com |
| Controller | Raspberry Pi Pico (RP2040) from makersbd.com |
| Wiring | Direct GPIO → switch → GND. No matrix, no diodes. |
| Firmware | Vial-QMK (custom keyboard def in `vial-qmk/keyboards/handwired/shinzuu_3x5/`) |
| Remapping | Browser-based via [vial.rocks](https://vial.rocks) (WebHID) |
| Total cost | ~650 BDT |

## Why direct-wired

A traditional 4×4 matrix saves GPIO pins (8 instead of 16) but needs **one diode per switch** for full N-key rollover, plus matrix-scan code. RP2040 has 26 usable GPIO and we only need 15 — so each switch gets its own pin, ground returns to a shared bus, and the firmware simply reads each pin with the internal pull-up. No diodes, no ghosting, native NKRO, fewer solder joints.

## Files in this directory

```
3.macro pads/
├── README.md                  ← this file
├── 3x5_pico_spec.html         ← full build spec (open in browser)
├── 3x5Print+cut/              ← KLE layout + plate print/cut artwork
│   ├── keyboard-layout.json
│   ├── keyboard-layout.png
│   ├── plate_A4.pdf
│   └── plate_with_calibration.svg
├── measurements/
│   └── keyswitch_dimensions.md  ← reference for B3F / MX / Choc footprints
├── map_wizard.py              ← live in-browser GPIO ↔ grid mapping tool
├── keymap.json                ← captured pin map (raw)
├── keymap_pins.py             ← drop-in PINS list for KMK
└── probe_viewer.py            ← live HTML dashboard of which GPIO is grounded
```

The Vial-QMK keyboard definition lives outside this folder (in the gitignored `vial-qmk/` submodule). The kb-specific source files are at:

```
vial-qmk/keyboards/handwired/shinzuu_3x5/
├── keyboard.json              ← matrix + USB IDs + layout
└── keymaps/vial/
    ├── config.h               ← Vial UID + unlock combo
    ├── keymap.c               ← default layer + 3 transparent layers
    ├── rules.mk               ← VIA_ENABLE + VIAL_ENABLE
    └── vial.json              ← keymap layout for Vial GUI
```

## Pin map

The wiring is captured by `map_wizard.py`, which highlights one cell at a time and binds the next GPIO that goes LOW. Result:

```
        col 0  col 1  col 2  col 3  col 4
row 0   GP22   GP19   GP2    GP5    GP8
row 1   GP21   GP18   GP3    GP6    GP9
row 2   GP20   GP17   GP4    GP7    GP10
```

Free pins remaining for future expansion: **GP0, GP1, GP11–GP16, GP26–GP28** (11 pins). Plenty of headroom for a rotary encoder, an OLED on I²C0 (GP0/GP1), or an RGB strip.

## Workflow

### 1. Wire it up

Each switch has 4 pins (2 internal contacts mirrored). Use any one pin from each side:

- Side A → its assigned GPIO (e.g. row 0 col 0 → GP22)
- Side B → shared GND bus

Solder a single bare wire across one leg of every switch to form the GND bus, then run one pin per cell from the other leg into the Pico.

### 2. Capture the pin map

Plug the Pico in. Run the mapping wizard and follow the prompts in your browser:

```bash
python3 "3.macro pads/map_wizard.py"
# Open http://127.0.0.1:8000
```

It walks you through the 15 cells in **column-major** order: (0,0) (1,0) (2,0) (0,1) (1,1) (2,1) … (2,4). Press the highlighted switch each time. The wizard writes `keymap.json` and `keymap_pins.py` when complete.

### 3. Build the firmware

Vial-QMK is cloned at `vial-qmk/` (gitignored — fetch fresh with `git clone --recurse-submodules https://github.com/vial-kb/vial-qmk.git`).

Edit `vial-qmk/keyboards/handwired/shinzuu_3x5/keyboard.json` so the `matrix_pins.direct` array matches your captured pin map, then build:

```bash
cd vial-qmk
qmk compile -kb handwired/shinzuu_3x5 -km vial
# Output: vial-qmk/handwired_shinzuu_3x5_vial.uf2  (~94 KB)
```

Toolchain on Ubuntu 24.04: `sudo apt install gcc-arm-none-eabi cmake build-essential libnewlib-arm-none-eabi git python3-pip` then `pip install qmk --break-system-packages`.

### 4. Flash

**First time** (Pico in BOOTSEL — physical button or freshly-flashed `flash_nuke.uf2`):

```bash
cp vial-qmk/handwired_shinzuu_3x5_vial.uf2 /media/shinzuu/RPI-RP2/
```

**After Vial is on the Pico** — the case can be sealed and you'll never need the BOOTSEL button again:

1. Open Vial → menu → **Reset to Bootloader**.
2. Pico re-enumerates as `RPI-RP2`.
3. Drag the new `.uf2` onto it.
4. Pico reboots into the new firmware automatically.

### 5. Remap

Open <https://vial.rocks> in Chrome, click **Authorize device**, pick `shinzuu_3x5`. All four layers are pre-allocated; layer 0 ships with QWERT/ASDFG/ZXCVB and layers 1–3 are transparent. Changes write to flash immediately.

To make Linux give Chrome WebHID access without sudo, install:

```
# /etc/udev/rules.d/99-vial-hidraw.rules
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="5348", MODE="0666"
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="239a", MODE="0666"
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="2e8a", MODE="0666"
```

Then `sudo udevadm control --reload-rules && sudo udevadm trigger`.

## Debugging tools

`probe_viewer.py` is a one-shot diagnostic for the case where a key has gone dead and you don't want to take the case apart to multimeter the joints. It needs the **CircuitPython probe firmware** (`code.py` from before the Vial migration) running on the Pico, then:

```bash
python3 "3.macro pads/probe_viewer.py"
# Open http://127.0.0.1:8000
```

Live dashboard shows every GPIO; touching a pin to GND lights up its tile and logs the event. Auto-discovers the Pico by USB VID, survives replug.

## BOM (BD-sourced)

| Qty | Part | Source | Unit BDT | Subtotal |
|---|---|---|---|---|
| 1 | Raspberry Pi Pico (RP2040) | [makersbd.com](https://makersbd.com/product/raspberry-pi-pico-board-rp2040-dual-core-264kb-arm-low-power-microcomputer-high-performance-84) | 450 | 450 |
| 15 | B3F-4055 tactile switch (12×12×7.3 mm) | [udvabony.com u5454](https://udvabony.com/product/12x12x73mm-momentary-tactile-push-switch/) | 5 | 75 |
| 15 | Round caps for B3F (optional, multi-color) | udvabony | 5 | 75 |
| 1 m | Hookup wire (28 AWG, multi-color) | udvabony | ~50 | 50 |
| 1 | USB micro-B cable | local / on hand | — | — |
| | | | **Total** | **~650** |

## See also

- `3x5_pico_spec.html` — original design doc, written before the Vial migration. Pin assignments and wiring diagrams are still accurate; firmware section refers to KMK and is now superseded by Vial-QMK.
- Top-level [`CLAUDE.md`](../CLAUDE.md) — full repo conventions and the rest of the EEEprojects workflow.

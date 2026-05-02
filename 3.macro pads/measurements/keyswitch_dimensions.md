# Keyswitch Dimensions

Reference for macropad design. All dimensions in mm.
PCB hole/cutout sizes are for the switch body; keycap top sits above the plate.

---

## 1. Standard Mechanical (MX-style)

The de-facto DIY keyboard switch. Cherry MX, Gateron, Kailh BOX, Outemu — all share the same footprint and stem.

| Spec                     | Value                            |
|--------------------------|----------------------------------|
| Body (plate cutout)      | **14.0 × 14.0**                  |
| Body height (plate→PCB)  | 11.6 (plate-mount) / 15.6 (PCB-mount, with extra legs) |
| Total height (no cap)    | ~18.5 (top of stem above plate)  |
| Travel                   | 4.0                              |
| Pre-travel (actuation)   | 2.0                              |
| Stem                     | Cherry MX cross (+) — 4 mm       |
| Pins                     | 2 contact + 2 plastic locator (PCB-mount) or 2 only (plate-mount) |
| Switch pitch (key spacing)| **19.05 (1u)**                  |
| PCB hole pattern         | 2× contact Ø1.0; 1× center Ø4.0; 2× locator Ø1.7 |
| Plate thickness          | 1.5 (steel/FR4)                  |

Keycap: standard MX profile (OEM/Cherry/SA/DSA). 1u keycap top ~18 × 18.

---

## 2. Low-Profile Mechanical

Two competing footprints — **Kailh Choc v1** is the most common in DIY (used by Corne, Sweep, Ferris). Cherry MX Low-Profile exists but is rarer in BD.

### 2a. Kailh Choc v1 (PG1350)

| Spec                     | Value                            |
|--------------------------|----------------------------------|
| Body (plate cutout)      | **13.8 × 13.8**                  |
| Body height (plate→PCB)  | 2.2 (above plate ~3.0)           |
| Total height (no cap)    | **~4.6** (top of stem above plate) |
| Travel                   | 3.0                              |
| Pre-travel (actuation)   | 1.3                              |
| Stem                     | Choc proprietary (3 prongs, ~5.7×3.0) |
| Pins                     | 2 contact Ø1.2; 2 locator pegs Ø1.9 |
| Switch pitch             | **18.0 × 17.0** (Choc spacing)   OR 19.05 (MX-spacing PCBs) |
| PCB hole pattern         | 2× contact Ø1.2; 2× locator Ø1.9 (asymmetric) |
| Plate thickness          | 1.2–1.3                          |

Keycap: MBK / Chicago Steno / FK Choc — top ~17.5 × 16.5, height ~3.0.

### 2b. Kailh Choc v2 (PG1353)

Same body footprint as v1 but uses **MX cross stem** so MX keycaps fit.
- Body: 13.8 × 13.8, height ~5.0 above plate.
- Slightly taller than v1 because of the stem.

### 2c. Cherry MX Low-Profile (rare)

| Spec                     | Value                            |
|--------------------------|----------------------------------|
| Body (plate cutout)      | 14.0 × 14.0 (MX cutout)          |
| Total height (no cap)    | ~11.9                            |
| Travel                   | 3.2                              |
| Pre-travel               | 1.2                              |
| Stem                     | MX cross, shortened              |

---

## 3. Tactile Push Buttons (PCB / through-hole — what BD shops actually stock)

These are momentary tactile switches, not keyboard switches. Useful for nav/macro buttons on a sub-panel of the macropad. All sourced from udvabony.com.

### 3a. 12 × 12 × 7.3 mm — "B3F-4055" / Omron-clone

| Spec               | Value                          |
|--------------------|--------------------------------|
| Body               | **12.0 × 12.0 × 7.3**          |
| Pins               | 4-pin DIP, 2 internal contacts |
| Pin pitch          | 6.5 (across) × 8.5 (between rows) — actual leg spacing 7.62 typical |
| Actuation force    | ~2.55 N (260 gf)               |
| Travel             | 0.25                           |
| Cap option         | Round multi-color cap snaps on (B3F caps, BDT 5) |
| BD source          | udvabony u5454 — BDT 5.00      |
| Cross-shop         | makersbd "5pcs B3F-4055" BDT 65 |

### 3b. 12 × 12 × 9.5 mm — taller variant

| Spec     | Value                       |
|----------|-----------------------------|
| Body     | **12.0 × 12.0 × 9.5**       |
| Pins     | 4-pin DIP                   |
| BD source| udvabony u5431 — BDT 8.00   |

### 3c. 12 × 12 × 17 mm — long-stem (panel-mount through enclosure)

| Spec     | Value                       |
|----------|-----------------------------|
| Body     | **12.0 × 12.0 × 17.0** (stem extends ~10 mm above body) |
| BD source| udvabony u99051 — BDT 8.00  |

### 3d. 6 × 6 — common breadboard tact switches (for completeness)

| Variant       | Body              | BD source      |
|---------------|-------------------|----------------|
| 6 × 6 × 4.5   | low profile       | udvabony u5396 — BDT 4 |
| 6 × 6 × 5     | SMD               | udvabony u5259 — BDT 3 |
| 6 × 6 × 6     | standard          | udvabony u5402 — BDT 5 |
| 6 × 6 × 10    | long stem         | udvabony u5255 / u5393 — BDT 5 |
| 6 × 6 × 12    | extra long + cap  | udvabony u20998 — BDT 5 |
| 6 × 3.5 × 2   | SMD low-profile   | udvabony u5488 — BDT 10 |

Pin pitch on all 6×6 series: 4.5 mm × 6.5 mm (4-pin DIP), Ø0.7 mm legs.

---

## Pitch / spacing summary (for plate design)

| Switch type        | Min plate cutout | Recommended pitch (center-to-center) |
|--------------------|------------------|--------------------------------------|
| MX standard        | 14.0 × 14.0      | 19.05 (1u)                           |
| Choc v1            | 13.8 × 13.8      | 18.0 × 17.0 (Choc) or 19.05 (MX)     |
| 12×12 tact         | ~12.5 × 12.5     | 15.0 minimum (cap clearance: 19+)    |
| 6×6 tact           | ~6.5 × 6.5       | 9.0 minimum (10–12 typical)          |

---

## Notes for the macropad build

- **MX is the obvious pick** if BD shops stock them — none of the 3 indexed shops did at last scrape. Likely need AliExpress or local computer-parts shops (Computer Source, Ryans, Star Tech) for Outemu/Gateron.
- **Choc** for a thin / portable macropad — same sourcing problem.
- **B3F-4055 (12×12×7.3)** is the realistic local choice. Add 3D-printed keycap to make it feel like a keyboard. Tactile feel is decent (260 gf, similar to a clicky MX Blue but without the click).
- Pitch 19.05 is overkill for B3F — 15 mm minimum, 17 mm comfy, 19 mm if you want MX-compatible keycap clearance.

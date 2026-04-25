# DIY USB Microphone — Build Reference

Source videos:
- Video 1: ElectroNoobs — *I Built a $500 Microphone for Only $20 and It WORKS!* (2025-01-11) — https://www.youtube.com/watch?v=_j5UO-791_4
- Video 2: DIY Perks — *Building a quality USB-C microphone* (2021-11) — https://www.youtube.com/watch?v=LoQu3XXIayc

Both builds share the **same circuit topology**. ElectroNoobs is a clone of DIY Perks with: 3D-printed body instead of brass tube, custom PCB, and INA217 substituted for the THAT1512 (because his THAT1512 was counterfeit/dead).

---

## Topology overview

`JLI-2555 capsule  →  2N4416 JFET source-follower  →  THAT1512 (or INA217) instrumentation preamp  →  22µF coupling cap  →  3.5 mm TRS  →  generic USB sound-card dongle (CM108B class) or Behringer LINE 2 USB  →  USB host`

Power: USB 5V → NMA0515SC isolated DC/DC → ±15V rails for the preamp.

This is **not** a native-USB / MEMS / digital build. The "USB" stage is a re-purposed analog→USB sound card. No firmware, no driver, no microcontroller.

---

## Bill of Materials (BOM)

### Active / signal chain

| Qty | Part | Purpose | Notes / sources |
|-----|------|---------|-----------------|
| 1 | **JLI-2555BXZ3-GP** large-diaphragm back-electret capsule | Mic capsule (the "$500 sound" part) | micbooster.com (EU), jlielectronics.com (US), eBay |
| 1 | **THAT1512** mic preamp IC (8-pin DIP) | Differential preamp | Newark, Mouser, eBay. Counterfeits common on AliExpress |
| 1 | **INA217** | Drop-in alternative to THAT1512 (ElectroNoobs uses this) | Add ~2.2 kΩ gain resistor when substituting |
| 1 | **2N4416** N-channel JFET | Source-follower buffer at capsule | Alternates: J111 / J112 / J113 / J304 (slightly more noise). Clip the case/4th pin |
| 1 | **NMA0515SC** isolated DC/DC | 5V → ±15V preamp rails | Mouser / RS Online |
| 1 | USB audio interface module | Analog-out → USB | **Best:** Behringer LINE 2 USB (or GUITAR 2 USB) ~€20. **Cheap:** any CM108B dongle (remove R13 bias resistor) |

### Passives

| Qty | Part | Purpose |
|-----|------|---------|
| 3 | 22 µF non-polarized (bipolar) electrolytic, 35V | Signal coupling caps. Upgrade path: 2.2 µF polystyrene film |
| 4 | 2200 µF 16V electrolytic | ±15V rail decoupling |
| 2 | 100 Ω 1/4W | Series with THAT1512 V+ (pin 7) and V- (pin 4) |
| — | 2.2 kΩ, 3.9 kΩ, 5.6 Ω … 2.2 kΩ | Gain network around THAT1512 RG1/RG2 (rotary switch); bridge for fixed high gain |
| — | 1/4W metal-film resistors, 1% | All signal-path |
| — | 0.1 µF ceramic | Decoupling (optional) |

### Mechanical / enclosure

| Qty | Part | Purpose |
|-----|------|---------|
| 2 | USB-C breakout boards | Body connectors |
| 1 | Brass tube, 7 mm OD (DIY Perks) **or** 3D-printed body (ElectroNoobs STLs) | Body |
| — | Brass rod, 6 mm + 3 mm | Yoke / arm (DIY Perks) |
| 2 | Nitrile O-rings, 72 × 1.5 mm (DIY Perks) **or** 150 mm O-ring (ElectroNoobs) | Capsule shock-mount |
| 1 | Brass / metal mesh | Grille + Faraday cage |
| 1 | Copper desoldering braid, ~2 mm | Internal cable shield |
| — | Enameled copper wire | Internal signal wiring |
| 1 | Ball screw | Yoke pivot (ElectroNoobs) |

---

## Wiring summary

1. **JLI-2555 hot pin → 2N4416 gate.** No DC blocking cap on the gate — capsule is back-electret, not 48V phantom.
2. **2N4416 source-follower.** Drain → +15V. Source → bias resistor → -15V. Source is the output node.
3. **Source → 22 µF bipolar coupling cap → THAT1512 +IN (or INA217 IN+).**
4. **THAT1512 supply:** +15V → 100 Ω → pin 7. -15V → 100 Ω → pin 4. Gain set by resistor between RG1/RG2 (pins 1/8). Rotary switch picks 5.6 Ω … 2.2 kΩ; bridging RG1–RG2 = max gain.
5. **THAT1512 OUT → 22 µF bipolar → 3.5 mm TRS plug.** Plug into the USB sound card's mic / line input.
6. **Power path:** host USB-C VBUS (5V) → NMA0515SC → ±15V to preamp.
7. **Shielding:** all internal signal wires are enameled copper run inside desoldering braid. Braid grounds to chassis at the **capsule end only** (single-point earth) — multi-point earthing causes 50/60Hz hum.

### Common failure modes (from forum)

- Counterfeit THAT1512 → swap to INA217.
- Counterfeit NMA0515SC → check ±15V rails before installing the preamp IC.
- JFET case-pin grounded by accident → clip case pin off.
- Multi-point shield grounding → hum loop.
- USB sound-card dongle inside the shielded body → noise; ground the DC supply ground first.

---

## Schematics, PCB files, downloads

### ElectroNoobs (Video 1)

- Project page (full write-up + schematic image): https://electronoobs.com/eng_circuitos_tut91.php
- Parts list page: https://electronoobs.com/eng_circuitos_tut91_parts1.php
- Free Gerbers (`GERBERs.zip`): https://electronoobs.com/eng_circuitos_tut91_gerbers1.php
- 3D-printable body STLs: linked on the project page
- Hackaday writeup: https://hackaday.com/2025/01/14/audio-on-a-shoestring-diy-your-own-studio-grade-mic/

### DIY Perks (Video 2)

- Official project page (resource pack `DIY-Perks-Mic-Preamp-Resource-Pack-V1.1.zip` — schematic + PCB template + parts list):
  https://diyperks.com/project_31_high-quality-usb-c-microphone/
- Hackaday.io mirror: https://hackaday.io/project/185055-diyperks-diy-building-a-quality-usb-c-microphone/
- Hackaday news writeup: https://hackaday.com/2021/11/06/cheap-diy-mic-sounds-and-looks-damn-good/
- Official forum (most up-to-date BOM corrections): https://forum.diyperks.com/microphones/usb-c-microphone-official-topic/
- Audio-capture-card chip recommendations: https://forum.diyperks.com/microphones/audio-capture-card-options/

### Community KiCad / PCB ports

- **aeonSolutions/DIYPERKS_microphone_project** — Gerbers + KiCad of the original PCB; pre-assembled boards ~€20+ship. CC BY-NC-SA 4.0.
  https://github.com/aeonSolutions/DIYPERKS_microphone_project
- **lmarzen/diy-microphone** — Compact KiCad redesign that fits inside a BM-800 shell; XLR replaced with USB-C; includes 3D-printable USB-C mount (`XLR_to_USB_mic.STL`). GPL-3.0.
  https://github.com/lmarzen/diy-microphone
- **TrojanPinata/DIY-Mic** — Modified build: 3D-printed body, INA217 swap (with 2.2 kΩ gain res), 2023 PCB also fitted into BM-800 shell. Includes Google Sheets BOM, stripboard PNGs, STLs.
  https://github.com/TrojanPinata/DIY-Mic
- 3D-printable capsule mount (Thingiverse): https://www.thingiverse.com/thing:2541735

### Datasheets

- THAT1512 / 1510: https://www.thatcorp.com/datashts/THAT_1510-1512_Datasheet.pdf
- JLI-2555 (EU): https://micbooster.com/jli-microphones/262-jli2555.html
- JLI-2555BXZ3-GP (US): https://www.jlielectronics.com/microphone-capsules/jli-2555bxz3-gp/

---

## Cross-build notes

- Same circuit; pick the body style you prefer.
- The **CM108B dongle is the bottleneck** for noise. Spend on a Behringer LINE 2 USB if budget allows.
- INA217 substitution is now well-trodden — don't burn time chasing a real THAT1512 if a known-good one isn't available locally.
- Confirmed JFET subs: J111, J112, J113, J304.
- Op-amp variant front-end (OPA2134 + LSK170/2SK208) exists on GroupDIY threads if you want to skip the JFET pair.

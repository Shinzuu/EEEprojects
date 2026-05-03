# USB Mic v3 — Canonical Wiring List

**Print this on paper. Tick off as you build. Build top-to-bottom in order.**

Companion to `schematic_v3.html` (design reference) and `enclosure_planning.md` (mechanical).

---

## Conventions

- Breadboard: 830-point full-size, columns numbered 1–63, rows a-b-c-d-e (top half) + f-g-h-i-j (bottom half). Center gap between rows e and f.
- Power rails: top outer = **+5V**, top inner = **AGND**, bottom inner = **AGND** (jumpered to top inner), bottom outer = **−5V**.
- Wire color (matches wire colors you should physically use):
  - **Red** = +5V
  - **Black** = AGND
  - **Blue** = −5V
  - **Yellow** = audio signal
  - **White** = sidechain control voltage
  - **Green** = clean ground from chassis / shield
- "Col X row Y" means a single hole on the breadboard. Example: "col 9 row b" = the hole in column 9, row b.
- Resistor leads bent 90°, body laid flat, leads spaced for the column gap (typically 5 columns / 5 holes = ~25 mm).

---

## STAGE 0 — Power supply (build first, verify before anything else)

### Off-board: USB → DC-DC modules

You'll build the PSU on a small piece of perfboard or a separate region of the breadboard. Recommend perfboard for this — the B0505 modules have stiff pins that wear out breadboard contacts.

```
[USB-A male connector]
   pin 1 (VBUS, +5V) → red wire to PSU board
   pin 4 (GND)       → black wire to PSU board
   (pins 2, 3 = data, ignore for now — only used by the dongle later)

[PSU board / breadboard region — keep separate from audio rails]

  Module A (B0505S-1W):
    pin 1 (Vin+)  ← from USB +5V wire (red)
    pin 2 (Vin−)  ← from USB GND wire (black)
    pin 3 (Vout−) → to AGND rail of MAIN audio breadboard
    pin 4 (Vout+) → to +5V rail of MAIN audio breadboard

  Module B (B0505S-1W):
    pin 1 (Vin+)  ← from USB +5V wire (shared)
    pin 2 (Vin−)  ← from USB GND wire (shared)
    pin 3 (Vout−) → to −5V rail of MAIN audio breadboard
    pin 4 (Vout+) → to AGND rail of MAIN audio breadboard  (TIES TO MODULE A's Vout−)
```

⚠ **Module pinout varies by manufacturer.** Always check the bottom-print or datasheet of the specific B0505S-1W you have. A common pinout has Vin+ on pin 1 (marked with dot), but counterfeits exist. **If unsure: power one module from USB alone, measure Vout pins with DMM. Output pin reading +5V = Vout+, the other = Vout−.**

### Main audio breadboard — power rails

| What | Where | Wire color |
|---|---|---|
| Top outer rail (red side) | from Module A Vout+ | red |
| Top inner rail (blue side) | from Module A Vout− = AGND | black |
| Bottom inner rail (red side) | from Module B Vout+ = AGND | black |
| Bottom outer rail (blue side) | from Module B Vout− | blue |
| Jumper col 1 to col 60 on TOP outer rail (if rail breaks at mid-board) | breadboard | red |
| Jumper col 1 to col 60 on BOTTOM outer rail | breadboard | blue |
| Jumper TOP inner (AGND) to BOTTOM inner (AGND) | breadboard, near col 30 | black |

### Stage 0 components on main breadboard

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| C1 | 100 µF / 25V electrolytic | +5V rail (col 1) | AGND rail (col 1) | LONG lead = +. Body roughly above col 1. |
| C2 | 100 nF ceramic | +5V rail (col 3) | AGND rail (col 3) | Non-polar, either way. |
| R_dummy_pos | 330 Ω 1/4W | +5V rail (col 4) | AGND rail (col 4) | Minimum-load resistor for Module A regulation. |
| C3 | 100 µF / 25V electrolytic | −5V rail (col 1) | AGND rail (col 1) | LONG lead = + on AGND side (because rail is negative). |
| C4 | 100 nF ceramic | −5V rail (col 3) | AGND rail (col 3) | |
| R_dummy_neg | 330 Ω 1/4W | −5V rail (col 4) | AGND rail (col 4) | Minimum-load for Module B. |

### Stage 0 verification (power-up checklist)

⚠ **Audio dongle is NOT plugged in yet.** Just USB power.

1. Visual inspection: every wire matches the table. Phone photo for record.
2. Plug USB. Listen — modules should be silent (no whine).
3. DMM, DC voltage, 20V range:
   - [ ] Top outer rail (red) to top inner rail (AGND): **+5.0 ± 0.3 V**
   - [ ] Bottom outer rail (blue) to bottom inner rail (AGND): **−5.0 ± 0.3 V**
   - [ ] Top inner rail (AGND) to bottom inner rail (AGND): **0 V** (continuity confirms the jumper)
   - [ ] Top outer rail to bottom outer rail: **+10.0 ± 0.5 V**
4. Touch each module after 1 minute. **Warm**, not hot. Hot = short. Unplug, find short.
5. If any rail reads ≥ 6V: dummy load missing. Recheck.
6. If any rail reads ≤ 4V: load too heavy or module faulty.

✅ **PASS:** all 4 voltages in range, modules warm, no whine. Move to Stage 1.
❌ **FAIL:** stop. Debug Stage 0 before adding anything.

---

## STAGE 1 — JFET buffer + capsule

⚠ Keep dongle UNPLUGGED. We'll connect at end of Stage 1 verification.

### Components

Q1 = 2N3819 N-channel JFET, TO-92 package.

**Verify pinout BEFORE inserting:** DMM in diode mode. Place black probe on suspected gate, red on suspected drain or source — should read ~0.5–0.7 V drop. Reverse: open. Standard TO-92 pinout (flat side facing you, leads down): **left = Drain, center = Source, right = Gate**. Some clones are S-G-D — verify before powering.

### Wiring table

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| (capsule) | 20 mm raw back-electret | + terminal: shielded wire to col 8 row a | − terminal: shielded wire to AGND rail | Wire is twisted pair inside copper desolder braid. Braid grounded at capsule end ONLY. |
| R3 | 10 MΩ 1/4W | col 8 row b | col 9 row b | Resistor body horizontal, between cols 8 and 9. |
| R4 | 10 MΩ 1/4W | col 9 row c | AGND rail (jumper) | Body horizontal. Other end goes through breadboard to AGND. |
| Jumper | wire | col 9 row b | col 9 row c | Internal connection between R3-bottom and R4-top (shared node). |
| C_boot | 1 µF film cap (or 22 µF NP electro) | col 9 row b (R3/R4 junction) | col 14 row a (Q1 source) | Body horizontal across the gap. |
| Q1 | 2N3819 | Drain → col 13 row a | (see next 2 rows) | Insert with leads in row a, body sticking up. |
| Q1 (continued) | (same part) | Source → col 14 row a | Gate → col 15 row a | All three leads in row a, columns 13, 14, 15. |
| Jumper | wire | col 8 row a (capsule + signal) | col 15 row a (Q1 gate) | Single wire connecting capsule to gate. |
| R1 | 4.7 kΩ 1/4W | +5V rail (col 13) | col 13 row a (Q1 drain) | Drain load resistor. Body vertical from rail to row a. |
| R2 | 4.7 kΩ 1/4W | col 14 row a (Q1 source) | AGND rail (col 14) | **For Stage 1 single-supply test, R2 goes to AGND, NOT to −5V.** Will be moved to −5V when full ±5V circuit is online (Stage 3+). |
| C7 | 1 µF film cap | col 14 row a (Q1 source) | col 18 row a (output node) | Coupling cap to next stage. Body horizontal. |
| (output flying wire) | wire | col 18 row a (output) | dongle mic-in tip | Short, ≤ 20 cm. Soldered to dongle's mic-in pad or 3.5 mm jack tip. |
| (output GND wire) | wire | AGND rail | dongle mic-in sleeve / GND pad | Defines the single-point AGND ↔ USB GND tie via dongle's chip. |

### Stage 1 verification

⚠ **Now plug USB and the dongle.** Open Audacity (or `arecord -l` in terminal first to confirm dongle enumerated).

1. DMM, DC voltage, 20V range:
   - [ ] Q1 drain (col 13 row a): **+3 to +5 V** (target ~+4.5 V)
   - [ ] Q1 source (col 14 row a): **+0.3 to +1.5 V** (target ~+0.5 V)
   - [ ] Q1 gate (col 15 row a): **0 V ± 100 mV**
2. Connect to dongle. In Audacity, set input device to dongle. Input level meter visible.
3. Tap the capsule lightly with a finger:
   - [ ] Visible amplitude spike in Audacity input meter.
4. Speak into capsule from 10 cm:
   - [ ] Voice clearly audible in headphones / playback.
   - [ ] Voice is recognizable (not distorted, not buried in noise).
5. Hold breath, mic in quiet position:
   - [ ] Noise floor is lower than what dongle alone produces with mic-input shorted (test by unplugging capsule wire and shorting dongle's mic-in to GND with a paper clip).

✅ **PASS:** voice works, noise floor reasonable. **You now have a working USB microphone.** Crude — no preamp, no HPF, no gate — but functional. Move to Stage 2.

❌ **FAIL:**
- Vd ≈ +5 V (no drop): Q1 not conducting. Check pinout (D-S-G vs S-G-D), try another sample.
- Vs ≈ 0 V: Q1 gate not biased — check R3/R4 not open, capsule + wire reaches col 8 row a.
- Vs > 2 V: high-Idss sample. Either accept it (still works) or raise R2 to 10 k.
- Audio works but very noisy: gate node has flux residue. Clean with isopropyl. Or shorten capsule wires.
- No audio: capsule polarity reversed. Swap + and −.

---

## STAGE 2 — High-pass filter (100 Hz, Sallen-Key)

Only build after Stage 1 passes.

### Components

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| C20 | 100 nF ceramic | col 18 row a (Stage 1 output) | col 20 row a | Filter cap 1. |
| C21 | 100 nF ceramic | col 20 row a | col 22 row a | Filter cap 2. |
| R20 | 16 kΩ 1/4W (or 15 k) | col 20 row a | AGND rail (col 20) | First R-to-ground. |
| R21 | 16 kΩ 1/4W | col 22 row a | col 26 row a (NE5532 IC1 pin 1, output) | Feedback path of Sallen-Key topology. |
| Jumper | wire | col 22 row a | col 25 row a (NE5532 pin 3, +in_A) | NE5532's non-inverting input. |
| Jumper | wire | col 26 row a (pin 1, output) | col 27 row a (pin 2, −in_A) | Unity-gain feedback (output direct to inverting input). |

### NE5532 IC1 placement

DIP-8 chip straddles the center gap. Pin 1 marker (small dot or notch) faces left. **Insert with power off.**

Pinout (top view, notch on left):

```
                   ┌──── notch ────┐
              1 ── │ ●             │ ── 8
              2 ── │               │ ── 7
              3 ── │               │ ── 6
              4 ── │               │ ── 5
                   └───────────────┘
```

Pin 1 = Output A, Pin 2 = −in A, Pin 3 = +in A, Pin 4 = V−, Pin 5 = +in B, Pin 6 = −in B, Pin 7 = Output B, Pin 8 = V+.

| IC pin | Goes to | Wire color |
|---|---|---|
| 1 (Out A) | col 26 row a (HPF output) | yellow |
| 2 (−in A) | col 27 row a, jumpered to col 26 row a | yellow |
| 3 (+in A) | col 25 row a, jumpered from C21/R20 junction | yellow |
| 4 (V−) | −5V rail (jumper from col 28 to bottom outer rail) | blue |
| 5 (+in B) | (Stage 3 will fill) | — |
| 6 (−in B) | (Stage 3 will fill) | — |
| 7 (Out B) | (Stage 3 will fill) | — |
| 8 (V+) | +5V rail (jumper from col 25 to top outer rail) | red |

### IC1 decoupling (CRITICAL — close to chip)

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| C_dec1 | 100 nF ceramic | IC1 pin 8 (col 25 in row a or jumper) | AGND rail | Within 10 mm of pin 8. Short leads. |
| C_dec2 | 47 µF / 25V electrolytic | IC1 pin 8 | AGND rail | Body close to pin 8 too. |
| C_dec3 | 100 nF ceramic | IC1 pin 4 | AGND rail | Within 10 mm of pin 4. |
| C_dec4 | 47 µF / 25V electrolytic | IC1 pin 4 | AGND rail | Body close to pin 4. |

### Stage 2 verification

1. DMM check first:
   - [ ] IC1 pin 8 (V+) reads +5.0 ± 0.3 V
   - [ ] IC1 pin 4 (V−) reads −5.0 ± 0.3 V
   - [ ] IC1 pin 1 (Out A) reads ~0 V DC (within ± 50 mV)
2. Frequency sweep (audio test). In Audacity, generate a sine sweep 30 Hz → 1 kHz at constant amplitude. Play through a small speaker placed near the capsule. Record the result, look at the spectrum:
   - [ ] At 30 Hz, recorded level is ≥ −15 dB below the 1 kHz level.
   - [ ] At 100 Hz, recorded level is roughly −3 dB below 1 kHz.
   - [ ] Above 200 Hz, response is flat (within ±2 dB).
3. Subjective: listen to recording with traffic outside the window:
   - [ ] Low-frequency rumble is noticeably reduced compared to Stage 1 recording.

✅ **PASS:** HPF working as designed.
❌ **FAIL:**
- Voice sounds tinny: HPF cutoff too high. Re-measure R20, R21 — if they're 1.6 k instead of 16 k, fc moved to 1 kHz.
- No frequency rolloff visible: signal not going through HPF — check jumpers, especially "col 22 row a → col 25 row a" connection.
- Loud whistle / oscillation: missing decoupling. Add 100 nF directly at pins 4 and 8.

---

## STAGE 3 — Preamp (NE5532, fixed gain first build)

For first build, **use a fixed R8 instead of the rotary**. Once everything works, you can swap R8 for the rotary switch later.

### Components

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| R5 | 10 kΩ 1/4W | col 26 row a (HPF output) | col 31 row a | Series input resistor. |
| R6 | 100 kΩ 1/4W | col 31 row a | AGND rail (col 31) | Input bias to ground (defines DC reference). |
| R8 | 470 Ω 1/4W (fixed) | col 32 row e (IC1 pin 6, −in B) | AGND rail (col 32) | Sets gain = 1 + R8/R5 = 1 + 22.34 = ~+27 dB. |
| Jumper | wire | col 31 row a (R5/R6 node) | col 32 row e (IC1 pin 6, −in B) | Feeds inverting input. |
| (Wait, that's wrong — non-inverting topology, R8 goes between output and -in, R5 goes from -in to GND. Let me redo this.) | | | | See note below. |

**Correction — non-inverting amplifier topology:**

```
   in (from HPF) ──► IC1 pin 5 (+in B)
                                          
   IC1 pin 7 (Out B) ──► R8 (470Ω) ──► IC1 pin 6 (−in B) ──► R5 (10k) ──► AGND
                                                                              │
                                                            Gain = 1 + R8/R5
                                                                  = 1 + 470/10000
                                                                  ≈ 1.05  ❌ wrong way!
```

The gain formula is `1 + R_feedback / R_ground`. For +27 dB (factor ~22.4), we need `R_fb / R_gnd = 21.4`. So if R5 = 470 Ω (between -in and GND) then R8 = 10 kΩ (between output and -in). Let me redo the table correctly.

### Stage 3 components (corrected)

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| C_in | 1 µF film cap | col 26 row a (HPF output) | col 30 row a | DC blocking between HPF and preamp. |
| R_bias | 100 kΩ 1/4W | col 30 row a | AGND rail | Input bias path for non-inverting input. |
| Jumper | wire | col 30 row a | col 33 row e (IC1 pin 5, +in B) | Sends signal to non-inverting input. |
| R_gnd | 470 Ω 1/4W | col 32 row e (IC1 pin 6, −in B) | AGND rail (col 32) | "Ground leg" of non-inverting amp. Smaller value = more gain. |
| R_fb | 10 kΩ 1/4W (fixed for v1 build) | col 32 row e (IC1 pin 6, −in B) | col 31 row e (IC1 pin 7, Out B) | Feedback resistor. Gain = 1 + R_fb/R_gnd = 1 + 10000/470 = 22.3× = +27 dB. |
| C_rfi | 100 pF ceramic | parallel to R_fb (same nodes) | (same) | Rolls off above 80 kHz. Prevents RFI demodulation. |
| (output flying wire to Stage 4) | wire | col 31 row e (IC1 pin 7, Out B) | (will go to Stage 4 input) | Yellow. |

### Stage 3 verification

1. DMM:
   - [ ] IC1 pin 7 (Out B) reads ~0 V DC ± 50 mV
2. Audio test:
   - [ ] Speak at 15 cm from capsule. Voice should be much louder in playback than Stage 2 result.
   - [ ] No clipping (waveform clean, not flat-topped) at normal speech volume.
   - [ ] Noise floor in silence: drop −10 to −20 dB below Stage 2 (preamp lifts signal vs digitizer noise).
3. Optional: test at full speech volume. If clipping occurs, reduce R_fb to 4.7 k (gain = +21 dB) and rebuild.

✅ **PASS:** voice loud and clean.
❌ **FAIL:**
- Output stuck at +5V or −5V (DC offset): bias network wrong. Re-check that pin 5 has a 100k bias path to AGND.
- Loud whistle: oscillation. Verify R_fb close to chip (within 20 mm), C_rfi installed, decoupling caps in place.
- Distortion: gain too high. Lower R_fb.

---

## STAGE 4 — VCA noise gate (JFET shunt)

Only after Stage 3 passes. This is the most fragile stage. Build slowly.

### Components

Q2 = 2N3819 (second one). Same pinout verification as Q1.

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| R10 | 100 kΩ 1/4W | col 31 row e (Stage 3 output) | col 41 row a | Series resistor — forms divider with Q2 channel. |
| Q2 | 2N3819 | Drain → col 41 row a | (next 2 rows) | TO-92, leads in row a. |
| Q2 (continued) | (same) | Source → col 42 row a | Gate → col 43 row a | |
| Jumper | wire | col 42 row a (Q2 source) | AGND rail | Source tied to AGND. |
| R12 | 100 kΩ 1/4W | col 41 row a (Q2 drain) | col 43 row a (Q2 gate) | Linearization feedback — this is what makes the JFET act linearly as a VCR. |
| R11 | 100 kΩ 1/4W | col 43 row a (Q2 gate) | col 47 row a (sidechain Vc input) | Series resistance to gate from sidechain control voltage. |
| (audio output wire) | wire | col 41 row a (gate output node, also Q2 drain) | Stage 6 input (col 56 row e) | Yellow. This is the audio AFTER the gate. |

### Stage 4 verification — without sidechain yet

For now, jumper the sidechain Vc input (col 47 row a) to one of two positions to test gate behavior:

**Test A: Vc = −5V (gate forced FULLY OPEN, audio passes):**
- [ ] Jumper col 47 row a directly to −5V rail.
- [ ] Audio at gate output ≈ audio at gate input. Negligible loss.
- [ ] Speak — voice still works, comparable level to Stage 3.

**Test B: Vc = 0V (gate forced FULLY CLOSED, audio shorted):**
- [ ] Jumper col 47 row a directly to AGND.
- [ ] Audio at gate output drops by ≥ 40 dB compared to Test A.
- [ ] Speak loudly — audio is heavily attenuated, mostly silence.

If both tests pass, the gate hardware is functional. Sidechain (Stage 5) just provides Vc dynamically.

---

## STAGE 5 — Sidechain (envelope follower + comparator)

This is the most complex stage. Build piece by piece.

### Tap point

Audio is tapped from **Stage 3 output** (col 31 row e — same node feeding Stage 4 input).

### Components

IC2 = second NE5532 chip. Place in cols 48–55, straddling center gap.

#### Sub-stage 5A: Half-wave gain stage (×11)

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| C30 | 1 µF film cap | col 31 row e (audio tap) | col 36 row e | DC block. |
| R30 | 10 kΩ 1/4W | col 36 row e | col 48 row e (IC2 pin 6, −in A) | Inverting input feed. |
| R30b | 100 kΩ 1/4W | col 36 row e | AGND rail | Bias to ground. |
| R31 | 10 kΩ 1/4W | col 48 row e (IC2 pin 6) | col 49 row e (IC2 pin 7, Out A) | Feedback (gain = R31/R30 = 1× — wait, for ×11 we need R31 = 110k. Use 100 k.) |
| (correction) R31 | 100 kΩ 1/4W | col 48 row e | col 49 row e | Gain = 100 / 10 = 10× (close to 11). Acceptable. |
| (jumper) | wire | IC2 pin 5 (+in A) | AGND rail | Non-inverting input grounded. |

#### Sub-stage 5B: Full-wave rectifier (BC547 pair, 1N4007 diodes)

This converts AC audio envelope into DC. Two BC547 (Q3, Q4) form an absolute-value circuit.

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| Q3 | BC547B | Collector → col 49 row e (Out A) via D1 | Emitter → col 51 row a | Active during positive half-cycles. |
| Q3 (continued) | | Base → col 50 row a (jumper to Q4 base for matched pair) | | |
| D1 | 1N4007 | Anode → col 49 row e | Cathode → Q3 collector | Steers positive half-cycles. |
| Q4 | BC547B | Collector → col 49 row e via D2 | Emitter → col 51 row a (same as Q3) | Active during negative half-cycles. |
| D2 | 1N4007 | Cathode → col 49 row e | Anode → Q4 collector | Steers negative half-cycles. |
| (jumper) | wire | Q3 base | Q4 base | Both bases tied. |
| (bias) | wire | bases | AGND through 100 k | Bases at GND, transistors operate in low-current rectifier mode. |
| C31 | 4.7 µF / 25V (or 47 µF substitute) | col 51 row a (combined emitter) | AGND rail | Smoothing — DC envelope appears here. |

⚠ **This rectifier topology is non-trivial.** If you're not comfortable with it, simpler alternative: **two 1N4148 diodes in a precision rectifier around the NE5532's other half** (op-amp full-wave rectifier). Standard textbook circuit. Slightly more parts but easier to debug. Mention if you want me to redo this section with the op-amp version.

#### Sub-stage 5C: Comparator + envelope buffer

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| (jumper) | wire | col 51 row a (envelope DC) | IC2 pin 2 (−in B, comparator input) | NE5532 pin 2 — wait, that's IC1. Use IC2 pin 2 (−in B of second chip). |
| VR1 wiper | 100 kΩ pot | wiper → IC2 pin 3 (+in B) | endpoints → −5V and AGND | Threshold control. Wiper voltage sets when comparator flips. |
| (output) | wire | IC2 pin 1 (Out B, comparator output) | col 47 row a via C32 + R22 | Goes to gate Vc through release time-constant. |
| R22 | 10 kΩ 1/4W | IC2 pin 1 | C32 | Release-time R. |
| C32 | 10 µF / 25V (or 47 µF) | R22 other end | AGND rail | C charges/discharges through R22 for envelope shape. |
| (Vc out) | wire | C32 + side | col 47 row a (Stage 4 gate Vc) | This is the control voltage going to the JFET VCA. |
| D3 | 1N4148 | parallel to R22, anode → comparator output side | cathode → C32 side | **Asymmetric attack/release.** Diode shorts R22 during fast attack (envelope rising), disabled during slow release. |

### Stage 5 verification

1. DMM at IC2 pin 1 (comparator output) while speaking:
   - [ ] Output swings between roughly +4 V (silence, gate should close) and −4 V (speech, gate should open). Or reverse, depending on comparator polarity.
   - [ ] Adjust VR1 (threshold pot) — verify the swing transition point moves with the pot.
2. With Stage 4 connected to receive Vc from Stage 5:
   - [ ] When you speak: audio at gate output is loud (gate open).
   - [ ] When you stop speaking and wait ~150 ms: audio at gate output drops by ≥ 30 dB (gate closed).
   - [ ] No clicks or pops at gate transitions (asymmetric attack/release smooths it).
3. Tune VR1: set threshold so quiet ambient noise stays gated, normal speech opens cleanly.

✅ **PASS:** gate works.
❌ **FAIL:**
- Gate never opens: threshold too high, OR comparator polarity inverted (swap pins 2 and 3 of IC2's B half).
- Gate never closes: threshold too low, OR rectifier not producing DC envelope (probe col 51 row a — should see DC voltage proportional to recent audio loudness).
- Gate chatters: release time too short. Increase C32.

---

## STAGE 6 — Output buffer + mute switch

Final stage before dongle.

### Components

IC3 = third NE5532 chip (or use spare half of IC1/IC2 — whichever has free halves).

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| (input) | wire | col 41 row a (Stage 4 audio output) | IC3 pin 3 (+in A) | Yellow. |
| (feedback) | wire | IC3 pin 1 (Out A) | IC3 pin 2 (−in A) | Unity-gain follower. |
| R40 | 220 Ω 1/4W (or 330 Ω from cart) | IC3 pin 1 (Out A) | (next node — switch) | Output series resistor. |
| (audio node) | flying wire pad | between R40 and switch | | Mute switch taps here. |
| SW1 | SPST latching push-button | terminal A → audio node | terminal B → AGND | When pressed: shorts audio to AGND. **Latching** = stays pressed. |
| C40 | 22 µF / 50V NP electrolytic (or 47 µF electro substitute) | audio node | dongle mic-in tip | Output coupling. |
| (output) | wire | C40 dongle side | dongle mic-in tip / 3.5 mm tip | Yellow. |
| (output GND) | wire | AGND rail | dongle mic-in sleeve | Single-point USB GND ↔ AGND tie via dongle's chip. |

### Mute LED indicators

| Ref | Part | Lead 1 → | Lead 2 → | Notes |
|---|---|---|---|---|
| R_red | 1 kΩ 1/4W | +5V rail | LED_red anode | Current limit, ~3 mA. |
| LED_red | 3 mm red LED | anode → R_red | cathode → SW1 terminal A (audio node side) | When SW1 closed, cathode reaches AGND, LED lights. When open, no path. |
| R_grn | 1 kΩ 1/4W | +5V rail | LED_grn anode | Always-on power indicator. |
| LED_grn | 3 mm green LED | anode → R_grn | cathode → AGND rail | Always lit when powered. |

⚠ **The red LED's cathode shares the same node as the audio output going to SW1.** This is the "shared SPST contact" trick: when SW1 closes, both the audio gets shorted to AGND AND the red LED gets a path to AGND.

### Stage 6 verification

1. DMM at IC3 pin 1: ~0 V DC ± 50 mV.
2. Speak — voice clean in dongle / Audacity playback.
3. Press SW1:
   - [ ] Audio goes silent in playback.
   - [ ] Red LED lights up.
   - [ ] Green LED stays on.
   - [ ] No "click" sound when pressing or releasing (asymmetric charge time of C40 is slow enough).
4. Press SW1 again to release:
   - [ ] Audio returns within ~50 ms.
   - [ ] Red LED off.

✅ **PASS:** complete v3 mic working on breadboard.

---

## After breadboard works — transition to perfboard

This is the milestone where ~80% of past builds died for you. Discipline:

1. **Photograph the working breadboard from 4 angles.**
2. **Solder ONE STAGE AT A TIME onto perfboard.** Validate after each stage transfers. Do NOT rip the whole breadboard apart and rebuild on perfboard in one go.
3. **Heatsink JFET and IC leads** with needle-nose pliers while soldering. 60/40 leaded solder, 350 °C max iron, < 3 seconds per joint.
4. **Decoupling caps go right at the IC pins**, not on power rails. Short leads.
5. **Run all power and ground as a star topology** to one central AGND junction. No daisy-chained grounds.
6. **Final verification on perfboard repeats the breadboard verification checklist** for each stage.

---

## Final BOM (with substitutions for parts NOT in cart)

| Ref | Spec | In cart? | Substitution if not |
|---|---|---|---|
| Q1, Q2 | 2N3819 | ✓ (8) | — |
| Q3, Q4 | BC547B | ✓ (12) | — |
| IC1, IC2, IC3 | NE5532 | ✓ (4) | — |
| D1, D2 | 1N4007 | ✓ (12) | — |
| D3 | 1N4148 | ✓ (36) | — |
| 100 nF ceramic | C0G/X7R | ✓ (36) | — |
| 100 µF / 25V electro | rail caps | ? — check stock | sub: 47 µF if needed |
| 47 µF / 25V electro | decoupling | ✓ (12) | — |
| 22 µF NP electro | C40 output | ✗ | sub: 47 µF normal electro (slight DC offset, acceptable) |
| 10 µF, 4.7 µF electro | sidechain | ✗ | sub: 47 µF, adjust R values to compensate time constants |
| 1 µF film cap | coupling | ✗ | sub: 22 µF NP electro, OR 10× 100nF mylar in parallel |
| 100 pF ceramic | RFI | ? | should be in cart |
| 1 kΩ 1/4W | LED current limit + others | ✓ (50) | — |
| 4.7 kΩ | R1, R2 | ✗ | sub: 1k + 3.3k (need 3.3k from another order) OR 5× 1k in parallel from row a — no wait, 5× 1k in parallel = 200 Ω, wrong. Need 4.7k actual. **Add to next order.** |
| 10 kΩ | R5, R31, R22, R_fb | ✗ | sub: 10× 1k in series. Ugly but works. |
| 16 kΩ | HPF R20, R21 | ✗ | sub: 16× 1k or 1k + 15k |
| 22 kΩ | sidechain | ✗ | 22× 1k or 10k + 12k |
| 100 kΩ | many places | ✗ | sub: 1× 330k //  330k // 330k = 110k (close enough for this) OR 100× 1k |
| 470 Ω | R_gnd Stage 3 | ✗ | sub: 1k // 1k = 500 Ω (close enough) OR 330R + 1k // ... |
| 220 Ω | R40 output | ✗ | sub: 330 Ω (cart). Slightly higher Zout, no audible effect. |
| 10 MΩ | R3, R4 | ✗ | **MANDATORY for Stage 1. Cannot be synthesized from cart values. ORDER 4 OF THESE.** |
| VR1 100 kΩ log pot | threshold | ✗ | source separately ~15 BDT, OR use fixed mid-threshold R |
| RS26 12-pos rotary | R8 gain | ✗ | source separately, OR fixed gain R_fb (current build uses fixed) |
| SW1 SPST latching | mute | ✗ | source separately, ~5 BDT slide switch fine. Or salvage from old electronics. |
| 3 mm LED red, green | indicators | ✓ | — |
| 3.5 mm TRS jack | output | ✗ | OR solder cable directly between PCB and dongle |
| USB-C female breakout | input | you said you have it | — |

**Minimum additional order to make v3 buildable:**
- 4× 10 MΩ resistor — mandatory
- 1× E12 metal-film resistor kit (covers 470Ω–100kΩ values) — strongly recommended
- 1× 100 kΩ log pot — for threshold
- 1× SPST or DPDT latching switch — for mute
- 2× 22 µF NP electrolytic, 1× 4.7 µF, 1× 10 µF (or sub 47 µF for all) — sidechain + output

Estimated cost: **~150–200 BDT** at udvabony or local market.

---

## Notes from the canonical wiring sheet author

This document is the build reference. Other documents:
- `schematic_v3.html` — design reference (theory, why each stage exists, math).
- `enclosure_planning.md` — mechanical (after PCB works).
- `breadboard_layout.html` — earlier draft, less detailed than this sheet — superseded.

If a wire isn't in a table here, it's not in the circuit. If you see something missing, say so and I'll add it.

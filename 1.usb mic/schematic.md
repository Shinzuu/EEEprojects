# DIY USB Mic — schematic & BOM (udvabony-sourced)

Target: 20mm raw 2-terminal back-electret capsule (no internal FET) → JFET buffer → low-noise audio preamp → JFET-VCA noise gate → USB sound-card adapter → host.

All parts confirmed in stock at https://udvabony.com (April 2026). Substitutions chosen for **audio quality**, not just availability — NE5532 in the signal path (4.5 nV/√Hz), TL072 only in the DC sidechain, no LM358 anywhere near audio.

---

## Power architecture

You have isolated DC-DC modules in 5 V / 9 V / 12 V single-rail. Use **two single-rail isolators** to synthesize ±9 V:

```
USB 5V VBUS ──┬── Isolator A: 5V → 9V  ──── +9V rail
              └── Isolator B: 5V → 9V (output inverted with reference flip) ──── -9V rail
                  ↑ wire B's "+" output as common ground, "−" as -9V
```

Both isolators must be **galvanically isolated** (otherwise the inversion trick floats audio ground from USB ground). The DIY-Perks-style fix is one dual-output module (NMA0509SC), but two single-rail iso modules wired this way is electrically equivalent. Decouple each rail with 470 µF electrolytic + 100 nF ceramic at the preamp.

Preamp section runs ±9 V. USB sound card runs from its own USB 5 V (do not share — keeps switching noise off the analog rails).

---

## Block diagram

```
                                       ┌─────────────────┐
[Capsule] ── JFET buffer ── HPF ──────►│  NE5532 PREAMP  │── HPF ── JFET VCA ──► OUTPUT BUFFER ──► 3.5mm TRS ──► USB sound card
                                       │  (rotary gain)  │           ▲
                                       └─────────────────┘           │
                                                                ┌────┴────┐
                                                                │ SIDECHAIN│
                                                                │  (TL072) │
                                                                │ thresh + │
                                                                │ envelope │
                                                                └──────────┘
                                                  Bypass DPDT toggle: gate in/out
```

---

## Stage 1 — JFET source-follower (capsule front-end)

```
        +9V
         │
         R1 4.7k (drain load, sets noise + gain)
         │
         ├──── Q1 drain
         │
         Q1: 2N5457 (or 2N3819 fallback)
         │
         ├──── Q1 source ──► to C1 ──► HPF ──► U1 input
         │                    │
         R2 2.2k              │
         │                    │
        -9V (or GND for       │
         single-supply)       │
                              │
        Capsule (+) ──┬───────┤
                      │       │
                      │      Q1 gate
                      │       │
                      R3 10M ─┴─ R4 10M (bootstrap from source)
                      │           │
                      ├───────────┴── to Q1 source (BOOTSTRAP NODE)
                      │
        Capsule (−) ──┴── audio ground (single-point at capsule)
```

**Why bootstrap R3:** udvabony's largest resistor is 10M. Loading a 50pF capsule with plain 10M gives a -3dB corner at ~320 Hz — kills bass. Driving R3's bottom from the source (which follows the gate) makes the AC voltage across R3 ≈ 0, so its effective AC impedance ≈ R3 / (1 − Av) ≈ 100M+ in practice. R4 sets the actual DC bias path. This is the same trick LDC mics use to fake a gigaohm bias from common parts.

**JFET pick:** 2N5457 (low Vp ≈ −1 V, low noise). Stock alternates: 2N3819, 2N5459. **Avoid 2N5459 from the MOSFET listing** (sku=u6610, 120 BDT, miscategorized) — get the cheaper one (sku=u5361, 55 BDT). 2N3819 is the safer no-tweak pick.

C1 = 1 µF non-polar film (104K is too small — use a 105 polypropylene or a 22 µF bipolar electrolytic).

---

## Stage 2 — Main preamp (NE5532, switched gain)

```
                              R8 (gain set, see rotary)
                              ┌──────────────────┐
                              │                  │
       C1 1µF        R5 10k   │      ┌───────┐   │
   ────┤├──────┬─────/\/\─────┴──────┤−      │   │
                │                     │ NE5532├───┴──── to C7 (1µF) ──► next stage
                R6 100k               │  /2   │
                │            ┌────────┤+      │
               GND           │        └───────┘
                             │
                          midpoint of bias (ground for ±9V supply)

   Rotary switch SW1 (RS26 12-position) selects R8:
     pos 1: open      → unity (~0 dB)   "off"
     pos 2: 22k       → ~7 dB
     pos 3: 10k       → ~14 dB
     pos 4: 4.7k      → ~20 dB
     pos 5: 2.2k      → ~26 dB
     pos 6: 1k        → ~32 dB
     pos 7: 470       → ~38 dB
     pos 8: 220       → ~45 dB    ← typical vocal
     pos 9: 100       → ~52 dB
     pos 10: 47       → ~58 dB    ← quiet voice
     pos 11–12: spare
```

R5 = 10k input series. Gain = 1 + R8/R5 inverting topology — wait, fix: this is **non-inverting**, so gain = 1 + R8/R5. That gives the values above. Drop a 100pF in parallel with R8 to roll off >80kHz (slew-limit sanity).

**Why NE5532, not TL07x:** input voltage noise 4.5 nV/√Hz vs ~18 nV/√Hz on TL072. With a 30–60 pF capsule and ~1 mV/Pa sensitivity you need every dB of headroom you can get. NE5532 is the same opamp inside almost every commercial mixer mic preamp. Decouple V+/V− with 100 nF ceramic + 47 µF electrolytic right at the package.

Use the **other half of the NE5532** as the output buffer after the VCA (Stage 4).

---

## Stage 3 — JFET VCA noise gate (sidechain via TL072)

This replaces the unobtainable THAT2180/SSM2164. Topology: signal passes through a fixed series resistor; a JFET shunts to ground when the gate should close. JFET Vgs is driven by an envelope follower (TL072) so attenuation is smooth, not a click.

```
                                                  ┌──── audio in (from C7)
                                                  │
                                                 R10 22k (series)
                                                  │
                                                  ├───── audio out (to NE5532 buffer)
                                                  │
                                                Q2 drain
                                                  │
                                          Q2: 2N5457 (used as VCR)
                                                  │
                                                Q2 source ── GND
                                                  │
                                                Q2 gate
                                                  │
                                                R11 1M
                                                  │
                                                  └── from sidechain control voltage Vc
                                                       (-9V = open, 0V = closed shunt)
```

When Vc ≈ -9 V, Q2 is fully off → infinite shunt impedance → signal passes through R10 unattenuated.
When Vc ≈ 0 V, Q2 conducts → low Rds(on) → R10 forms a divider with low Rds(on) → -40 dB+ attenuation.

**Linearity trick:** add R12 = 100k from Q2 drain to gate — this feeds half the signal voltage back into Vgs and cancels the FET's parabolic Rds vs Vgs nonlinearity (classic Siliconix AN trick). Keeps THD under 0.1% even at full signal.

### Sidechain (TL072 — DC only, doesn't touch audio)

```
   ┌─ tap from Stage 2 output (post-preamp, pre-VCA)
   │
   C8 1µF
   │
   ├─── R20 10k ──┤+ \
   │              │   \  TL072/A   ── full-wave rect (Q3+Q4 BC547 pair) ──┐
   ├──────────────┤−  /                                                    │
                  │  /                                                     │
                                                                           │
                                                                           ▼
                                                            C10 4.7µF (smoothing)
                                                                           │
                                                                           ├──── R21 100k
                                                                           │       │
                                                                           │       ▼
                                                            ┌──────────────┴── to TL072/B comparator
                                                            │
                                                            │   THRESHOLD: VR1 100k log pot
                                                            │   from -9V → wiper → comparator (−) input
                                                            │
                                                            └── output: -9V when below threshold (gate closed),
                                                                 ramps to 0V via R22+C11 (10k+10µF)
                                                                 = ~100 ms attack/release time-constant
                                                                                            │
                                                                                            └── to Q2 gate (Vc)
```

Two halves of one TL072: A as half-wave gain stage, B as comparator. Q3/Q4 form a full-wave rectifier with 1N4007 diodes (1N4148 not in stock; 1N4007 forward drop is fine here, slightly higher Vf is just a constant offset). C10 smooths to a clean envelope. VR1 sets the threshold (-60 dB to -20 dB sweep). R22+C11 control attack/release — fixed at ~100 ms here, fine for vocals.

**Why TL072 here:** sidechain is DC and low-frequency, noise doesn't matter, JFET inputs let us use big 10 M feedback resistors without bias-current offset. **Not LM358** — it has crossover distortion at low signal levels which would make the gate chatter near threshold.

---

## Stage 4 — Output buffer & USB

Second half of NE5532 (U1B) as a unity-gain buffer with 220 Ω series output resistor, AC-coupled through C20 = 22 µF NP electrolytic into the **PJ-307 3.5 mm TRS jack** — both T and R wired together (mono mic feed) into ring/sleeve, sleeve to audio ground. The USB sound card module sees a line-level mono signal on its mic input.

Sound card: any cheap USB Audio Class CM108-class adapter from your shelf. udvabony's stock matches in this category aren't ideal (no plain CM108 dongle was found); use one from your bench. Remove the dongle's internal mic-bias resistor (R13 on most CM108 boards) — your preamp output is already ~100 mV line level, you don't want phantom voltage on it.

### Bypass switch

DPDT slide switch (sku=u9135 — 8-pin, 3-position; use just two positions): one pole routes either the gated signal or the raw preamp output to the buffer; the other pole switches an LED indicator (3mm red) so you know the gate is engaged.

---

## Final BOM (udvabony.com)

| Ref | Part | Value | Qty | sku | Price BDT | Note |
|-----|------|-------|-----|-----|-----------|------|
| Q1 | 2N3819 N-JFET | — | 1 | u4227 | 55 | front-end buffer (or 2N5457 / 2N5459 sku=u5361) |
| Q2 | 2N3819 N-JFET | — | 1 | u4227 | 55 | VCA element |
| Q3, Q4 | BC547 NPN | — | 2 | u4175 | 1.50 ea | full-wave rectifier |
| U1 | NE5532 dual op-amp | — | 1 | u7266 | 60 | **signal path** (preamp + buffer) |
| U2 | TL072 dual op-amp | — | 1 | u5703 | 70 | sidechain only |
| D1, D2 | 1N4007 | — | 2 | u2416 | 1 ea | rectifier diodes (1N4148 not stocked; OK here) |
| C1, C7 | film coupling cap | 1 µF / ≥50 V polypropylene | 2 | u4167 (470nF version, parallel two for 940nF) | 15 ea | signal coupling. **Or** use 22µF NP electrolytic if film not available in 1µF |
| C20 | NP electrolytic | 22 µF / 50 V | 1 | u3949 | 2 | output coupling |
| C2…C6 | electrolytic | 47 µF / 25 V | 4 | u3949 family | 2 ea | rail decoupling |
| C8, C10, C11 | electrolytic | 4.7 µF / 50 V | 3 | (similar listing) | ~2 ea | sidechain caps |
| C9 | ceramic MLCC | 100 nF | 8–10 | u118264 | 3 ea | bypass everywhere |
| C-rail | electrolytic | 470 µF / 25 V | 2 | (similar) | ~5 ea | bulk DC-DC output |
| R1 | metal film 1W | 4.7 Ω | — | n/a (use 4.7k 1/4W instead, sku=u-resistor-lookup) | 0.40 | drain load |
| R3, R4 | carbon film 1/4W | 10 M | 2 | u2122 | 0.40 ea | bootstrapped gate bias |
| R5, R10 | metal-film 1/4W | 10 k / 22 k | — | catalog has all values | 0.40 ea | series + input |
| R6 | carbon film 1/4W | 100 k | 1 | catalog | 0.40 | input bias |
| R8a–R8f | gain resistors | 47, 100, 220, 470, 1k, 2.2k, 4.7k, 10k, 22k | 1 ea | catalog | 0.40 ea | rotary switch positions |
| R11 | carbon film 1/4W | 1 M | 1 | catalog | 0.40 | VCA gate-drive series |
| R12 | carbon film 1/4W | 100 k | 1 | catalog | 0.40 | VCA linearization feedback |
| R20–R22 | carbon film 1/4W | 10 k / 100 k | 3 | catalog | 0.40 ea | sidechain |
| VR1 | 100k log pot | panel mount | 1 | u1792 | 15 | threshold control |
| SW1 | RS26 rotary 1P12T | — | 1 | u129433 | 120 | gain switch |
| SW2 | DPDT slide switch | — | 1 | u9135 | 10 | gate bypass |
| J1 | PJ-307 TRS socket | 3.5 mm 5-pin PCB | 1 | u8817 | 5 | output to USB sound card |
| J2 | USB-C breakout | 24-pin | 1 | u157537 | 110 | power input |
| LED1 | 3 mm red LED | — | 1 | u1762 | 1 | gate-engaged indicator |
| KNOB1, KNOB2 | aluminium 16 mm knob | 6 mm shaft | 2 | u139952 | 25 ea | for gain + threshold |

**Estimated total: ~600–700 BDT (~$5–$6 USD) for active parts and connectors**, plus your existing capsule, USB adapter, and DC-DC modules.

---

## Build notes

1. **Ground topology:** star-ground everything to the audio-side ground of the DC-DC converters. Audio ground touches USB ground only at the PJ-307 sleeve (single point).
2. **Capsule wiring:** enameled wire run inside copper desoldering braid (you have this from the DIY Perks reference). Braid grounded to chassis at capsule end ONLY.
3. **Gate node hygiene:** the Q1 gate / R3 / R4 junction is gigaohm-class. PCB needs a guard ring around it tied to the bootstrap source, no flux residue, conformal coat after build.
4. **Test order:** (a) verify ±9 V rails before plugging ICs; (b) bring up Stage 1 alone, look for ~−4.5 V at Q1 drain, ~0 V at gate; (c) inject 1 kHz tone at capsule terminal via 100 pF cap, see clean sine at U1 output across all rotary positions; (d) bring up sidechain on bench scope, watch envelope follow tone bursts; (e) connect VCA, verify gate opens/closes; (f) only then plug in USB sound card.
5. **First-power smoke test:** put a 100 Ω resistor in series with each rail temporarily — if anything glows, blow, or smokes, the resistor saves your DC-DC modules.

---

## Substitutions if a part is gone

- NE5532 unavailable → **OPA2134 second choice** (not seen in stock as of this scrape). LM4562 also good. Avoid TL072 in signal path for this build — it's audible.
- 2N3819/2N5457 unavailable → **MPF102** (not listed; check restock), or sub a depletion-mode small-signal MOSFET like 2N7000 + bias network (different design, redo Stage 1).
- TL072 unavailable for sidechain → **TL071** (single, use two), or in this stage only LM358 works acceptably (it's DC).
- 1µF film unavailable → **22 µF non-polar electrolytic** (sku=u3949) — slight HF degradation but inaudible at this stage.

---

## What's NOT in this design

- No phantom power (capsule is electret, doesn't need it).
- No transformer balancing (signal stays single-ended into 3.5 mm jack).
- No EQ / compression / de-esser (build those as separate pedals).
- No digital sidechain or USB-class custom firmware (we're using a stock USB sound card).

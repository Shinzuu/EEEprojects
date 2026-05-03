# USB Mic v3 — Enclosure planning notes

Companion to `schematic_v3.html` and `breadboard_layout.html`. This is **planning, not build instructions** — to be revisited once the breadboard prototype works and dimensions are known.

Material on hand: aluminium frog-spray cans (multiple), salvaged. Steel screws, tap kit, drill press, hand tools assumed available.

---

## 1. Why a frog-spray can works as a mic enclosure

Pros:
- **Already a tube.** End-address mic geometry maps directly onto the can's cylinder. No fabrication needed for the body.
- **Aluminium = excellent EMI shield** at the frequencies that matter for audio (50 Hz hum from mains, USB switching noise at ~100 kHz, dongle enumeration noise in the MHz range). Skin depth is fine for these.
- **Free / abundant.** Mistakes are cheap. Can prototype 3 enclosures, throw away 2.
- **Thin walls (~0.2 mm) easy to cut** with tin snips, hobby knife, or rotary tool. Drill cleanly with a stepped drill bit.
- **Top cap unscrews** on most spray cans → instant removable top end-cap for the capsule mount.

Cons:
- **Resonant.** Thin metal cylinders ring at 2–4 kHz when struck — that's right in the voice intelligibility band. Need internal damping.
- **Inside coating.** Most cans have epoxy lining (food-safe, also non-conductive). Sand to bare metal at the chassis-ground tie point.
- **Residue.** Propellant + product residue inside. Wash thoroughly before use — soap, hot water, dry, optional brief bake at 80 °C to drive off solvent traces.
- **Wall thickness too thin for tapped threads.** Cannot tap M3 into 0.2 mm wall. All threading must use through-bolts with nuts on the inside, or pop-rivets, or epoxy-bonded standoffs.

---

## 2. Mechanical archetype: end-address tube

Reasoning: 20 mm omni capsule + close-mic Zoom use case + cylindrical raw material → **end-address tube** is the natural geometry.

Compare alternatives:

| Archetype | Description | Fits this build? | Why / why not |
|---|---|---|---|
| End-address tube (SM58, Røde NTG) | Capsule at one end of a long cylinder, talk into the end | **YES** | Matches the can. Matches close-mic technique. Capsule shock-mount fits naturally in the cap. |
| Side-address rectangle (Blue Yeti, AKG C414) | Capsule facing sideways, large flat enclosure | No | Wrong shape for a can. Would need fabricated panels. |
| Pencil (small-diaphragm) | Capsule at one end of a thin pencil-sized tube | Sort of | Could work in a smaller can but capsule is 20 mm — needs ~30 mm internal diameter, so no thin pencil shape. |
| Boundary / surface | Flat against a desk | No | Wrong capsule for the topology. |

---

## 3. Proposed internal layout

```
     ┌─────────────────────────┐  ← top cap (unscrews)
     │  ●  ●  ●  ●  ●  ●  ●   │  ← cap face: drilled holes for sound entry
     │  ●  ●  ●  ●  ●  ●  ●   │     covered with foam (windscreen)
     │  ●  ●  ●  ●  ●  ●  ●   │
     ├─────────────────────────┤
     │   ┌──── foam grommet ──┐│  ← capsule shock-mount
     │   │                    ││
     │   │   20 mm capsule    ││
     │   │                    ││
     │   └────────────────────┘│
     │                         │
     │   ↓ shielded twisted    │
     │     pair (signal + GND) │
     │   ↓ inside copper       │
     │     desolder braid      │
     │                         │
     │   ┌─────────────────┐   │
     │   │                 │   │
     │   │  PCB / perfboard│   │  ← all electronics here
     │   │  ~6 cm × 3 cm   │   │     long axis parallel to can axis
     │   │                 │   │     so the board "slides into" the can
     │   │                 │   │
     │   │  Stage 1–6      │   │
     │   │                 │   │
     │   │  IC1 IC2 IC3    │   │
     │   │                 │   │
     │   └─────────────────┘   │
     │                         │
     │   ┌─────────────────┐   │
     │   │ B0505 #A        │   │  ← isolators, tucked at the bottom
     │   │ B0505 #B        │   │     near the USB-C jack
     │   └─────────────────┘   │
     │                         │
     ├─────────────────────────┤
     │  USB-C    headphone     │  ← bottom panel: PLASTIC, not metal
     │  female   3.5 mm jack   │     (so jack bodies don't tie USB GND
     │   ▢         ◯           │      to chassis through the chassis itself)
     └─────────────────────────┘  ← bottom cap (custom plastic disc)
```

Approximate dimensions for a typical frog-spray can:
- Length: 18 cm (capsule + PCB stack + isolator stack + jack panel)
- Outer diameter: 5 cm
- Internal diameter: 4.7 cm (after coating sanded off in places)
- PCB width target: ≤ 3.5 cm to leave room for wiring and the desolder-braid shield

---

## 4. Front-end (capsule cup, mesh, windscreen)

The top cap of the spray can becomes the **capsule cup**.

### Mesh (sound entry)

Drill or punch a regular grid of small holes in the cap face. Hole size 1.5–2 mm, spacing 3 mm center-to-center. Don't go bigger than the capsule diameter — keeps the cap structurally rigid and limits visible insect/dust intrusion.

Total open area target: ~30–40% of the cap face. Less = HF roll-off (mesh becomes acoustic resistance). More = unnecessary, and risks structural damage.

### Foam windscreen

Soft open-cell foam disc, 1 cm thick, slightly larger than the cap diameter. Press-fit inside the cap, behind the holes. Acts as:
- Plosive blocker ("p", "b" breath bursts)
- Wind / breath cooling air-flow disruptor
- Insect / dust filter

Salvage from: pop-filter foam (if any), upholstery foam, mattress topper offcuts, even kitchen sponge in a pinch.

### Capsule mounting (shock isolation)

Two tiers of isolation, both inside the cap:

1. **Foam grommet around capsule body:** wrap the 20 mm capsule barrel in 3-mm-thick foam, friction-fit into the cap. Prevents direct mechanical contact between capsule brass body and aluminium cap.

2. **Decoupling between cap and body:** when the cap screws onto the body, the threads make metal-to-metal contact. This conducts mechanical vibration. **Add a felt or rubber washer at the thread interface** — small fabric ring under the cap. Some loss of EMI continuity, but EMI is dominated by the body anyway, the cap contribution is minor.

Avoid: rigid mounting of the capsule directly to the cap. Every desk bump becomes a click in the recording.

---

## 5. Back-end (USB-C, headphone jack, GND topology)

This is where most DIY mics fail. The back panel design determines whether you get a quiet mic or a hum-loop mess.

### Use a non-conductive (plastic) back panel

Cut a circular disc from:
- Plastic project box lid
- Acrylic / polycarbonate sheet (1.5–3 mm)
- 3D-printed disc (PLA or PETG fine)
- Last resort: thick cardboard with epoxy coating

**Why plastic:** every metal-bodied connector you mount has its outer shell (jack barrel, USB shield) tied to that connector's GND. If you bolt a metal connector to a metal back panel, that GND now touches the chassis. If two connectors do this for two different GNDs (USB GND and audio GND), the chassis becomes a parasitic short between them — defeating the whole point of the isolators.

Plastic panel = each jack's GND is wired explicitly to the right place on the PCB. No accidental shorts.

### Connectors mounted on back panel

| Connector | Function | GND ties to | Notes |
|---|---|---|---|
| USB-C female | Power in (5 V from host) + data through to dongle | USB GND (NOT audio GND) | Use a USB-C breakout board with through-hole pads. Solder VBUS, GND, D+, D− to the dongle. The dongle is the device, USB-C is just the physical connector. |
| 3.5 mm TRS (headphone out) | Listen to dongle's headphone output | Dongle's headphone-out GND (= USB GND) | This is for monitoring. The dongle's analog output. Plastic-bodied jack mandatory; metal would short to chassis. |
| (optional) Mute switch | Hardware mute | Audio GND | Push-button cuts the signal at preamp output. SPST momentary or latching, your choice. |
| (optional) LED | Power indicator | Audio +5V → R → AGND | 1 kΩ in series with red LED, ~3 mA. Visible through a small hole in the back panel. |

**No** input jacks on this build. The only audio input is the internal capsule.

### Where the dongle lives

**Inside the can, on the PCB.** The dongle is just a small board with CM108 (or equivalent) + 12 MHz crystal + a few passives. Cut off its USB-A plug (or desolder), wire VBUS / GND / D+ / D− to your USB-C breakout's pads, wire the dongle's mic-in pads directly to the audio buffer's output (via the 3.5 mm sleeve-equivalent — you can skip the actual TRS connector since both ends are inside the same enclosure). Wire the dongle's headphone-out pads to the back-panel headphone jack.

This makes the headphone monitoring work seamlessly: USB host sees one device (dongle), records mic input from the dongle's analog mic-in (= your buffer output), plays back via dongle's headphone-out (= back panel jack).

### The single grounding rule (read this twice)

> The ONLY DC path between USB GND and AUDIO GND is at the dongle's internal junction where its mic-input GND meets its USB-side GND.

Everything else is isolated:
- B0505 modules: input GND ≠ output GND (transformer isolation).
- Chassis: tied to AUDIO GND only, at one point.
- Headphone jack: USB GND only (it's playback, dongle handles it).
- USB-C: USB GND only.
- Capsule shield: AUDIO GND only, at the capsule end.

Visual:

```
            [USB host]
                │
                ├── 5V VBUS
                ├── USB GND ────────────────────────────── this is "USB GND"
                │
       USB-C female (mounted on plastic panel)
                │
                ├──► dongle USB pins (VBUS, GND, D+, D−)
                │
       inside dongle
                │
                ├──► CM108 chip
                │      │
                │      └── analog GND (internal to chip, joins USB GND
                │           through chip's substrate — this is the
                │           single inter-domain tie that has to exist
                │           for the analog input to reference USB GND)
                │
                ├──► dongle mic-in pad ◄──── AUDIO buffer output
                │                              from your circuit
                │                              (through C40 22µF NP)
                │
                └──► dongle headphone-out pad ──► back-panel 3.5mm jack
                                                   tip = signal
                                                   sleeve = USB GND
                                                   
       inside the can, separately:
                                
       AUDIO GND (your circuit's reference)
                │
                ├── B0505 outputs (modules' floating outputs)
                │
                ├── all NE5532 GND pins
                │
                ├── capsule (−)
                │
                ├── chassis (one wire, one screw, to inside of can)
                │
                └── (NOT connected anywhere on the USB side except
                     through the dongle's internal chip substrate
                     mentioned above)
```

---

## 6. Resonance damping

Empty aluminium tubes ring. Fix it with internal damping.

Options (in order of effectiveness vs effort):

1. **Self-adhesive felt strip**, 5 mm wide, lining the inside of the can axially in 4 strips at 90° intervals. Cheap, fast, kills 80% of the ring.
2. **Closed-cell foam tube insert,** salvaged from packaging foam. Wrap the PCB stack in foam — kills resonance and provides shock isolation in one step.
3. **Mass loading:** stick a thin layer of constrained-layer damping material (CLD) on the inside. Overkill for this build.
4. **Lossy fluid:** fill the void with sand or bird seed. Effective but heavy and unrepairable. Skip.

Recommendation: option 2. Foam wrap around the PCB. Kills two birds.

---

## 7. Construction sequence

Approximate order, refine as you go:

1. **Empty + clean** the spray cans (multiple, for spares). Soap + water + dry + bake at 80 °C × 20 min.
2. **Cut to length.** Mark the can at ~18 cm from the screw-cap end. Cut with tin snips. File the cut edge. Optionally fold a 5 mm lip inward for safety + rigidity.
3. **Sand the inside** at the chassis-ground tie point (a 1 cm × 1 cm patch near the bottom). Confirms continuity to the AGND wire.
4. **Drill the front cap** with hole grid (mesh).
5. **Cut the back panel** from plastic (acrylic / polycarb). Drill for USB-C, 3.5mm jack, optional LED hole, optional switch hole.
6. **Mount the dongle to a small carrier board** (perfboard, 3×3 cm). Solder USB-C breakout's pads to dongle's USB pins. Confirm dongle still enumerates over a temporary USB-C cable to the host before doing anything else.
7. **Solder the audio PCB** (transferred from breadboard once Stage 6 passes).
8. **Wire audio PCB to dongle** (one short coax / shielded pair from buffer output to dongle mic-in pad; bottom side of buffer cap = audio GND).
9. **Wire dongle to back-panel jacks.**
10. **Bolt the back panel to the can** (4× M3 through-bolts with nuts + washers, OR pop-rivets, OR epoxy-bond + screws into nutserts).
11. **Attach the AGND chassis-tie wire** at the sanded patch on inside of can — solder lug + screw.
12. **Mount the capsule + foam grommet in the cap.** Wire shielded pair (signal + AGND) down to PCB.
13. **Foam-wrap the PCB** for resonance damping.
14. **Slide PCB into can,** route capsule wires up to cap, screw the cap on.
15. **Plug in, test.** Bring-up should mirror the breadboard sequence (Stage 0 → 1 → 2 → ... → 6) since nothing changed electrically — only mechanically.

---

## 8. Things to think about but not commit to yet

These are **defer-until-the-prototype-works** items:

- **Mute button.** Convenient for Zoom. Adds a switch + maybe an LED to the front panel. Decide after you've used the mic for a week.
- **Gain knob on the outside.** The schematic specifies a 12-position rotary. If front-panel-mounted, drill a hole through the can for the shaft. Or accept fixed gain (saves the rotary, which isn't in your cart anyway).
- **Threshold knob on the outside.** Same logic as gain knob.
- **Shock mount / boom arm interface.** Standard 5/8" thread (US) or 3/8" (Euro) is the boom arm convention. Out of scope for this build — accept the can sits on the desk for now.
- **Pop filter:** the foam windscreen handles small plosives. If you talk loud, a separate ring-mounted pop filter helps. Not the enclosure's job.
- **Aesthetics.** Spray paint the can after build. Don't paint before — you'll scratch it during construction.

---

## 9. Summary of grounding / shielding rules (the one-page reference)

- **AUDIO GND** = output side of B0505 modules, junction of A's Vout− and B's Vout+.
- **USB GND** = input side of B0505s + USB cable + dongle's USB-side electronics + headphone jack sleeve.
- **CHASSIS** (the metal can) = tied to AUDIO GND, at one point, on the inside of the can, on a sanded patch of bare aluminium.
- **CAPSULE SHIELD** (desolder braid around capsule wires) = tied to AUDIO GND, at the capsule end ONLY. Open at the PCB end.
- **HEADPHONE JACK SLEEVE** = USB GND (it's the dongle's playback). Plastic-body jack mandatory to keep this from touching the chassis.
- **USB-C SHIELD** = USB GND. Plastic-mounted (no chassis contact).
- **AUDIO GND ↔ USB GND** = single junction inside the dongle's chip, on the analog mic-in path. NO other connection anywhere.

If you find yourself running a wire that violates any of these, stop and redraw the topology. Ground loops are silent killers.

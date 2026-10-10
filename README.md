# RP2040 Dev Board Case — enclosure-forge target #3

First enclosure produced by the **enclosure-forge harness** (2026-10-10):
generic KiCad front-end extraction → stage-signature pipeline
(orientation / envelopes / parameters) → boolean-validated CadQuery case.
Board: [PartialScience/Custom-RP2040-Dev-Board](https://github.com/PartialScience/Custom-RP2040-Dev-Board)
(KiCad 8, 53.34 × 53.34 × 1.6, 4 × M2.5 holes, micro-B USB, dual 2×18 headers).

[![Validate](https://github.com/Amperstrand/rp2040-devboard-enclosure/actions/workflows/validate.yml/badge.svg)](https://github.com/Amperstrand/rp2040-devboard-enclosure/actions/workflows/validate.yml)

## Design

- Board seats on 4 printed bosses at the **measured** hole centres
  (27.94 × 42.43 grid, drill Ø2.7) — M2.5 self-tap pilots Ø2.1
  (coupon-verify before production print).
- Micro-USB opening through the v=0 wall (full seated-plug envelope +
  bend void, boolean-checked zero shell material).
- Jumper-exit relief windows over **both** 2×18 headers (J3 u-min, J4
  u-max) — lid lip interrupted across both bands.
- Friction-lip lid; interior height = seat + board + tallest header + 1.0.

## Validation — 7/7 PASS

`scripts/validate.py`: seated interference (with support predicate),
component clearance vs all 30 extracted components, USB + both header
envelopes, boss/annulus alignment, watertight solids, deterministic
rebuild. Report: `analysis/interference_report.json`.

The stage-by-stage decisions (including two debug iterations and their
root causes) are recorded in `stages/*.json` — the bootstrap trace for
the forge's optimizer layer (`Amperstrand/enclosure-forge`).

## Regenerate

```sh
python3 scripts/validate.py    # 7 boolean checks
python3 scripts/build.py       # STEP + STL -> output/exports
```

Board geometry re-extraction (any KiCad 6+ board):
`enclosure-forge/harness/frontends/kicad_extract.py`.

## Status

Boolean-validated; physical print pending (print a pilot-hole coupon
ladder Ø2.0–2.3 before the case — the M2.5 self-tap pilot is the one
printer-dependent number).

## 3D

- Spin the assembly: [`exports/rp2040_assembly.glb`](exports/rp2040_assembly.glb) (GLB — Windows 3D Viewer, macOS
  Preview, Blender, gltf-viewer.donmccurdy.com). STLs in
  `output/exports/` render inline on GitHub.
- Scored by the forge metric: **1.00 (7/7 checks)** — see
  `Amperstrand/enclosure-forge` experiments/runs/.


#!/usr/bin/env python3
"""Boolean validation for the RP2040 dev-board case (enclosure-forge S6).

Pass gate: zero unexpected common volume against the KiCad-derived
reference geometry; INTENDED contacts (boss shoulders under the board)
subtracted and named. Report -> analysis/interference_report.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq

from cad import case as C
from cad import parameters as P

REPORT = []


def check(name, ok, value, expect="", note=""):
    REPORT.append({"name": name, "pass": bool(ok), "value": value,
                   "expect": expect, "note": note})
    print(f"  {'PASS' if ok else 'FAIL'} {name} {value} {note}")


def vol(s):
    return s.Volume() if s is not None else 0.0


def inter(a, b):
    if a is None or b is None:
        return 0.0
    return vol(a.intersect(b))


def board_solid():
    return cq.Solid.makeBox(P.BOARD_W, P.BOARD_L, P.BOARD_T,
                            cq.Vector(0, 0, P.BOARD_SEAT_Z))


def comp_solids():
    out = {}
    for ref, c in P.COMPS.items():
        u0, u1 = c["u"]
        v0, v1 = c["v"]
        out[ref] = cq.Solid.makeBox(u1 - u0, v1 - v0, c["height"],
                                    cq.Vector(u0, v0,
                                              P.BOARD_SEAT_Z + P.BOARD_T))
    return out


def main() -> int:
    board = board_solid()
    comps = comp_solids()
    bottom = C.bottom_shell()
    lid = C.lid()
    both = bottom.fuse(lid)

    # 1 seated board vs shells: coincident face contact reads 0 mm3, so
    #   the gate is zero-volume PLUS a support predicate: every mounting
    #   hole has boss material within 0.05 mm below the seat plane
    real = inter(board, bottom) + inter(board, lid)
    supported = 0
    for h in P.GEOM["mounting_holes"]:
        x, y = h["center"]
        probe = cq.Solid.makeCylinder(P.BOSS_OUTER / 2, 0.2,
                                      cq.Vector(x, y,
                                                P.BOARD_SEAT_Z - 0.25))
        if inter(probe, bottom) > 0.1:
            supported += 1
    check("seated_board_interference", real < 0.05 and supported == 4,
          {"volume": round(real, 4), "holes_supported": supported},
          expect="0 mm3, 4/4 supported",
          note="board rests on 4 boss shoulders; nothing else touches")

    # 2 every component clears both shells
    bad = {r: round(inter(c, both), 3) for r, c in comps.items()
           if inter(c, both) > 0.01}
    check("component_clearance", not bad, bad,
          note="all placed components clear bottom+lid (0 mm3)")

    # 3 USB envelope stays free of shell material
    u0, u1 = P.USB_U
    z0 = P.BOARD_SEAT_Z + P.BOARD_T - 0.4 - P.USB_CLEAR
    z1 = P.BOARD_SEAT_Z + P.BOARD_T + P.USB_PLUG_H + P.USB_CLEAR
    plug = cq.Solid.makeBox(u1 - u0 + 2 * (1.0 + P.USB_CLEAR), P.USB_REACH,
                            z1 - z0, cq.Vector(u0 - 1.0 - P.USB_CLEAR,
                                               C.INT_V0, z0))
    v = inter(plug, both)
    check("usb_envelope_clear", v < 0.01, round(v, 3),
          note="fully-seated micro-B plug + bend void free of shell")

    # 4 header jumper-exit envelopes stay free (one per 2x18 header)
    worst = 0.0
    for _ref, h in P.HEADERS_2X18.items():
        hv0, hv1 = h["v"]
        if (h["u"][0] + h["u"][1]) / 2 < P.BOARD_W / 2:
            jenv = cq.Solid.makeBox(
                P.HDR_EXIT_REACH, hv1 - hv0 + 2.0,
                P.BOARD_SEAT_Z + P.BOARD_T + 8.5 + 0.8,
                cq.Vector(C.INT_U0, hv0 - 1.0, 0.2))
        else:
            jenv = cq.Solid.makeBox(
                P.HDR_EXIT_REACH, hv1 - hv0 + 2.0,
                P.BOARD_SEAT_Z + P.BOARD_T + 8.5 + 0.8,
                cq.Vector(C.INT_U1 - P.HDR_EXIT_REACH, hv0 - 1.0, 0.2))
        worst = max(worst, inter(jenv, both))
    check("header_exit_envelope_clear", worst < 0.01, round(worst, 3),
          note="2x18 jumper exits (both walls) + finger access free of shell")

    # 5 bosses align with the measured holes (annulus just below the seat)
    ok, detail = True, []
    for h in P.GEOM["mounting_holes"]:
        x, y = h["center"]
        annulus = cq.Solid.makeCylinder(h["drill"] / 2 + 0.15, 0.2,
                                        cq.Vector(x, y,
                                                  P.BOARD_SEAT_Z - 0.25))
        in_band = inter(annulus, bottom)
        hole_free = cq.Solid.makeCylinder(P.BOSS_PILOT / 2 - 0.05, 1.0,
                                          cq.Vector(x, y, 0.5))
        blocked = inter(hole_free, bottom)
        detail.append((round(in_band, 2), round(blocked, 3)))
        ok = ok and in_band > 0.1 and blocked < 0.01
    check("bosses_at_measured_holes", ok, detail,
          note="boss ring carries the hole annulus; pilot stays clear")

    # 6 solids valid + watertight
    sv = {"bottom": round(vol(bottom), 1), "lid": round(vol(lid), 1)}
    check("solids_valid", bottom.isValid() and lid.isValid()
          and vol(bottom) > 0 and vol(lid) > 0, sv,
          note="watertight B-reps, positive volume")

    # 7 deterministic rebuild (STL hash)
    import tempfile

    def stl_hash(solid):
        w = cq.Workplane(obj=solid)
        with tempfile.NamedTemporaryFile(suffix=".stl") as tf:
            cq.exporters.export(w, tf.name, exportType="STL", tolerance=0.05,
                                angularTolerance=0.2)
            tf.seek(0)
            return hashlib.sha256(tf.read()).hexdigest()[:16]

    h1a, h2a = stl_hash(C.bottom_shell()), stl_hash(C.lid())
    h1b, h2b = stl_hash(C.bottom_shell()), stl_hash(C.lid())
    check("deterministic_rebuild", h1a == h1b and h2a == h2b,
          {"bottom": h1a, "lid": h2a},
          note="two consecutive builds produce hash-identical STLs")

    out = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "analysis", "interference_report.json")
    with open(out, "w") as f:
        json.dump(REPORT, f, indent=1)
    failed = sum(1 for r in REPORT if not r["pass"])
    print(f"\n{len(REPORT)} checks, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the RP2040 dev-board case parts -> output/exports (STEP + STL)."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cadquery as cq

from cad import case as C

OUT = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "output", "exports")


def export(name, solid):
    w = cq.Workplane(obj=solid)
    cq.exporters.export(w, os.path.join(OUT, name + ".step"))
    cq.exporters.export(w, os.path.join(OUT, name + ".stl"), exportType="STL",
                        tolerance=0.05, angularTolerance=0.2)
    bb = solid.BoundingBox()
    print(f"{name:24s} vol {solid.Volume():8.1f} mm^3  "
          f"bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")


def main():
    os.makedirs(OUT, exist_ok=True)
    export("bottom_shell", C.bottom_shell())
    export("lid", C.lid())


if __name__ == "__main__":
    main()

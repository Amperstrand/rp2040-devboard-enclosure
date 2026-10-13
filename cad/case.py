"""RP2040 dev-board case: bottom shell + friction lid (target #3).

Board seats on four printed bosses at the measured M2.5 holes; micro-USB
opens through the v=0 wall; the 2x18 header gets a side-exit relief
window in the u=0 wall. Built by the enclosure-forge harness S4/S5.
"""

from __future__ import annotations

import cadquery as cq

from . import parameters as P

INT_U0, INT_U1 = -P.WALL_T, P.BOARD_W + P.WALL_T
INT_V0, INT_V1 = -P.WALL_T, P.BOARD_L + P.WALL_T
LID_Z0 = P.LID_INT_Z


def _box(x0, y0, x1, y1, z0, z1):
    if x1 <= x0 or y1 <= y0 or z1 <= z0:
        return None
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def _fuse_all(solids):
    out = None
    for s in solids:
        if s is None:
            continue
        out = s if out is None else out.fuse(s)
    return out


def bottom_shell():
    ox0, oy0 = INT_U0 - P.WALL_T, INT_V0 - P.WALL_T
    ox1, oy1 = INT_U1 + P.WALL_T, INT_V1 + P.WALL_T
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2

    walls = (
        cq.Workplane("XY", origin=(cx, cy, -P.FLOOR_T))
        .rect(ox1 - ox0, oy1 - oy0).extrude(LID_Z0 + P.FLOOR_T)
        .edges("|Z").fillet(P.CORNER_R)
    ).val()
    cavity = _box(INT_U0, INT_V0, INT_U1, INT_V1, -P.FLOOR_T - 0.01, LID_Z0 + 1)
    solid = walls.cut(cavity)
    solid = solid.fuse(_box(INT_U0, INT_V0, INT_U1, INT_V1, -P.FLOOR_T, 0.0))

    # bosses at measured hole centres: outer shoulder fused, pilot CUT
    bosses, pilots = [], []
    for h in P.GEOM["mounting_holes"]:
        x, y = h["center"]
        bosses.append(cq.Solid.makeCylinder(
            P.BOSS_OUTER / 2, P.BOARD_SEAT_Z, cq.Vector(x, y, 0)))
        pilots.append(cq.Solid.makeCylinder(
            P.BOSS_PILOT / 2, P.BOARD_SEAT_Z + 1, cq.Vector(x, y, 0.0)))
    solid = solid.fuse(_fuse_all(bosses))
    for p in pilots:
        solid = solid.cut(p)

    # micro-USB opening in the v=0 wall (full plug envelope + bend void)
    u0, u1 = P.USB_U
    z0 = P.BOARD_SEAT_Z + P.BOARD_T - 0.4
    z1 = P.BOARD_SEAT_Z + P.BOARD_T + P.USB_PLUG_H + P.USB_CLEAR
    solid = solid.cut(_box(u0 - 1.0 - P.USB_CLEAR, oy0 - 1,
                           u1 + 1.0 + P.USB_CLEAR, INT_V0 + P.USB_REACH,
                           z0 - P.USB_CLEAR, z1))
    # 2x18 header relief windows in the nearest u wall of each header
    for _ref, h in P.HEADERS_2X18.items():
        hv0, hv1 = h["v"]
        hu0, hu1 = h["u"]
        if (hu0 + hu1) / 2 < P.BOARD_W / 2:
            cut = _box(ox0 - 1, hv0 - 1.0, INT_U0 + P.HDR_EXIT_REACH,
                       hv1 + 1.0, 0.2,
                       P.BOARD_SEAT_Z + P.BOARD_T + 8.5 + 1.0)
        else:
            cut = _box(INT_U1 - P.HDR_EXIT_REACH, hv0 - 1.0, ox1 + 1,
                       hv1 + 1.0, 0.2,
                       P.BOARD_SEAT_Z + P.BOARD_T + 8.5 + 1.0)
        solid = solid.cut(cut)
    return solid


def lid():
    ox0, oy0 = INT_U0 - P.WALL_T, INT_V0 - P.WALL_T
    ox1, oy1 = INT_U1 + P.WALL_T, INT_V1 + P.WALL_T
    cx, cy = (ox0 + ox1) / 2, (oy0 + oy1) / 2
    roof = (
        cq.Workplane("XY", origin=(cx, cy, LID_Z0))
        .rect(ox1 - ox0, oy1 - oy0).extrude(1.6)\
        .edges("|Z").fillet(P.CORNER_R)\
        .edges(">Z").chamfer(0.6)
    ).val()
    lip = _box(INT_U0 + P.LID_GAP, INT_V0 + P.LID_GAP,
               INT_U1 - P.LID_GAP, INT_V1 - P.LID_GAP,
               LID_Z0 - P.LID_LIP, LID_Z0)
    lip = lip.cut(_box(INT_U0 + P.LID_GAP + 1.2, INT_V0 + P.LID_GAP + 1.2,
                       INT_U1 - P.LID_GAP - 1.2, INT_V1 - P.LID_GAP - 1.2,
                       LID_Z0 - P.LID_LIP - 1, LID_Z0 + 1))
    # break the lip runs over the header exit bands (both u walls)
    for _ref, h in P.HEADERS_2X18.items():
        hv0, hv1 = h["v"]
        lip = lip.cut(_box(INT_U0 - 1, hv0 - 1.5, INT_U1 + 1, hv1 + 1.5,
                           LID_Z0 - P.LID_LIP - 1, LID_Z0 + 1))
    return roof.fuse(lip)

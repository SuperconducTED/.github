"""SuperconducTED, round 3, style RADIAL ORNAMENT / ASTROLABE.

The hero looks straight up into the dilution refrigerator. The bolted room-temperature
top flange is the outermost, heaviest ring; four plates follow inward, going from solid
and bolted (warm) to open hairlines (cold); the space between plates is engraved with
radial hatching that converges on the axis, like looking up a shaft. Support rods are
seen end-on as hollow radial tubes in every gap, and three coax bundles run down through
every stage with a slack bow per gap, feedthroughs in the solid plates, beads on the open
ones, attenuator blocks where they reach the dial, and one service loop each.

The coldest plate (the mixing chamber) is the astrolabe's plate: its rim is engraved as a
graduated calibration dial. The index at twelve o'clock and the reticle under it mark
where the frozen snapshot says the machine is. The chip has drifted 45 degrees clockwise
off that index along a wandering path of earlier positions; between a [ and a ] the dial
turns solid and its graduations open as windows: the range the engine reports, holding
the index, the whole trail and the chip.

All art is filled geometry computed here and combined in VectorCraft with real booleans
(unite, minus front), so every knockout is a hole: the same mark works in ink on paper,
paper on ink, and solid black on transparent. Each shipped SVG is one compound path.

The small companion is a separate bold redraw on a 32-unit grid (small_e); its 16 px
version is hand-hinted pixel art of the same drawing (PIX16).

Usage (Python 3.12, standard library only; the engine path is in tools/vcdriver.py):
    python -I build.py            look renders in _work/, then every deliverable
    python -I build.py ship       only the deliverables, the SVG round trip and magnifier
    python -I build.py look       only the quick look renders in _work/
    python -I build.py hero       only _work/look-hero.png
    python -I build.py lab        the small-mark variants side by side, _work/lab-mag.png
"""
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, TOOLS)
from vcdriver import VC  # noqa: E402

INK = "#1A1D24"
PAPER = "#F2EEE6"
BLACK = "#000000"
WHITE = "#FFFFFF"
FONT = "Space Grotesk"

C = 500.0  # hero art box is 1000 x 1000 units, centre (C, C)

# ---------------------------------------------------------------- geometry primitives
# Every positive shape is wound counter-clockwise on screen (y down), so shapes that
# overlap inside one path union under the engine's nonzero fill rule.


def f(v):
    return f"{v:.3f}"


def pol(r, b, cx=C, cy=C):
    """Point at radius r and bearing b (degrees clockwise from twelve o'clock)."""
    a = math.radians(b)
    return cx + r * math.sin(a), cy - r * math.cos(a)


def circle(cx, cy, r, hole=False):
    s = 1 if hole else 0
    return (f"M {f(cx + r)} {f(cy)} A {f(r)} {f(r)} 0 1 {s} {f(cx - r)} {f(cy)} "
            f"A {f(r)} {f(r)} 0 1 {s} {f(cx + r)} {f(cy)} Z")


def annulus(r_out, r_in, cx=C, cy=C):
    return circle(cx, cy, r_out) + " " + circle(cx, cy, r_in, hole=True)


def sector(r_in, r_out, b0, b1, cx=C, cy=C):
    """Annular sector from bearing b0 to b1 (b1 > b0), wound counter-clockwise."""
    large = 1 if (b1 - b0) > 180 else 0
    x0, y0 = pol(r_out, b1, cx, cy)
    x1, y1 = pol(r_out, b0, cx, cy)
    x2, y2 = pol(r_in, b0, cx, cy)
    x3, y3 = pol(r_in, b1, cx, cy)
    return (f"M {f(x0)} {f(y0)} A {f(r_out)} {f(r_out)} 0 {large} 0 {f(x1)} {f(y1)} "
            f"L {f(x2)} {f(y2)} A {f(r_in)} {f(r_in)} 0 {large} 1 {f(x3)} {f(y3)} Z")


def area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts)))


def poly(pts):
    """Closed polygon, re-wound counter-clockwise on screen (negative shoelace in y down)."""
    if area(pts) > 0:
        pts = pts[::-1]
    return "M " + " L ".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"


def capsule(x0, y0, x1, y1, w):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 1e-9:
        return circle(x0, y0, w / 2)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -dy * w / 2, dx * w / 2
    r = w / 2
    a, b = (x0 + nx, y0 + ny), (x1 + nx, y1 + ny)
    c, d = (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)
    return (f"M {f(a[0])} {f(a[1])} L {f(b[0])} {f(b[1])} A {f(r)} {f(r)} 0 0 0 {f(c[0])} {f(c[1])} "
            f"L {f(d[0])} {f(d[1])} A {f(r)} {f(r)} 0 0 0 {f(a[0])} {f(a[1])} Z")


def bar(x0, y0, x1, y1, w):
    """Square-ended thick segment."""
    L = math.hypot(x1 - x0, y1 - y0)
    dx, dy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -dy * w / 2, dx * w / 2
    return poly([(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)])


def radial_bar(r0, r1, b, w, cx=C, cy=C):
    return bar(*pol(r0, b, cx, cy), *pol(r1, b, cx, cy), w)


def radial_capsule(r0, r1, b, w, cx=C, cy=C):
    return capsule(*pol(r0, b, cx, cy), *pol(r1, b, cx, cy), w)


def rrect(x, y, w, h, r):
    """Rounded rectangle wound counter-clockwise on screen."""
    return (f"M {f(x + r)} {f(y)} A {f(r)} {f(r)} 0 0 0 {f(x)} {f(y + r)} L {f(x)} {f(y + h - r)} "
            f"A {f(r)} {f(r)} 0 0 0 {f(x + r)} {f(y + h)} L {f(x + w - r)} {f(y + h)} "
            f"A {f(r)} {f(r)} 0 0 0 {f(x + w)} {f(y + h - r)} L {f(x + w)} {f(y + r)} "
            f"A {f(r)} {f(r)} 0 0 0 {f(x + w - r)} {f(y)} Z")


def polyline(pts, w):
    """A stroked open polyline as round-capped capsules (they union where they meet)."""
    return " ".join(capsule(*pts[i], *pts[i + 1], w) for i in range(len(pts) - 1))


def catmull(pts, n=12):
    """Smooth curve through pts (Catmull-Rom, sampled)."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(pts[-1])
    return out


def J(*parts):
    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------- the hero, in layers
# Radii in the 1000-unit box, outside in: the bolted top flange, four plates, and the
# mixing-chamber plate, whose rim is engraved as the calibration dial around the chip.
W_HEAVY, W_MED, W_FINE, W_HAIR = 12.0, 4.4, 2.2, 1.3   # the stroke-weight hierarchy

FLANGE = (490, 456)            # room-temperature top flange: heavy, bolted
PLATES = [                     # (outer, inner) edge radii, warm to cold
    (428, 414),                # P1: solid, a ring of small bolts
    (392, 380),                # P2: solid, one engraved line
    (362, 352),                # P3: open band with beads
    (338, 332),                # P4: double hairline
]
DIAL_RIM = (294, 302)          # mixing-chamber plate: outer rim of the dial
DIAL_IRIM = (250, 253.5)       # inner rim of the dial
TICK_OUT = 290
MINOR_IN, MID_IN, MAJOR_IN = 281, 273, 264
RINGS = [FLANGE] + PLATES + [(DIAL_RIM[1], DIAL_IRIM[0])]
GAPS = [(RINGS[k + 1][0], RINGS[k][1]) for k in range(5)]   # (inner, outer) radius of each gap

B_LO, B_HI = -18.0, 68.0      # the reported interval, as bearings on the dial
B_INDEX = 0.0                 # the frozen snapshot's index
R_ORBIT = 168.0               # where the chip rides on the coldest plate
B_CHIP = 45.0                 # where the chip is now
TRAIL = [(0.0, 168), (-10.0, 142), (10.0, 140), (22.0, 172)]  # oldest first: snapshot, then drift
CHIP_S = 78.0
HATCH_PITCH = 8.0             # units between hatch lines at mid-gap
COAX_B = (135.0, 225.0, 315.0)  # three cable bundles on the diagonals the interval leaves free


def dial_ticks(r_out=TICK_OUT, minor_in=MINOR_IN, mid_in=MID_IN, major_in=MAJOR_IN):
    """Graduations every 2 degrees: fine; every 10: medium; every 30: a tapered dagger."""
    out = []
    for k in range(180):
        b = 2.0 * k
        if k % 15 == 0:
            p0, p1 = pol(major_in, b), pol(r_out, b)
            hw0, hw1 = 0.7, 3.8
            ang = math.radians(b)
            tx, ty = math.cos(ang), math.sin(ang)   # tangent at bearing b
            out.append(poly([(p0[0] - tx * hw0, p0[1] - ty * hw0), (p0[0] + tx * hw0, p0[1] + ty * hw0),
                             (p1[0] + tx * hw1, p1[1] + ty * hw1), (p1[0] - tx * hw1, p1[1] - ty * hw1)]))
        elif k % 5 == 0:
            out.append(radial_capsule(mid_in, r_out, b, 3.4))
        else:
            out.append(radial_capsule(minor_in, r_out, b, 1.7))
    return out


def ticks_in(b0, b1):
    """Only the graduations whose bearing lies strictly inside (b0, b1)."""
    keep = []
    for k, d in enumerate(dial_ticks()):
        b = 2.0 * k
        bb = b if b <= 180 else b - 360
        if b0 < bb < b1:
            keep.append(d)
    return keep


def bracket(b, side, r_a, r_b, t, arm, grow=0.0, cx=C, cy=C):
    """An interval bracket bent onto the dial: a radial spine at bearing b and two arms
    along the arcs at r_a and r_b, reaching `arm` units into the interval
    (side=+1 draws '[' opening clockwise, side=-1 draws ']')."""
    g = grow
    out = [radial_bar(r_a - g, r_b + g, b, t + 2 * g, cx, cy)]
    for r0, r1 in ((r_a - g, r_a + t + g), (r_b - t - g, r_b + g)):
        rm = (r0 + r1) / 2
        half_spine = math.degrees((t / 2 + g) / rm)
        reach = math.degrees((arm + g) / rm)
        if side > 0:
            out.append(sector(r0, r1, b - half_spine, b + reach, cx, cy))
        else:
            out.append(sector(r0, r1, b - reach, b + half_spine, cx, cy))
    return out


def chip_body(cx, cy, s, grow=0.0):
    """A packaged chip: body plus 4 pins a side (grow > 0 gives its halo)."""
    g = grow
    pin_l, pin_w, pitch = 0.16 * s, 0.085 * s, 0.2 * s
    out = [rrect(cx - s / 2 - g, cy - s / 2 - g, s + 2 * g, s + 2 * g, 0.1 * s + g)]
    for k in range(4):
        o = (k - 1.5) * pitch
        rr = pin_w / 2.4
        out.append(rrect(cx - s / 2 - pin_l - g, cy + o - pin_w / 2 - g, pin_l + 2 * g + 2, pin_w + 2 * g, rr))
        out.append(rrect(cx + s / 2 - 2 - g, cy + o - pin_w / 2 - g, pin_l + 2 * g + 2, pin_w + 2 * g, rr))
        out.append(rrect(cx + o - pin_w / 2 - g, cy - s / 2 - pin_l - g, pin_w + 2 * g, pin_l + 2 * g + 2, rr))
        out.append(rrect(cx + o - pin_w / 2 - g, cy + s / 2 - 2 - g, pin_w + 2 * g, pin_l + 2 * g + 2, rr))
    return out


def coax_path(b, r_out, r_in, amp):
    """One cable crossing a gap from r_out down to r_in with a slack bow of `amp` degrees."""
    pts = []
    for n in range(19):
        t = n / 18
        pts.append(pol(r_out + (r_in - r_out) * t, b + amp * math.sin(math.pi * t)))
    return pts


def loop_path(b, r_out, r_in, rho):
    """A cable with one service loop: a prolate cycloid along the radius (it loops back
    once because 2 pi rho exceeds the gap), displaced tangentially toward larger bearing."""
    Lg = r_out - r_in
    pts = []
    for n in range(61):
        t = n / 60
        s = Lg * t + rho * math.sin(2 * math.pi * t)
        u = rho * (1 - math.cos(2 * math.pi * t))
        r = r_out - s
        pts.append(pol(r, b + math.degrees(u / r)))
    return pts


def hero_layers():
    """The hero as an ordered list of ('ink' | 'knock', path data). Order is paint order:
    a knock removes everything drawn so far inside its footprint."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731

    # 1. The top flange: the warmest, heaviest ring, bolted, with an engraved line.
    ink(annulus(*FLANGE))
    knock(*[circle(*pol(475, 15.0 * k + 7.5), 6.2) for k in range(24)], annulus(464.8, 463.0))

    # 2. Four plates, warm (heavy) to cold (fine).
    o, i = PLATES[0]
    ink(annulus(o, i))
    knock(*[circle(*pol((o + i) / 2, 7.5 * k + 3.75), 2.7) for k in range(48)])
    o, i = PLATES[1]
    ink(annulus(o, i))
    knock(annulus(o - 3.6, o - 5.0))
    o, i = PLATES[2]
    ink(annulus(o, o - 2.6), annulus(i + 2.2, i), *[circle(*pol((o + i) / 2, 4.0 * k + 2.0), 1.7) for k in range(90)])
    o, i = PLATES[3]
    ink(annulus(o, o - 1.8), annulus(i + 1.4, i))

    # 3. The mixing-chamber plate, its rim engraved as the calibration dial.
    ink(annulus(DIAL_RIM[1], DIAL_RIM[0]), annulus(DIAL_IRIM[1], DIAL_IRIM[0]), *dial_ticks())

    # 4. The space between the plates, engraved with fine radial lines that converge on
    #    the axis: looking up a shaft. The last gap stays clear so the dial and its
    #    brackets sit on open paper.
    hatch = []
    for g, (r_in, r_out) in enumerate(GAPS[:4]):
        n = int(round(2 * math.pi * (r_in + r_out) / 2 / HATCH_PITCH))
        for k in range(n):
            hatch.append(radial_capsule(r_in + 3.0, r_out - 3.0, 360.0 * (k + 0.5) / n, 1.1))
    ink(*hatch)

    # 5. Support rods seen end-on: tubes spanning each gap, alternating by 30 degrees,
    #    each cut clear of the hatching.
    rods, slots, clear = [], [], []
    for g, (r_in, r_out) in enumerate(GAPS):
        w = (13, 11, 9.5, 8, 8)[g]
        off = 30.0 if g % 2 == 0 else 0.0
        for k in range(6):
            b = off + 60.0 * k
            clear.append(radial_bar(r_in + 0.5, r_out - 0.5, b, w + 7 + 9))
            rods.append(radial_bar(r_in - 1, r_out + 1, b, w))
            rods.append(radial_bar(r_in - 1, r_in + 3.5, b, w + 7))
            rods.append(radial_bar(r_out - 3.5, r_out + 1, b, w + 7))
            if r_out - r_in > 17:
                slots.append(radial_bar(r_in + 6.5, r_out - 6.5, b, max(1.6, w * 0.3)))
    knock(*clear)
    ink(*rods)
    knock(*slots)

    # 6. Coax: three bundles of three lines running down through every stage,
    #    slack-bowed in each gap, attenuators on the first plate and at the dial,
    #    bulkhead beads between, one service loop per bundle.
    cables, chan, blocks = [], [], []
    for b0 in COAX_B:
        for j, off in enumerate((-2.3, 0.0, 2.3)):
            for g, (r_in, r_out) in enumerate(GAPS):
                amp = (1.5, 1.2, 1.0, 0.9, 0.8)[g]
                if g == 0 and j == 2:
                    pts = loop_path(b0 + off, r_out, r_in, 10.5)
                else:
                    pts = coax_path(b0 + off, r_out, r_in, amp)
                cables.append(polyline(pts, 2.0))
                chan.append(polyline(pts, 8.0))
            for k, (o, i) in enumerate(PLATES + [(DIAL_RIM[1], DIAL_RIM[1] - 6)]):
                if k in (2, 3):
                    blocks.append(radial_capsule(i - 2.5, o + 2.5, b0 + off, 5.6))
                elif k == 4:
                    blocks.append(radial_bar(i - 3, o + 3, b0 + off, 6.0))
    knock(*chan)
    ink(*cables, *blocks)
    # feedthroughs where the cables pass the solid flange and the two solid plates
    holes = [(FLANGE[1] + 10, b0 + off) for b0 in COAX_B for off in (-2.3, 0.0, 2.3)]
    holes += [((o + i) / 2, b0 + off) for (o, i) in PLATES[:2] for b0 in COAX_B for off in (-2.3, 0.0, 2.3)]
    knock(*[circle(*pol(r, b), 4.4) for r, b in holes])
    ink(*[circle(*pol(r, b), 2.0) for r, b in holes])

    # 7. The face of the coldest plate: the chip's dashed track, a hexagonal cold-finger boss
    #    and six mounting screws.
    track = [sector(R_ORBIT - 0.7, R_ORBIT + 0.7, 3.0 * k, 3.0 * k + 1.6) for k in range(120)]
    hexo = [pol(40, 60.0 * k + 30) for k in range(6)]
    hexi = [pol(36.2, 60.0 * k + 30) for k in range(6)]
    ink(*track, poly(hexo))
    knock(poly(hexi))
    ink(annulus(20.2, 18.2), circle(C, C, 6.0), *[annulus(5.0, 3.0, *pol(86, 60.0 * k + 30)) for k in range(6)])

    # 8. The snapshot's index: a pointer above the dial at twelve o'clock.
    tri = [pol(306, B_INDEX), pol(329, B_INDEX - 1.95), pol(329, B_INDEX + 1.95)]
    knock(poly([pol(303, B_INDEX - 0.6), pol(303, B_INDEX + 0.6), pol(334, B_INDEX + 3.0), pol(334, B_INDEX - 3.0)]))
    ink(poly(tri))

    # 9. The reported interval: the dial goes solid between the brackets, its
    #    graduations open as windows, and the brackets close it.
    ink(sector(DIAL_IRIM[0], DIAL_RIM[1], B_LO, B_HI))
    knock(*ticks_in(B_LO + 1.0, B_HI - 1.0))
    r_a, r_b, t, arm = 234.0, 321.0, W_HEAVY, 24.0
    knock(*bracket(B_LO, +1, r_a, r_b, t, arm, grow=5.5), *bracket(B_HI, -1, r_a, r_b, t, arm, grow=5.5))
    ink(*bracket(B_LO, +1, r_a, r_b, t, arm), *bracket(B_HI, -1, r_a, r_b, t, arm))

    # 10. The drift: the snapshot's aim point, a trail of earlier positions, the chip now.
    chip_xy = pol(R_ORBIT, B_CHIP)
    curve = catmull([pol(r, b) for b, r in TRAIL] + [chip_xy], 12)
    n = len(curve) - 1
    wid = [1.1 + 1.5 * (k / n) for k in range(n + 1)]       # the path thickens toward now
    knock(*[capsule(*curve[k], *curve[k + 1], wid[k] + 6.0) for k in range(n)])
    ink(*[capsule(*curve[k], *curve[k + 1], wid[k]) for k in range(n)])
    dot_r = [0, 4.0, 5.2, 6.4]
    ink(*[circle(*pol(r, b), dot_r[k]) for k, (b, r) in enumerate(TRAIL) if k > 0])
    sx, sy = pol(TRAIL[0][1], TRAIL[0][0])
    knock(circle(sx, sy, 21.0))
    ink(annulus(11.0, 8.4, sx, sy), capsule(sx - 17, sy, sx - 5, sy, 2.0), capsule(sx + 5, sy, sx + 17, sy, 2.0),
        capsule(sx, sy - 17, sx, sy - 5, 2.0), capsule(sx, sy + 5, sx, sy + 17, 2.0))
    cx, cy = chip_xy
    s = CHIP_S
    knock(*chip_body(cx, cy, s, grow=6.5))
    ink(*chip_body(cx, cy, s))
    q = 0.018 * s
    knock(rrect(cx - 0.31 * s, cy - 0.31 * s, 0.62 * s, 0.62 * s, 0.05 * s))
    ink(rrect(cx - 0.21 * s, cy - 0.21 * s, 0.42 * s, 0.42 * s, 0.035 * s))
    knock(rrect(cx - 0.13 * s, cy - 2 * q, 0.26 * s, 4 * q, 2 * q), rrect(cx - 2 * q, cy - 0.13 * s, 4 * q, 0.26 * s, 2 * q))
    return L


# ---------------------------------------------------------------- the small companion
# A separate bold redraw on a 32-unit grid (1 unit = 1 px at 32, 0.5 px at 16).
SB_LO, SB_HI, SB_CHIP = -30.0, 75.0, 25.0   # used by the lab variants a..d; the shipped small_e runs 0 to 90


def small_bracket(b, side, r_a, r_b, t, arm, grow=0.0, c=16.0):
    return bracket(b, side, r_a, r_b, t, arm, grow, c, c)


def small_a():
    """Ring, a thick bracketed arc on it, the chip inside, off the index."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    ink(annulus(14.0, 12.0, c, c))
    ink(sector(8.5, 14.0, SB_LO, SB_HI, c, c))
    knock(*small_bracket(SB_LO, +1, 6.0, 16.0, 2.0, 2.6, 1.2), *small_bracket(SB_HI, -1, 6.0, 16.0, 2.0, 2.6, 1.2))
    ink(*small_bracket(SB_LO, +1, 6.0, 16.0, 2.0, 2.6), *small_bracket(SB_HI, -1, 6.0, 16.0, 2.0, 2.6))
    x, y = pol(3.2, SB_CHIP, c, c)
    knock(rrect(x - 4.4, y - 4.4, 8.8, 8.8, 2.0))
    ink(rrect(x - 3.0, y - 3.0, 6.0, 6.0, 1.0))
    return L


def small_b():
    """Three rings (flange, plate, dial), the dial thick inside its brackets, the chip."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    ink(annulus(16.0, 14.0, c, c), annulus(11.5, 10.0, c, c))
    ink(sector(6.5, 11.5, SB_LO, SB_HI, c, c))
    knock(*small_bracket(SB_LO, +1, 5.0, 12.5, 1.8, 2.2, 1.0), *small_bracket(SB_HI, -1, 5.0, 12.5, 1.8, 2.2, 1.0))
    ink(*small_bracket(SB_LO, +1, 5.0, 12.5, 1.8, 2.2), *small_bracket(SB_HI, -1, 5.0, 12.5, 1.8, 2.2))
    x, y = pol(1.8, SB_CHIP, c, c)
    knock(rrect(x - 3.6, y - 3.6, 7.2, 7.2, 1.6))
    ink(rrect(x - 2.4, y - 2.4, 4.8, 4.8, 0.8))
    return L


def small_c():
    """Bold: a heavy ring whose interval swells into a bracketed band; the chip is big."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    ink(annulus(15.0, 12.0, c, c))
    ink(sector(9.0, 15.0, SB_LO, SB_HI, c, c))
    knock(*[radial_bar(7.0, 16.5, b, 4.6, c, c) for b in (SB_LO, SB_HI)])
    ink(*small_bracket(SB_LO, +1, 8.0, 16.0, 2.0, 2.4), *small_bracket(SB_HI, -1, 8.0, 16.0, 2.0, 2.4))
    x, y = pol(3.0, SB_CHIP, c, c)
    knock(rrect(x - 5.0, y - 5.0, 10.0, 10.0, 2.4))
    ink(rrect(x - 3.6, y - 3.6, 7.2, 7.2, 1.2))
    return L


def small_d():
    """The chosen 32-unit redraw: the dial ring, the interval swelling into a heavy band
    held by two bracket glyphs whose arms clear it, the chip off centre toward it."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    ink(annulus(13.0, 11.0, c, c))
    ink(sector(9.0, 13.0, SB_LO, SB_HI, c, c))
    r_a, r_b, t, arm = 5.5, 16.0, 2.0, 3.4
    knock(*small_bracket(SB_LO, +1, r_a, r_b, t, arm, 1.0), *small_bracket(SB_HI, -1, r_a, r_b, t, arm, 1.0))
    ink(*small_bracket(SB_LO, +1, r_a, r_b, t, arm), *small_bracket(SB_HI, -1, r_a, r_b, t, arm))
    x, y = pol(2.0, SB_CHIP, c, c)
    knock(rrect(x - 4.2, y - 4.2, 8.4, 8.4, 1.8))
    ink(rrect(x - 3.0, y - 3.0, 6.0, 6.0, 1.0))
    return L


def R(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def small_e():
    """The chosen 32-unit redraw. The interval runs from twelve to three o'clock so both
    bracket glyphs are axis-aligned and land on whole pixels at 32 and at 16 px: the '['
    stands upright at the top, the ']' lies on its side at the right (each glyph is
    radial, as on the hero). Between them the dial swells into a heavy band; the chip
    sits two units off centre toward it."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    ink(sector(10.6, 15.0, 0.0, 90.0, c, c))
    knock(R(0, 0, 20.6, 32), R(0, 11.4, 32, 32))
    ink(annulus(15.0, 13.0, c, c))
    knock(R(13.5, -1, 20.5, 10), R(22, 11.5, 33, 18.5))
    ink(R(16, 0, 18, 8), R(18, 0, 20, 2), R(18, 6, 20, 8),
        R(24, 14, 32, 16), R(24, 12, 26, 14), R(30, 12, 32, 14))
    ink(rrect(16, 10, 6, 6, 1.0))
    return L


def small_f():
    """Mirror-symmetric redraw: the interval is centred on the index at twelve o'clock and
    held by two tilted bracket glyphs (as on the hero); the chip has drifted off the index
    toward one side but stays under the band. The index is a notch in the band."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = 16.0
    lo, hi = -50.0, 50.0
    ink(annulus(14.0, 12.0, c, c))
    ink(sector(9.0, 14.0, lo, hi, c, c))
    r_a, r_b, t, arm = 6.0, 16.0, 2.2, 3.2
    knock(*small_bracket(lo, +1, r_a, r_b, t, arm, 1.1), *small_bracket(hi, -1, r_a, r_b, t, arm, 1.1))
    ink(*small_bracket(lo, +1, r_a, r_b, t, arm), *small_bracket(hi, -1, r_a, r_b, t, arm))
    knock(poly([pol(10.5, -4.0, c, c), pol(10.5, 4.0, c, c), pol(15.0, 0.0, c, c)]))
    x, y = pol(3.4, 28.0, c, c)
    knock(rrect(x - 4.3, y - 4.3, 8.6, 8.6, 1.9))
    ink(rrect(x - 3.0, y - 3.0, 6.0, 6.0, 1.0))
    return L


# The 16 px favicon is hinted by hand as pixel art: every shape lands on whole pixels.
PIX16 = [
    "........##......",
    ".....##.#.#.....",
    "...##...#.###...",
    "..#.....##.###..",
    "..#.........##..",
    ".#......###..##.",
    ".#......###.#..#",
    ".#......###.####",
    ".#..............",
    ".#............#.",
    ".#............#.",
    "..#..........#..",
    "..#..........#..",
    "...##......##...",
    ".....######.....",
    "................",
]


def pix16_layers(rows=PIX16):
    """Pixel art as one path of unit squares (16-unit grid)."""
    sq = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#":
                sq.append(poly([(x, y), (x + 1, y), (x + 1, y + 1), (x, y + 1)]))
    return [("ink", J(*sq))]


SMALL_VARIANTS = {"d": small_d, "e": small_e, "f": small_f}
small_layers = small_e   # shipped as small.svg; small_a..small_f are lab variants kept for the record


def small_lab(vc, work):
    keys = list(SMALL_VARIANTS)
    W = 48 * len(keys) + 8
    new(vc, W, 72, "lab")
    rect(vc, 0, 0, W, 72, PAPER)
    for k, key in enumerate(keys):
        S = SMALL_VARIANTS[key]()
        render(vc, S, 48 * k + 8, 4, 1.0, INK)
        render(vc, S, 48 * k + 16, 48, 0.5, INK)
    render(vc, pix16_layers(), 48 * len(keys) - 20, 48, 1.0, INK)
    vc.tool("export", path=os.path.join(work, "lab.png"), scale=1)
    close(vc)
    magnify(os.path.join(work, "lab.png"), os.path.join(work, "lab-mag.png"), 6)


# ---------------------------------------------------------------- VectorCraft plumbing
TOK = re.compile(r"[MLCAZ]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def xf(d, ox, oy, s):
    """Scale path data by s about the origin, then move by (ox, oy). M L C A Z only."""
    toks = TOK.findall(d)
    out, i, cmd = [], 0, None
    while i < len(toks):
        t = toks[i]
        if t in "MLCAZ":
            cmd = t
            out.append(t)
            i += 1
            continue
        if cmd in ("M", "L", "C"):
            out += [f(ox + float(toks[i]) * s), f(oy + float(toks[i + 1]) * s)]
            i += 2
        elif cmd == "A":
            rx, ry, rot, la, sw, ex, ey = toks[i:i + 7]
            out += [f(float(rx) * s), f(float(ry) * s), rot, la, sw, f(ox + float(ex) * s), f(oy + float(ey) * s)]
            i += 7
        else:
            raise ValueError(d[:80])
    return " ".join(out)


def render(vc, layers, ox, oy, s, colour):
    """Paint the layers at offset (ox, oy) and scale s with real booleans; returns ids."""
    acc = None
    for op, d in layers:
        if not d.strip():
            continue
        pid = vc.tool("draw_path", d=xf(d, ox, oy, s), fill=colour, stroke="none")["id"]
        if acc is None:
            if op == "ink":
                acc = [pid]
            else:
                vc.cmd("edit.clear", ids=[pid])
            continue
        vc.cmd("select.set", ids=acc + [pid])
        res = vc.cmd("object.pathfinder.unite" if op == "ink" else "object.pathfinder.minusFront")
        acc = res["ids"]
    vc.cmd("select.set", ids=acc)
    vc.cmd("paint.setFill", color=colour)
    vc.cmd("paint.setStroke", none=True)
    return acc


def rect(vc, x, y, w, h, fill, r=0):
    a = dict(shape="rectangle", x=x, y=y, width=w, height=h, fill=fill, stroke="none")
    if r:
        a["radius"] = r
    return vc.tool("draw_shape", **a)["id"]


def text(vc, s, x, base, size, colour, style="Regular", tracking=None):
    t = vc.tool("add_text", x=x, y=base, text=s, font=FONT, size=size, color=colour)["id"]
    kw = {}
    if style != "Regular":
        kw["style"] = style
    if tracking is not None:
        kw["tracking"] = tracking
    if kw:
        vc.cmd("text.setStyle", id=t, **kw)
    return t


def new(vc, w, h, name):
    vc.cmd("file.new", width=w, height=h, units="Pixels", name=name)


def close(vc):
    vc.cmd("file.close")


def look(vc, work):
    """Quick look renders for the quality loop."""
    H = hero_layers()
    new(vc, 1000, 1000, "look")
    rect(vc, 0, 0, 1000, 1000, PAPER)
    render(vc, H, 0, 0, 1.0, INK)
    vc.tool("export", path=os.path.join(work, "look-hero.png"), scale=1)
    close(vc)
    for name, (fx, fy) in (("look-zoom-coax.png", (0.16, 0.66)), ("look-zoom-chip.png", (0.42, 0.22))):
        z = 2.6
        new(vc, 600, 600, "zoom")
        rect(vc, 0, 0, 600, 600, PAPER)
        render(vc, H, -fx * 1000 * z, -fy * 1000 * z, z, INK)
        vc.tool("export", path=os.path.join(work, name), scale=1)
        close(vc)
    # Small sizes side by side, at true pixel size, then magnified for inspection.
    new(vc, 520, 200, "looksmall")
    rect(vc, 0, 0, 520, 200, PAPER)
    rect(vc, 260, 0, 260, 200, INK)
    x = 10
    for sz in (128, 64):
        render(vc, H, x, 10, sz / 1000, INK)
        render(vc, H, 260 + x, 10, sz / 1000, PAPER)
        x += sz + 10
    S = small_layers()
    for k, sz in enumerate((32, 16)):
        render(vc, S, 10 + k * 50, 150, sz / 32, INK)
        render(vc, S, 270 + k * 50, 150, sz / 32, PAPER)
    vc.tool("export", path=os.path.join(work, "look-small.png"), scale=1)
    close(vc)


# ---------------------------------------------------------------- pixel tools (stdlib only)
def png_read(path):
    """Decode an 8-bit RGB or RGBA, non-interlaced PNG into (w, h, rows of RGBA tuples)."""
    import struct
    import zlib
    data = open(path, "rb").read()
    pos, idat = 8, b""
    w = h = ct = None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
            assert bd == 8 and ct in (2, 6) and il == 0, (bd, ct, il)
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    bpp = 4 if ct == 6 else 3
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a_ = line[x - bpp] if x >= bpp else 0
            b_ = prev[x]
            c_ = prev[x - bpp] if x >= bpp else 0
            if ft == 1:
                line[x] = (line[x] + a_) & 255
            elif ft == 2:
                line[x] = (line[x] + b_) & 255
            elif ft == 3:
                line[x] = (line[x] + (a_ + b_) // 2) & 255
            elif ft == 4:
                pa, pb, pc = abs(b_ - c_), abs(a_ - c_), abs(a_ + b_ - 2 * c_)
                pr = a_ if pa <= pb and pa <= pc else (b_ if pb <= pc else c_)
                line[x] = (line[x] + pr) & 255
        prev = line
        rows.append([tuple(line[x * bpp:x * bpp + bpp]) + ((255,) if bpp == 3 else ()) for x in range(w)])
    return w, h, rows


def png_write(path, w, h, rows):
    import struct
    import zlib
    raw = b"".join(b"\x00" + bytes(v for px in row for v in px) for row in rows)

    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    out += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(out)


def magnify(src, dst, k):
    """Nearest-neighbour enlargement, so a 16 px favicon can be judged pixel by pixel."""
    w, h, rows = png_read(src)
    big = []
    for row in rows:
        line = [px for px in row for _ in range(k)]
        big += [line] * k
    png_write(dst, w * k, h * k, big)


# ---------------------------------------------------------------- deliverables
def deliverables(vc, out):
    H, S = hero_layers(), small_layers()
    # The hero on paper: SVG (the paper square included) and a 1024 px PNG.
    new(vc, 1000, 1000, "hero")
    rect(vc, 0, 0, 1000, 1000, PAPER)
    render(vc, H, 0, 0, 1.0, INK)
    vc.tool("export", path=os.path.join(out, "hero.svg"))
    vc.tool("export", path=os.path.join(out, "hero-1024.png"), scale=1.024)
    close(vc)
    # Solid black on transparent.
    new(vc, 1000, 1000, "hero-black")
    render(vc, H, 0, 0, 1.0, BLACK)
    vc.tool("export", path=os.path.join(out, "hero-black.svg"))
    close(vc)
    # Solid white on black.
    new(vc, 1000, 1000, "hero-white-on-black")
    rect(vc, 0, 0, 1000, 1000, BLACK)
    render(vc, H, 0, 0, 1.0, WHITE)
    vc.tool("export", path=os.path.join(out, "hero-white-on-black.png"), scale=1.024)
    close(vc)
    # The small companion: ink on transparent as SVG; true-size PNGs on paper.
    new(vc, 32, 32, "small")
    render(vc, S, 0, 0, 1.0, INK)
    vc.tool("export", path=os.path.join(out, "small.svg"))
    close(vc)
    for px, layers in ((32, S), (16, pix16_layers())):
        new(vc, px, px, f"small-{px}")
        rect(vc, 0, 0, px, px, PAPER)
        render(vc, layers, 0, 0, 1.0, INK)
        vc.tool("export", path=os.path.join(out, f"small-{px}.png"), scale=1)
        close(vc)
    sheet(vc, out, H, S)


def sheet(vc, out, H, S):
    """One presentation sheet at true pixel scale (exported at scale 1)."""
    W, Ht = 2000, 1130
    new(vc, W, Ht, "sheet")
    rect(vc, 0, 0, W, Ht, "#E3DED4")
    # The hero, large, on paper.
    rect(vc, 40, 40, 1050, 1050, PAPER)
    render(vc, H, 65, 65, 1.0, INK)
    X = 1130
    # On the dark ink ground, and solid black on white.
    rect(vc, X, 40, 405, 405, INK)
    render(vc, H, X + 22.5, 62.5, 0.36, PAPER)
    rect(vc, X + 425, 40, 405, 405, WHITE)
    render(vc, H, X + 447.5, 62.5, 0.36, BLACK)
    # The size ladder at true pixels: hero 128 and 64, small mark 32 and 16.
    for k, (ground, art) in enumerate(((PAPER, INK), (INK, PAPER))):
        y0 = 475 + k * 205
        rect(vc, X, y0, 830, 185, ground)
        x = X + 28
        cy = y0 + 92
        for sz in (128, 64):
            render(vc, H, x, cy - sz // 2, sz / 1000, art)
            x += sz + 44
        render(vc, S, x, cy - 16, 1.0, art)
        x += 32 + 44
        render(vc, pix16_layers(), x, cy - 8, 1.0, art)
        # the small mark magnified, to show its pixel grid
        render(vc, S, X + 830 - 28 - 128, cy - 64, 4.0, art)
    # The lockup.
    y0 = 885
    rect(vc, X, y0, 830, 205, PAPER)
    render(vc, H, X + 30, y0 + 32.5, 0.14, INK)
    text(vc, "SuperconducTED", X + 196, y0 + 112, 62, INK, "Medium", tracking=-10)
    text(vc, "NOISE ENGINE", X + 199, y0 + 152, 21, INK, "Medium", tracking=320)
    vc.tool("export", path=os.path.join(out, "sheet.png"), scale=1)
    close(vc)


def verify(vc, out, work):
    """Round-trip the shipped SVGs through the engine and magnify the favicons."""
    for name in ("hero.svg", "hero-black.svg", "small.svg"):
        vc.tool("open_file", path=os.path.join(out, name))
        vc.tool("export", path=os.path.join(work, "rt-" + name.replace(".svg", ".png")), scale=1)
        close(vc)
    magnify(os.path.join(out, "small-16.png"), os.path.join(work, "mag-small-16.png"), 16)
    magnify(os.path.join(out, "small-32.png"), os.path.join(work, "mag-small-32.png"), 8)


def main():
    work = os.path.join(HERE, "_work")
    os.makedirs(work, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    with VC(HERE) as vc:
        if mode in ("look", "all"):
            look(vc, work)
        if mode == "hero":
            H = hero_layers()
            new(vc, 1000, 1000, "look")
            rect(vc, 0, 0, 1000, 1000, PAPER)
            render(vc, H, 0, 0, 1.0, INK)
            vc.tool("export", path=os.path.join(work, "look-hero.png"), scale=1)
            close(vc)
        if mode == "lab":
            small_lab(vc, work)
        if mode in ("all", "ship"):
            deliverables(vc, HERE)
            verify(vc, HERE, work)
    print("ok", mode)


if __name__ == "__main__":
    main()

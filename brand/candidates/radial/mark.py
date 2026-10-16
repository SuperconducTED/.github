"""SuperconducTED, round 3, style RADIAL ORNAMENT / ASTROLABE: the mark and its colour-role API.

This module is the single source of the mark's geometry. It implements the shared contract in
../MARK_API.md, so one generator can draw this candidate in any palette:

    box(variant)                                   the art's bounding box in the unit square
    draw_mark(vc, x, y, size, colours, variant, mono)   draw it into VectorCraft's active document

Variants (VARIANTS):
    "hero"     the detailed mark, 128 px and up; unit square = the 1000-unit hero box.
    "small"    the bold 32-unit redraw for 24 to 32 px; unit square = its 32-unit grid.
    "small16"  the hand-hinted 16 px favicon (PIX16), drawn as one unit square per pixel cell;
               unit square = its 16-cell grid. Its cells land on whole pixels only when `size`
               is a whole multiple of 16 and x, y are whole numbers (size 16 at (0, 0) is the
               favicon exactly as shipped).

The colour rule (MARK_API.md): the accent is the range and only the range.
    hero     the [ and ] bent onto the dial, and the solid interval arc between them, whose
             graduation windows stay knocked out. The index, the chip, its trail, the rings,
             rods and coax stay ink.
    small    the [ and ] glyphs and the heavy band between them (the dial ring over the
             interval swells into the band, so that whole arc is the range); the rest of the
             ring and the chip stay ink.
    small16  the same cells as `small`: the ones marked "x" in PIX16.
No variant paints paper inside the art: every knockout is a real hole, so draw_mark draws no
background and colours["paper"] is never used for drawing.

How the accent is separated (the geometry is computed once, as an ordered list of layers):
    Each layer is (op, path data) with op "ink", "accent" or "knock", painted in order; a knock
    removes everything drawn so far inside its footprint. R, the whole mark, is the fold of all
    layers with "accent" treated as "ink": that is the one-colour mark, exactly as it has always
    been built.
    * Merged (mono=True, or accent equal to ink): R in colours["ink"], one compound path. This is
      the byte-for-byte path of the committed one-colour files.
    * Split, hero: A, the accent region, is its own fold in paint order: the dial rims
      clipped to the interval's wedge, then "accent" layers add and every knock or ink layer
      painted after the first accent layer removes (later ink covers the accent). The ink path
      is R minus A and the accent path is R minus the ink path, on top: the same region as A,
      but bounded by R's own segments, so it rasterises exactly as the one-colour mark does.
      The only new edge is where the support rod at bearing 30 stands on the arc (radius 302).
    * Split, small: the accent is the set of whole connected pieces of R inside the selector
      SMALL_ACCENT, whose edges run only through paper. The ink path is R minus SMALL_ACCENT,
      the accent path R intersected with it, so no edge of the art is cut or duplicated.
    * Split, small16: the "#" cells in ink, the "x" cells in the accent (no accent cell shares
      an edge with an ink cell).
"""
import math
import re

ROLES = ("ink", "paper", "accent", "tint-light", "tint-shade")
VARIANTS = ("hero", "small", "small16")
TINTS = (("tint-light", 0.20), ("tint-shade", 0.55))   # t(a) = (1 - a) * paper + a * ink

C = 500.0       # hero art box is 1000 x 1000 units, centre (C, C)
HERO_UNITS = 1000.0
SMALL_UNITS = 32.0
PIX_UNITS = 16.0

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


def R(x0, y0, x1, y1):
    """Axis-aligned rectangle from corner (x0, y0) to corner (x1, y1)."""
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


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
    """The hero as an ordered list of (op, path data), op in 'ink' | 'accent' | 'knock'.
    Order is paint order: a knock removes everything drawn so far inside its footprint.
    'accent' layers are the range (step 9); in one colour they are ink like the rest."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))        # noqa: E731
    accent = lambda *d: L.append(("accent", J(*d)))  # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))    # noqa: E731

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
    ink(dial_rims(), *dial_ticks())

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

    # 9. The reported interval, in the accent: the dial goes solid between the brackets,
    #    its graduations open as windows, and the brackets close it.
    accent(sector(DIAL_IRIM[0], DIAL_RIM[1], B_LO, B_HI))
    knock(*ticks_in(B_LO + 1.0, B_HI - 1.0))
    r_a, r_b, t, arm = 234.0, 321.0, W_HEAVY, 24.0
    knock(*bracket(B_LO, +1, r_a, r_b, t, arm, grow=5.5), *bracket(B_HI, -1, r_a, r_b, t, arm, grow=5.5))
    accent(*bracket(B_LO, +1, r_a, r_b, t, arm), *bracket(B_HI, -1, r_a, r_b, t, arm))

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


def dial_rims():
    """The dial's outer and inner rims (drawn with the ticks in step 3 of hero_layers)."""
    return J(annulus(DIAL_RIM[1], DIAL_RIM[0]), annulus(DIAL_IRIM[1], DIAL_IRIM[0]))


def interval_wedge():
    """The interval's wedge from the centre out to the flange: bearings B_LO to B_HI, its
    outer side a polyline with vertices at most 30 degrees apart (so it clears the dial)."""
    n = int(math.ceil((B_HI - B_LO) / 30.0))
    return poly([(C, C)] + [pol(FLANGE[0], B_LO + (B_HI - B_LO) * k / n) for k in range(n + 1)])


def hero_accent_layers(layers):
    """A, the hero's accent region, as a fold: the dial rims clipped to the interval's wedge,
    then accent_fold. The rims and the solid sector are the same circles approximated by
    different Bezier segments, so the drawn mark's edge along the interval is the envelope of
    both; taking the rims into A gives A that same edge (without them, R minus A leaves
    hairline ink slivers up to 0.08 units thick along the arc). The wedge's straight sides
    fall inside the bracket halos, which knock them out again."""
    return [("ink", dial_rims()), ("clip", interval_wedge())] + accent_fold(layers)


def accent_fold(layers):
    """The accent region as its own fold, in paint order: 'accent' layers add, and every
    knock or ink layer painted after the first accent layer removes (ink painted later
    covers the accent). Layers before the first accent layer cannot touch it."""
    out, started = [], False
    for op, d in layers:
        if op == "accent":
            started = True
            out.append(("ink", d))
        elif started:
            out.append(("knock", d))
    return out


# ---------------------------------------------------------------- the small companion
# A separate bold redraw on a 32-unit grid (1 unit = 1 px at 32, 0.5 px at 16). The interval
# runs from twelve to three o'clock so both bracket glyphs are axis-aligned and land on whole
# pixels at 32 and at 16 px.
SC = 16.0                                     # centre of the 32-unit grid
S_RING = (15.0, 13.0)                         # the dial ring, outer and inner radius
S_BAND = (10.6, 15.0, 0.0, 90.0)              # the heavy band: inner, outer radius, bearings
S_BAND_CLIP = [(0, 0, 20.6, 32), (0, 11.4, 32, 32)]          # cut back from the glyph halos
S_HALOS = [(13.5, -1, 20.5, 10), (22, 11.5, 33, 18.5)]       # clearances round the glyphs
S_OPEN = [(16, 0, 18, 8), (18, 0, 20, 2), (18, 6, 20, 8)]    # '[' upright at the top
S_CLOSE = [(24, 14, 32, 16), (24, 12, 26, 14), (30, 12, 32, 14)]   # ']' on its side, right
S_CHIP = (16, 10, 6, 6, 1.0)                  # x, y, w, h, corner radius
# The accent selector: two rectangles whose edges run only through paper (each at least
# 0.9 units clear of any art), so they take the glyphs and the band, with the ring arc it
# swells from, as whole pieces: left edge in the '[' halo (x 13.5 to 16), y = 9 between the
# '[' foot (y 8) and the chip (y 10), x = 23 between the chip (x 22) and the ']' (x 24) and
# left of the band's inner edge (x 23.96 at y 9), y = 17 between the ']' (y 16) and the
# ring's cut end (y 18.5). Top and right edges lie outside the grid.
SMALL_ACCENT = [(15, -1, 33, 9), (23, 9, 33, 17)]


def small_layers():
    """The chosen 32-unit redraw (small_e of the quality loop). The '[' stands upright at
    the top, the ']' lies on its side at the right (each glyph is radial, as on the hero).
    Between them the dial swells into a heavy band; the chip sits two units off centre
    toward it. One-colour layers only: the accent is taken out by SMALL_ACCENT."""
    L = []
    ink = lambda *d: L.append(("ink", J(*d)))      # noqa: E731
    knock = lambda *d: L.append(("knock", J(*d)))  # noqa: E731
    c = SC
    ink(sector(*S_BAND, c, c))
    knock(*[R(*q) for q in S_BAND_CLIP])
    ink(annulus(*S_RING, c, c))
    knock(*[R(*q) for q in S_HALOS])
    ink(*[R(*q) for q in S_OPEN + S_CLOSE])
    ink(rrect(*S_CHIP))
    return L


# The 16 px favicon is hinted by hand as pixel art: every shape lands on whole pixels.
# "#" is an ink cell, "x" an accent cell (the brackets and the band), "." is paper.
PIX16 = [
    "........xx......",
    ".....##.x.x.....",
    "...##...x.xxx...",
    "..#.....xx.xxx..",
    "..#.........xx..",
    ".#......###..xx.",
    ".#......###.x..x",
    ".#......###.xxxx",
    ".#..............",
    ".#............#.",
    ".#............#.",
    "..#..........#..",
    "..#..........#..",
    "...##......##...",
    ".....######.....",
    "................",
]


def pix16_cells(roles="#x", rows=PIX16):
    """The unit squares of the cells whose character is in `roles`, in row-major order."""
    sq = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in roles:
                sq.append(R(x, y, x + 1, y + 1))
    return sq


def pix16_layers(rows=PIX16):
    """Pixel art as one path of unit squares (16-unit grid), every filled cell."""
    return [("ink", J(*pix16_cells("#x", rows)))]


# ---------------------------------------------------------------- the API
def box(variant="hero"):
    """The art's bounding box (x0, y0, x1, y1) inside the unit square that draw_mark scales.
    Derived from the geometry: the hero's outermost shape is the flange; the small mark's
    extremes are the ring (left, bottom) and the glyphs (top, right); small16's are its cells."""
    if variant == "hero":
        lo, hi = (C - FLANGE[0]) / HERO_UNITS, (C + FLANGE[0]) / HERO_UNITS
        return (lo, lo, hi, hi)
    if variant == "small":
        rects = S_OPEN + S_CLOSE + [(S_CHIP[0], S_CHIP[1], S_CHIP[0] + S_CHIP[2], S_CHIP[1] + S_CHIP[3])]
        r = S_RING[0]
        x0 = min([SC - r] + [q[0] for q in rects])
        y0 = min([SC - r] + [q[1] for q in rects])
        x1 = max([SC + r] + [q[2] for q in rects])
        y1 = max([SC + r] + [q[3] for q in rects])
        return (x0 / SMALL_UNITS, y0 / SMALL_UNITS, x1 / SMALL_UNITS, y1 / SMALL_UNITS)
    if variant == "small16":
        cells = [(x, y) for y, row in enumerate(PIX16) for x, ch in enumerate(row) if ch != "."]
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        return (min(xs) / PIX_UNITS, min(ys) / PIX_UNITS, (max(xs) + 1) / PIX_UNITS, (max(ys) + 1) / PIX_UNITS)
    raise ValueError(f"unknown variant {variant!r}; this mark has {VARIANTS}")


def _hex(c):
    c = c.strip().lstrip("#")
    if len(c) != 6:
        raise ValueError(f"colour must be #rrggbb, got {c!r}")
    return tuple(int(c[k:k + 2], 16) for k in (0, 2, 4))


def resolve_colours(colours):
    """The full role map: 'ink' is required; a missing 'accent' falls back to ink (the mark
    then draws in one colour); missing tints are mixed from paper and ink when paper is
    given, t(a) = (1 - a) * paper + a * ink per sRGB channel, rounded to the nearest level.
    This mark never draws with paper or the tints; they are resolved for completeness."""
    out = dict(colours)
    if "ink" not in out:
        raise ValueError("colours needs at least 'ink'")
    out.setdefault("accent", out["ink"])
    if "paper" in out:
        p, i = _hex(out["paper"]), _hex(out["ink"])
        for name, a in TINTS:
            if name not in out:
                out[name] = "#" + "".join(f"{round((1 - a) * p[k] + a * i[k]):02X}" for k in range(3))
    return out


def draw_mark(vc, x, y, size, colours, variant="hero", mono=False):
    """Draw the mark into VectorCraft's ACTIVE document, its unit square mapped to the square
    with top-left (x, y) and side `size` (points, y down). Returns the ids it drew, bottom to
    top: the ink path, then the accent path when the accent is drawn separately.

    One compound path in colours['ink'] when mono=True or when the accent equals the ink
    (case-insensitive): exactly the committed one-colour drawing. Otherwise two paths, the
    accent (the range) on top of the ink, never overlapping. No background, no strokes, no
    opacity; paper is never painted inside the art."""
    col = resolve_colours(colours)
    split = (not mono) and col["accent"].lower() != col["ink"].lower()
    ink_ids, accent_ids = draw_parts(vc, x, y, size, col["ink"], col["accent"], variant, split)
    return ink_ids + accent_ids


def draw_parts(vc, x, y, size, ink, accent, variant="hero", split=True):
    """draw_mark's engine, which also lets a check force the split with accent == ink.
    Returns (ink ids, accent ids); the accent list is empty when not split."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant {variant!r}; this mark has {VARIANTS}")
    if variant == "hero":
        s = size / HERO_UNITS
        layers = hero_layers()
        if not split:
            return render(vc, layers, x, y, s, ink), []
        # ink = R - A; accent = R - ink, so that every edge of the accent except its join
        # with the rod at bearing 30 is a verbatim segment of R and rasterises exactly as in
        # the one-colour mark (R intersected with A would be the same region, but its edges
        # are recut curves whose anti-aliasing differs by a subsample here and there).
        whole = render(vc, layers, x, y, s, ink)
        keep = _dup(vc, whole)
        cut = render(vc, hero_accent_layers(layers), x, y, s, ink)
        vc.cmd("select.set", ids=keep + cut)
        ink_ids = vc.cmd("object.pathfinder.minusFront")["ids"]
        vc.cmd("select.set", ids=whole + _dup(vc, ink_ids))
        accent_ids = vc.cmd("object.pathfinder.minusFront")["ids"]
        vc.cmd("select.set", ids=accent_ids)
        vc.cmd("object.arrange.bringToFront")
        return _paint(vc, ink_ids, ink), _paint(vc, accent_ids, accent)
    if variant == "small":
        s = size / SMALL_UNITS
        layers = small_layers()
        if not split:
            return render(vc, layers, x, y, s, ink), []
        sel = J(*[R(*q) for q in SMALL_ACCENT])
        ink_ids = render(vc, layers + [("knock", sel)], x, y, s, ink)
        return ink_ids, render(vc, layers + [("clip", sel)], x, y, s, accent)
    s = size / PIX_UNITS
    if not split:
        return render(vc, pix16_layers(), x, y, s, ink), []
    return (render(vc, [("ink", J(*pix16_cells("#")))], x, y, s, ink),
            render(vc, [("ink", J(*pix16_cells("x")))], x, y, s, accent))


# ---------------------------------------------------------------- VectorCraft plumbing
TOK = re.compile(r"[MLCAZ]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")
BOOLEAN = {"ink": "object.pathfinder.unite", "accent": "object.pathfinder.unite",
           "knock": "object.pathfinder.minusFront", "clip": "object.pathfinder.intersect"}


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


def _dup(vc, ids):
    """A copy of the objects `ids`, in place, just above them; returns the copies' ids."""
    vc.cmd("select.set", ids=ids)
    return vc.cmd("edit.duplicate")["ids"]


def _paint(vc, ids, colour):
    vc.cmd("select.set", ids=ids)
    vc.cmd("paint.setFill", color=colour)
    vc.cmd("paint.setStroke", none=True)
    return ids


def render(vc, layers, ox, oy, s, colour):
    """Paint the layers at offset (ox, oy) and scale s with real booleans; returns ids.
    'ink' and 'accent' unite, 'knock' subtracts, 'clip' intersects, in order; the result is
    filled with `colour` and has no stroke."""
    acc = None
    for op, d in layers:
        if not d.strip():
            continue
        pid = vc.tool("draw_path", d=xf(d, ox, oy, s), fill=colour, stroke="none")["id"]
        if acc is None:
            if op in ("ink", "accent"):
                acc = [pid]
            else:
                vc.cmd("edit.clear", ids=[pid])
            continue
        vc.cmd("select.set", ids=acc + [pid])
        acc = vc.cmd(BOOLEAN[op])["ids"]
    return _paint(vc, acc, colour)

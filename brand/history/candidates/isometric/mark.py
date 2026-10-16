"""SuperconducTED logo, round 3, isometric candidate: the mark, behind the shared colour-role API.

This module is the single source of the drawing: every number of the geometry lives here, and
`build.py` (the deliverables) and the brand generator (`brand/tools/build_brand.py`) both draw
through `draw_mark`. It follows `brand/candidates/MARK_API.md`.

The drawing
-----------
A 3D model of a dilution-refrigerator chandelier, projected with one orthographic camera
(azimuth 0, elevation 22 degrees) and painted back to front in flat facets: six plates of
decreasing diameter joined by support rods, eight coaxial lines with an attenuator on every
plate, a pulse-tube cold head, the still pot, a helical heat exchanger and the mixing-chamber
pot. Below the coldest plate hangs the calibration dial (a flat face in a graduated bezel); its
centre, on the chandelier's axis, is the aim point where a dashed ghost of the chip sits (the
frozen snapshot). The chip package has drifted off it and twisted, at the end of a dotted trail
of kept calibrations. Two extruded square brackets stand on the dial face with a tinted,
graduated range zone between them: the interval the engine reports.

The small variant is a separate bold redraw on a 16-unit grid (ring, drifted chip, brackets).

Public interface
----------------
ROLES                     the five colour roles of MARK_API.md.
box(variant)              the visible art's bounding box inside the unit square.
draw_mark(vc, x, y, size, colours, variant, mono, knockouts)
                          draws into VectorCraft's active document; returns the ids drawn.
transform(variant, x, y, size)
                          the (scale, x offset, y offset) that maps model units to the page
                          for that unit square, for placing things relative to the model.
resolve(colours)          the five roles with the missing tints mixed in.
colours_used(colours, variant, mono)
                          every colour draw_mark paints: the roles in use plus, with a distinct
                          accent, the accent's two facet mixes (not roles; a colour checker that
                          allows only the five roles must add these).
on_dark(colours)          the same colours for a dark ground: ink and paper swapped, which
                          inverts the tint ladder (t becomes 1 minus t).
INK, PAPER, NEUTRAL       the brief's two neutrals and the neutral colour set (accent = ink).

Colour roles: what wears which colour
-------------------------------------
Every primitive carries a tone, 0 to 3 (0 = lightest face, 3 = full ink), and range primitives
also carry `acc`, the name of their piece ("[", "]" or "zone").

| tone | machine and measurement (all but the range) | range (brackets and zone, `acc`) |
|------|---------------------------------------------|----------------------------------|
| 0    | paper: top faces, the dial face, halos      | paper (the brackets' lit tops)   |
| 1    | tint-light (faces turned left)              | mix(paper, accent, 0.20)         |
| 2    | tint-shade (faces turned right)             | mix(paper, accent, 0.55)         |
| 3    | ink: all line work, the die, bolts          | accent                           |

mix(p, q, a) = (1 - a) p + a q per sRGB channel, rounded to the nearest integer. The tints
default to TINT_COVERAGE (0.20 and 0.55), exactly the coverage values the neutral drawing has
always used, so the defaults reproduce it. The accent ladder uses the same two coverage values,
so with accent = ink every range primitive gets the colour it has in the neutral drawing. If a
caller passes its own tint-light or tint-shade, the machine uses them and the range keeps the
0.20 and 0.55 mixes of the accent.

The range, the only thing that wears the accent:
* hero: both extruded brackets, every face (the front caps in accent, the side faces in the
  accent mixes, the tops in paper) and every edge line of them; the range zone on the dial face
  (its fill at mix(paper, accent, 0.20)), its far edge, its front edge and its 25 graduations.
* small: the two brackets (their knockout halos stay paper).
Everything else (plates, rods, coax, attenuators, pots, helix, flange, dial face and bezel,
graduations of the bezel, guide circle, aim point, plumb line, hangers, chip, die, qubits, bond
wires, connectors, ghost, trail; the small mark's ring, notch and chip) stays ink, tints, paper.

One colour (mono=True): only colours["ink"] remains. Tones 0 and 1 become knockouts, tone 2 is
hatched with 1 px lines, tone 3 is solid, and the accent plays no part. With the default
knockouts="cut" the knockouts are real holes: the art is painted with a sentinel colour for
the holes, every stroke is outlined, VectorCraft's pathfinder merge keeps only the topmost
colour of every visible region, and the sentinel regions are deleted.

Contract extension (the one deviation from MARK_API.md)
-------------------------------------------------------
knockouts="paint" (only with mono=True) paints the knockouts in colours["paper"] instead of
cutting them. It is a cheaper raster preview on a known ground, and it is how the committed
hero-white-on-black.png has always been drawn; cutting changes the geometry slightly, so a cut
version on a black square is not pixel-identical to that file.
"""
import functools
import math
import random
import re

ROLES = ("ink", "paper", "accent", "tint-light", "tint-shade")
TINT_COVERAGE = {"tint-light": 0.20, "tint-shade": 0.55}   # a in t(a) = (1 - a) paper + a ink
VARIANTS = ("hero", "small")

PAPER = "#F2EEE6"
INK = "#1A1D24"
NEUTRAL = {"ink": INK, "paper": PAPER, "accent": INK}

_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ----------------------------------------------------------------------------------------
# Colour
# ----------------------------------------------------------------------------------------
def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    """Colour a moved a fraction t of the way to colour b, per RGB channel, rounded."""
    ca, cb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def resolve(colours, need=("ink", "paper", "accent")):
    """The colour set with the optional tints filled in.

    Inputs: a dict of role -> "#rrggbb"; `need` lists the roles that must be present.
    Output: a new dict; a missing tint is t(a) = mix(paper, ink, a), a from TINT_COVERAGE (only
    when both paper and ink are given). Raises KeyError for a missing role and ValueError for a
    value that is not #rrggbb or a role that MARK_API.md does not define.
    """
    unknown = set(colours) - set(ROLES)
    if unknown:
        raise ValueError(f"unknown colour roles {sorted(unknown)}; the roles are {ROLES}")
    missing = [r for r in need if r not in colours]
    if missing:
        raise KeyError(f"colours lacks {missing}")
    for role, value in colours.items():
        if not isinstance(value, str) or not _HEX.match(value):
            raise ValueError(f"colours[{role!r}] = {value!r} is not #rrggbb")
    out = dict(colours)
    if "ink" in out and "paper" in out:
        for role, a in TINT_COVERAGE.items():
            out.setdefault(role, mix(out["paper"], out["ink"], a))
    return out


def on_dark(colours):
    """The colour set for a dark ground: ink and paper swapped, which inverts the tint ladder.

    An accent equal to the old ink follows it (so the neutral set stays neutral), any other
    accent is kept. Given tints are dropped so they mix again from the swapped pair: tint-light
    becomes mix(old ink, old paper, 0.20), i.e. 80 % ink, and tint-shade 45 % ink.
    """
    c = resolve(colours)
    accent = c["paper"] if c["accent"].lower() == c["ink"].lower() else c["accent"]
    return {"ink": c["paper"], "paper": c["ink"], "accent": accent}


# ----------------------------------------------------------------------------------------
# Camera: orthographic, azimuth 0, elevation PHI above the horizon.
# World: x right, y away from the viewer, z up. Screen units: X right, Y down.
# A point at polar angle th (degrees) on a circle: th = 0 faces the viewer, +90 is right.
# ----------------------------------------------------------------------------------------
PHI = math.radians(22.0)
SP, CP = math.sin(PHI), math.cos(PHI)
VIEW = (0.0, -CP, SP)          # unit vector from the scene toward the camera
SPLIT = 22.0                   # light from the left: cylinder sides change tone at this angle

# Stroke weights in screen units (the hero is fitted at about 200 px per unit, so W1 is ~4 px)
W1 = 0.021     # silhouettes of the big parts: plates, ring, brackets, chip package
W2 = 0.0105    # internal edges and small parts
W3 = 0.0050    # detail: ticks, bolts, bond wires, hatching, ghosts
WC_OUT, WC_IN = 0.021, 0.0085   # coaxial line: ink casing and its light core
WH_OUT, WH_IN = 0.016, 0.0060   # heat-exchanger tube


def pr(p):
    x, y, z = p
    return (x, -(z * CP + y * SP))


def depth(p):
    """Larger is nearer the camera."""
    x, y, z = p
    return -y * CP + z * SP


def polar(r, th, z, c=(0.0, 0.0)):
    t = math.radians(th)
    return (c[0] + r * math.sin(t), c[1] - r * math.cos(t), z)


def arc(c, r, z, th0, th1, n=None):
    """Projected points of a horizontal circle from th0 to th1 (degrees, inclusive)."""
    if n is None:
        n = max(6, int(abs(th1 - th0) / 360.0 * max(24, r * 260)))
    return [pr(polar(r, th0 + (th1 - th0) * i / n, z, c)) for i in range(n + 1)]


# Primitive constructors: F = filled region (list of rings), L = stroked polyline.
def F(rings, tone, hatch=90.0):
    return {"k": "F", "rings": rings, "tone": tone, "hatch": hatch}


def L(pts, tone, w, closed=False, cap="round"):
    return {"k": "L", "pts": pts, "tone": tone, "w": w, "closed": closed, "cap": cap}


def as_range(out, start, part):
    """Flag every primitive appended to `out` since index `start` as part of the range; `part`
    ("[", "]" or "zone") names which piece, so a test can check each piece on its own."""
    for p in out[start:]:
        p["acc"] = part


def dashed(pts, on, off, tone, w):
    """Split a polyline into dash segments of length `on` separated by `off` (screen units)."""
    out, cur, pos, drawing = [], [pts[0]], 0.0, True
    seg_left = on
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        d = math.hypot(x1 - x0, y1 - y0)
        t = 0.0
        while d - t > seg_left:
            t += seg_left
            p = (x0 + (x1 - x0) * t / d, y0 + (y1 - y0) * t / d)
            if drawing:
                cur.append(p)
                out.append(L(cur, tone, w))
            cur = [p]
            drawing = not drawing
            seg_left = on if drawing else off
        seg_left -= d - t
        if drawing:
            cur.append((x1, y1))
        else:
            cur = [(x1, y1)]
    if drawing and len(cur) > 1:
        out.append(L(cur, tone, w))
    return out


def area(poly):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))


def clip_convex(subject, clipper):
    """Sutherland-Hodgman: subject polygon clipped by a convex polygon."""
    if area(clipper) < 0:
        clipper = clipper[::-1]
    out = subject
    for (ax, ay), (bx, by) in zip(clipper, clipper[1:] + clipper[:1]):
        inp, out = out, []
        if not inp:
            break

        def inside(p):
            return (bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax) >= 0

        def cross(p, q):
            dx, dy = q[0] - p[0], q[1] - p[1]
            ex, ey = bx - ax, by - ay
            den = ex * dy - ey * dx
            t = (ex * (ay - p[1]) - ey * (ax - p[0])) / den
            return (p[0] + t * dx, p[1] + t * dy)
        for i, cur in enumerate(inp):
            prev = inp[i - 1]
            if inside(cur):
                if not inside(prev):
                    out.append(cross(prev, cur))
                out.append(cur)
            elif inside(prev):
                out.append(cross(prev, cur))
    return out


def hull(pts):
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and ((h[-1][0] - h[-2][0]) * (p[1] - h[-2][1])
                                   - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0])) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, hi = half(pts), half(pts[::-1])
    return lo[:-1] + hi[:-1]


# ----------------------------------------------------------------------------------------
# Solids
# ----------------------------------------------------------------------------------------
def shade(n):
    """Tone of a face from its outward normal: top faces lightest, faces turned right darkest."""
    if n[2] > 0.7:
        return 0
    return 2 if n[0] > 0.30 else 1


def vcyl(out, c, r, z0, z1, top=True, tones=None, wsil=W2, wint=W3, top_tone=0):
    """Vertical cylinder from z0 up to z1 at centre c. Visible: front half of the side, and
    the top face when `top` (things that end under a plate pass top=False)."""
    tl, tr = tones or (1, 2)
    left = arc(c, r, z1, -90, SPLIT) + arc(c, r, z0, SPLIT, -90)
    right = arc(c, r, z1, SPLIT, 90) + arc(c, r, z0, 90, SPLIT)
    out.append(F([left], tl))
    out.append(F([right], tr))
    if top:
        out.append(F([arc(c, r, z1, 0, 360)], top_tone))
        out.append(L(arc(c, r, z1, 90, 270) + arc(c, r, z0, -90, 90), 3, wsil, closed=True))
        out.append(L(arc(c, r, z1, -90, 90), 3, wint))
    else:
        out.append(L([pr(polar(r, -90, z1, c))] + arc(c, r, z0, -90, 90) + [pr(polar(r, 90, z1, c))], 3, wsil))


def disc(out, c, R, z, t, wsil=W1, wint=W2):
    vcyl(out, c, R, z - t, z, top=True, wsil=wsil, wint=wint)


def cuboid(out, c, z0, a, b, h, beta, wsil=W1, wint=W2, tones=None):
    """Box of footprint a (along U) by b (along V), height h; U at angle beta in plan.
    Returns the top-face mapper (u, v) -> world point, for surface detail."""
    bt = math.radians(beta)
    U = (math.cos(bt), math.sin(bt), 0.0)
    V = (-math.sin(bt), math.cos(bt), 0.0)

    def P(u, v, z):
        return (c[0] + u * U[0] + v * V[0], c[1] + u * U[1] + v * V[1], z)
    zt = z0 + h
    sides = [((a / 2, -b / 2), (a / 2, b / 2), U), ((a / 2, b / 2), (-a / 2, b / 2), V),
             ((-a / 2, b / 2), (-a / 2, -b / 2), (-U[0], -U[1], 0.0)),
             ((-a / 2, -b / 2), (a / 2, -b / 2), (-V[0], -V[1], 0.0))]
    proj = []
    for (u0, v0), (u1, v1), n in sides:
        if n[0] * VIEW[0] + n[1] * VIEW[1] > 1e-6:
            q = [pr(P(u0, v0, zt)), pr(P(u1, v1, zt)), pr(P(u1, v1, z0)), pr(P(u0, v0, z0))]
            tone = shade(n) if tones is None else min(3, shade(n) + tones.get("side_shift", 0))
            out.append(F([q], tone))
            out.append(L(q, 3, wint, closed=True))
            proj += q
    topq = [pr(P(-a / 2, -b / 2, zt)), pr(P(a / 2, -b / 2, zt)), pr(P(a / 2, b / 2, zt)), pr(P(-a / 2, b / 2, zt))]
    out.append(F([topq], 0 if tones is None else tones.get("top", 0)))
    out.append(L(topq, 3, wint, closed=True))
    proj += topq
    out.append(L(hull(proj), 3, wsil, closed=True))
    return lambda u, v: P(u, v, zt)


def cuboid_ghost(out, c, z0, a, b, h, beta, on, off, w):
    """Dashed outline of a box (its visible edges), for earlier positions of the chip."""
    bt = math.radians(beta)
    U = (math.cos(bt), math.sin(bt))
    V = (-math.sin(bt), math.cos(bt))

    def P(u, v, z):
        return pr((c[0] + u * U[0] + v * V[0], c[1] + u * U[1] + v * V[1], z))
    zt = z0 + h
    corners = [(-a / 2, -b / 2), (a / 2, -b / 2), (a / 2, b / 2), (-a / 2, b / 2)]
    top = [P(u, v, zt) for u, v in corners]
    out += dashed(top + [top[0]], on, off, 3, w)
    # front vertical edges and bottom front edges: the two corners nearest the viewer
    near = sorted(corners, key=lambda uv: depth((c[0] + uv[0] * U[0] + uv[1] * V[0],
                                                  c[1] + uv[0] * U[1] + uv[1] * V[1], 0)))[-3:]
    for u, v in near:
        out += dashed([P(u, v, zt), P(u, v, z0)], on, off, 3, w)
    i = corners.index(near[-1])
    for j in (i - 1, (i + 1) % 4):
        out += dashed([P(*corners[i], z0), P(*corners[j], z0)], on, off, 3, w)


def prism(out, profile, O, U, N, d, cap_tone=3, wcap=W2, wside=W2):
    """Extrude a CCW (u right, w up) profile: point = O + u*U + w*Z + n*N, n in [0, d].
    The n = 0 cap faces the viewer. Side faces are painted far to near, the cap last."""
    def P(u, w, n):
        return (O[0] + u * U[0] + n * N[0], O[1] + u * U[1] + n * N[1], O[2] + w)
    faces = []
    m = len(profile)
    for i in range(m):
        (u0, w0), (u1, w1) = profile[i], profile[(i + 1) % m]
        du, dw = u1 - u0, w1 - w0
        ln = math.hypot(du, dw)
        nu, nw = dw / ln, -du / ln
        n3 = (nu * U[0], nu * U[1], nw)
        if n3[0] * VIEW[0] + n3[1] * VIEW[1] + n3[2] * VIEW[2] <= 1e-6:
            continue
        q3 = [P(u0, w0, 0), P(u1, w1, 0), P(u1, w1, d), P(u0, w0, d)]
        dep = sum(depth(p) for p in q3) / 4
        faces.append((dep, [pr(p) for p in q3], shade(n3)))
    for _, q, tone in sorted(faces, key=lambda f: f[0]):
        out.append(F([q], tone))
        out.append(L(q, 3, wside, closed=True))
    cap = [pr(P(u, w, 0)) for u, w in profile]
    out.append(F([cap], cap_tone))
    out.append(L(cap, 3, wcap, closed=True))


def rod(out, c, r, z0, z1, washer=True):
    if washer:
        disc(out, c, r * 1.9, z0 + 0.012, 0.012, wsil=W3, wint=W3)
    vcyl(out, c, r, z0 + 0.012, z1, top=False, wsil=W2)


def coax(out, pts3d):
    pts = [pr(p) for p in pts3d]
    out.append(L(pts, 3, WC_OUT))
    out.append(L(pts, 1, WC_IN))


def smooth(t):
    return t * t * (3 - 2 * t)


def coax_gap(a, b, n=28, bow=0.0, loop=0.0):
    """3D path from polar a = (r, th, z) down to b, vertical at both ends (an S-bend). With
    loop > 0 the line also throws one service loop of that radius in its tangent plane."""
    pts = []
    for i in range(n + 1):
        t = i / n
        s = smooth(t)
        r = a[0] + (b[0] - a[0]) * s + bow * math.sin(math.pi * t)
        th = a[1] + (b[1] - a[1]) * s
        z = a[2] + (b[2] - a[2]) * t
        p = polar(r, th, z)
        if loop and 0.30 < t < 0.70:
            u = (t - 0.30) / 0.40                  # 0..1 once round the loop
            ang = 2 * math.pi * u
            tt = math.radians(th)
            tang = (math.cos(tt), math.sin(tt))
            off_t = loop * math.sin(ang)
            off_z = loop * (1 - math.cos(ang))
            p = (p[0] + off_t * tang[0], p[1] + off_t * tang[1], p[2] + off_z)
        pts.append(p)
    return pts


def bezier3(p0, p1, p2, p3, n=36):
    out = []
    for i in range(n + 1):
        t = i / n
        mt = 1 - t
        out.append(tuple(mt ** 3 * a + 3 * mt * mt * t * b + 3 * mt * t * t * c + t ** 3 * d
                         for a, b, c, d in zip(p0, p1, p2, p3)))
    return out


# ----------------------------------------------------------------------------------------
# The machine: plates, gaps, the ring stage. All lengths in world units.
# ----------------------------------------------------------------------------------------
# Plates, top flange first, mixing-chamber plate last: radius, thickness, and the clear gap
# below each plate. The ring (the dial) sits RING_GAP below the last plate, at z = 0.
RADII = [0.94, 0.84, 0.74, 0.64, 0.55, 0.47]
THICK = [0.115, 0.058, 0.058, 0.052, 0.048, 0.080]
GAPS = [0.48, 0.48, 0.44, 0.42, 0.40]
RING_GAP = 0.95


def _plates():
    z = RING_GAP + THICK[5]
    out = [None] * 6
    out[5] = (RADII[5], z, THICK[5])
    for k in range(4, -1, -1):
        z = z + GAPS[k] + THICK[k]
        out[k] = (RADII[k], z, THICK[k])
    return out


PLATES = _plates()      # (radius, z of top face, thickness)
BOLTS = [30, 24, 22, 20, 18, 16]          # bolt heads around each plate
RODS = [  # support rods per gap (below plate k): angles, radius, rod radius
    ([-84, -10, 82, 180], 0.75, 0.030),
    ([-78, 84, 180], 0.65, 0.027),
    ([-86, -2, 80, 180], 0.56, 0.024),
    ([-80, 84, 180], 0.47, 0.021),
    ([-84, 2, 86, 180], 0.40, 0.018),
]
N_COAX = 8
COAX_BASE = [8.0 + 7.5 * i for i in range(N_COAX)]          # degrees, front-right sector
COAX_SHIFT = [0.0, 8.0, -3.0, 9.0, -2.0, 5.0]               # per plate: S-bends between plates
COAX_INSET = 0.10
COAX_TO_CHIP = (2, 4, 6)                                    # lines that continue to the chip
COAX_LOOPS = {(1, 1): 0.075, (1, 5): 0.07, (3, 3): 0.06, (0, 7): 0.065}   # (gap, line): loop radius
ATT_R, ATT_H = 0.026, 0.066                                  # attenuator on each plate
HX_C = (-0.25 * math.sin(math.radians(38)), -0.25 * math.cos(math.radians(38)))  # heat exchanger axis
PT_POS = (0.52, -48.0)                                       # pulse-tube cold head (r, th)

# The calibration dial hangs below the mixing-chamber plate: a flat dial face inside a raised,
# graduated bezel ring. Its centre, straight below the chandelier's axis, is the aim point: where
# the frozen snapshot says the chip is.
DIAL_R = 0.96                     # dial face radius (inside the bezel)
BEZ_RO, BEZ_H, BEZ_T = 1.17, 0.05, 0.11   # bezel outer radius, height above the face, rim depth
RC = (DIAL_R + BEZ_RO) / 2        # hangers land on the bezel here
CHIP_A, CHIP_H = 0.40, 0.085
DRIFT = [  # (x, y, yaw): the snapshot (square on the aim point), then the chip now
    (0.00, 0.00, 0.0),
    (0.37, -0.150, 24.0),
]
BR_H, BR_S, BR_L, BR_D = 0.64, 0.105, 0.19, 0.16   # bracket height, stroke, serif, depth
BR_Y = -0.14                      # the brackets' front plane
BR_X = (-0.40, 0.85)              # outer faces of the [ and the ]
BR_YAW = 20.0                     # each bracket turned toward the viewer by this much
ZONE_DEPTH = 0.50                 # depth of the tinted range zone behind the brackets' front plane
# The drift trail: every calibration the engine kept, as dots on the dial face, joined in time
# order from the frozen snapshot (the centre) to where the chip is now. Waypoints, then a seeded
# Brownian bridge between them, so the path wanders but always ends exactly on each waypoint.
TRAIL_WAYPOINTS = [(0.0, 0.0), (-0.13, 0.04), (-0.26, 0.15), (-0.11, 0.31), (0.12, 0.27), (0.25, 0.06), (0.37, -0.15)]
TRAIL_SEED, TRAIL_STEPS, TRAIL_SIGMA, TRAIL_DOT_EVERY = 11, 7, 0.014, 3


def plate_coax(k, i):
    R = PLATES[k][0]
    return (R - COAX_INSET - 0.018 * (i % 2), COAX_BASE[i] + COAX_SHIFT[k] + 1.2 * i * (k % 2))


def through_hole(out, c, rh, z, t):
    """A hole through a plate: its back wall in shade, the opening below it in ink."""
    e0 = arc(c, rh, z, 0, 360, 40)
    e1 = arc(c, rh, z - t, 0, 360, 40)
    out.append(F([e0], 2))
    thru = clip_convex(e1, e0)
    if len(thru) > 2:
        out.append(F([thru], 3))
    out.append(L(e0, 3, W3, closed=True))


def plate(out, k):
    R, z, t = PLATES[k]
    disc(out, (0, 0), R, z, t)
    # bolt heads around the rim
    rb = R - 0.042
    for j in range(BOLTS[k]):
        th = j * 360.0 / BOLTS[k] + 7
        out.append(F([arc(polar(rb, th, 0), 0.015, z, 0, 360, 10)], 3))
    # lightening holes, and the bore the heat exchanger passes through
    holes = {1: [(0.50, -150, 0.07), (0.52, 150, 0.065)], 2: [(0.46, -150, 0.06), (0.47, 145, 0.06)],
             4: [(math.hypot(*HX_C), -38.0, 0.165)]}
    for rh_pos, th, rh in holes.get(k, []):
        through_hole(out, polar(rh_pos, th, 0)[:2], rh, z, t)
    if k == 5:   # the mixing-chamber plate is a breadboard: a grid of tapped holes
        g = 0.075
        for i in range(-7, 8):
            for j in range(-7, 8):
                x, y = i * g, j * g
                r = math.hypot(x, y)
                if r > R - 0.09 or r < 0.06:
                    continue
                if math.hypot(x - HX_C[0], y - HX_C[1]) < 0.20:
                    continue
                out.append(F([arc((x, y), 0.0105, z, 0, 360, 8)], 2))


def gap_items(k):
    """Everything between plate k (above) and plate k+1 (below), as (depth, prims) items."""
    items = []
    Ra, za, ta = PLATES[k]
    Rb, zb, tb = PLATES[k + 1]
    zbot = za - ta
    rods, rr, rrad = RODS[k]
    for th in rods:
        o = []
        c = polar(rr, th, 0)[:2]
        rod(o, c, rrad, zb, zbot)
        items.append((depth(polar(rr, th, zb)), o))
    # coax: from plate k down to an attenuator on plate k+1
    for i in range(N_COAX):
        ra, tha = plate_coax(k, i)
        rb, thb = plate_coax(k + 1, i)
        o = []
        cb = polar(rb, thb, 0)[:2]
        vcyl(o, cb, ATT_R, zb, zb + ATT_H, wsil=W2, wint=W3)
        o.append(L(arc(cb, ATT_R, zb + ATT_H * 0.45, -90, 90, 8), 3, W3))
        bow = (0.05, -0.03, 0.035, -0.02)[i % 4]
        loop = COAX_LOOPS.get((k, i), 0.0)
        pts = coax_gap((ra, tha, zbot), (rb, thb, zb + ATT_H), n=60 if loop else 28, bow=bow, loop=loop)
        coax(o, pts)
        items.append((depth(polar((ra + rb) / 2, (tha + thb) / 2, 0)) + 0.001 * i, o))
    if k in (0, 1):   # pulse-tube cold head: wide first stage, narrow second stage
        o = []
        c = polar(PT_POS[0], PT_POS[1], 0)[:2]
        r = 0.125 if k == 0 else 0.080
        disc(o, c, r * 1.35, zb + 0.03, 0.03, wsil=W2, wint=W3)
        vcyl(o, c, r, zb + 0.03, zbot, top=False, wsil=W2)
        vcyl(o, c, r * 1.25, zbot - 0.05, zbot, top=False, wsil=W2)
        for f in (0.35, 0.55):
            zz = zb + 0.03 + (zbot - zb) * f
            o.append(L(arc(c, r, zz, -90, 90, 16), 3, W3))
        items.append((depth(polar(PT_POS[0], PT_POS[1], zb)), o))
    if k in (3, 4):   # still pot, helical heat exchanger, mixing-chamber pot
        o_back, o_front = [], []
        if k == 3:
            ztop = zbot - 0.12
            vcyl(o_back, HX_C, 0.15, ztop, zbot, top=False, wsil=W2)
            o_back.append(L(arc(HX_C, 0.15, ztop + 0.05, -90, 90, 20), 3, W3))
            h0, h1 = ztop, zb
            turns, phase = 2.4, 0.0
        else:
            h0, h1 = zbot, zb + 0.12
            turns, phase = 2.4, 0.0
        rod(o_back, HX_C, 0.026, h1, h0, washer=False)
        helix(o_back, o_front, HX_C, 0.105, h0, h1, turns, phase)
        o = o_back + o_front
        if k == 4:
            pot = []
            vcyl(pot, HX_C, 0.14, zb, zb + 0.12, wsil=W2, wint=W3)
            pot.append(L(arc(HX_C, 0.14, zb + 0.045, -90, 90, 20), 3, W3))
            o = pot + o
        items.append((depth((HX_C[0], HX_C[1], zb)), o))
    return items


def helix(o_back, o_front, c, rh, z0, z1, turns, phase):
    n = int(turns * 64)
    runs, cur, cur_front = [], [], None
    for i in range(n + 1):
        a = phase + 2 * math.pi * turns * i / n
        p = (c[0] + rh * math.sin(a), c[1] - rh * math.cos(a), z0 + (z1 - z0) * i / n)
        front = math.cos(a) > 0
        if cur_front is None:
            cur_front = front
        if front != cur_front:
            cur.append(pr(p))
            runs.append((cur_front, cur))
            cur, cur_front = [pr(p)], front
        else:
            cur.append(pr(p))
    runs.append((cur_front, cur))
    for front, pts in runs:
        if len(pts) < 2:
            continue
        tgt = o_front if front else o_back
        tgt.append(L(pts, 3, WH_OUT))
        tgt.append(L(pts, 0 if front else 2, WH_IN))


def dial_stage(out):
    zf = 0.0                      # dial face
    zt = BEZ_H                    # bezel top
    zb = BEZ_H - BEZ_T            # bezel bottom
    c = (0.0, 0.0)
    # the face, then what is printed on it
    out.append(F([arc(c, DIAL_R, zf, 0, 360)], 0))
    # the reported range: a tinted zone on the face between the brackets, edged in ink
    t = math.radians(BR_YAW)
    xl = BR_X[0] + BR_S * math.cos(t)
    xr = BR_X[1] - BR_S * math.cos(t)
    y0, y1 = BR_Y - 0.02, BR_Y + ZONE_DEPTH
    zone = [pr((xl, y0, zf)), pr((xr, y0, zf)), pr((xr, y1, zf)), pr((xl, y1, zf))]
    n0 = len(out)
    out.append(F([zone], 1, hatch=0.0))
    out.append(L([zone[3], zone[2]], 3, W3))
    as_range(out, n0, "zone")     # the zone and its far edge wear the accent
    for rr in (0.66,):            # a concentric guide circle, very fine
        out.append(L(arc(c, rr, zf, 0, 360), 3, W3 * 0.8, closed=True))
    # the aim point: a small ring with a dot, straight below the chandelier's axis
    out.append(L(arc(c, 0.05, zf, 0, 360, 24), 3, W2, closed=True))
    out.append(F([arc(c, 0.016, zf, 0, 360, 12)], 3))
    # the zone's front edge carries a fine graduation: the interval is a measured span
    n0 = len(out)
    out.append(L([zone[0], zone[1]], 3, W2))
    n = 24
    for j in range(n + 1):
        x = xl + (xr - xl) * j / n
        ln = 0.06 if j % 6 == 0 else 0.03
        out.append(L([pr((x, y0, zf)), pr((x, y0 + ln, zf))], 3, W3, cap="butt"))
    as_range(out, n0, "zone")     # the front edge and its graduations wear the accent
    # inner wall of the bezel (back half), the bezel top with its graduations, the outer rim
    inner_l = arc(c, DIAL_R, zt, 180, 270) + arc(c, DIAL_R, zf, 270, 180)
    inner_r = arc(c, DIAL_R, zt, 90, 180) + arc(c, DIAL_R, zf, 180, 90)
    out.append(F([inner_l], 2))
    out.append(F([inner_r], 1))
    left = arc(c, BEZ_RO, zt, -90, SPLIT) + arc(c, BEZ_RO, zb, SPLIT, -90)
    right = arc(c, BEZ_RO, zt, SPLIT, 90) + arc(c, BEZ_RO, zb, 90, SPLIT)
    out.append(F([left], 1))
    out.append(F([right], 2))
    out.append(F([arc(c, BEZ_RO, zt, 0, 360), arc(c, DIAL_R, zt, 360, 0)], 0))
    for j in range(120):          # graduations: minor every 3 degrees, major every 15
        th = j * 3.0
        major = j % 5 == 0
        ln = 0.095 if major else 0.050
        p0 = pr(polar(BEZ_RO - 0.018, th, zt))
        p1 = pr(polar(BEZ_RO - 0.018 - ln, th, zt))
        out.append(L([p0, p1], 3, W2 if major else W3, cap="butt"))
    for th in (0, 90, 180, 270):  # cardinal ticks cross the bezel, in line with the crosshair
        out.append(L([pr(polar(DIAL_R + 0.012, th, zt)), pr(polar(BEZ_RO - 0.004, th, zt))], 3, W1, cap="butt"))
    out.append(L(arc(c, BEZ_RO, zt, 90, 270) + arc(c, BEZ_RO, zb, -90, 90), 3, W1, closed=True))
    out.append(L(arc(c, BEZ_RO, zt, -90, 90), 3, W2))
    out.append(L(arc(c, DIAL_R, zt, 0, 360), 3, W2, closed=True))
    out.append(L(arc(c, DIAL_R, zf, 90, 270), 3, W3))


def trail_points():
    """Brownian bridge through the waypoints: on each leg, Gaussian steps of TRAIL_SIGMA are
    summed into a walk w(i), and the bridge w(i) - (i/n) w(n) is added to the straight leg, so
    the noise is zero at both ends of every leg."""
    rng = random.Random(TRAIL_SEED)
    pts = []
    for (ax, ay), (bx, by) in zip(TRAIL_WAYPOINTS, TRAIL_WAYPOINTS[1:]):
        n = TRAIL_STEPS
        wx, wy = [0.0], [0.0]
        for _ in range(n):
            wx.append(wx[-1] + rng.gauss(0.0, TRAIL_SIGMA))
            wy.append(wy[-1] + rng.gauss(0.0, TRAIL_SIGMA))
        for i in range(n):
            t = i / n
            pts.append((ax + (bx - ax) * t + wx[i] - t * wx[n], ay + (by - ay) * t + wy[i] - t * wy[n]))
    pts.append(TRAIL_WAYPOINTS[-1])
    return pts


def chip_stage(out):
    zf = 0.0
    (x0, y0, b0), (x2, y2, b2) = DRIFT
    # the trail of kept calibrations, then the frozen snapshot as a dashed ghost on the aim point
    tp = trail_points()
    out.append(L([pr((x, y, zf)) for x, y in tp], 3, W3))
    for i, (x, y) in enumerate(tp[:-1]):
        if i % TRAIL_DOT_EVERY == 0 and i > 0:
            out.append(F([arc((x, y), 0.019, zf, 0, 360, 12)], 3))
    cuboid_ghost(out, (x0, y0), zf, CHIP_A, CHIP_A, CHIP_H, b0, 0.030, 0.020, W2)
    top = cuboid(out, (x2, y2), zf, CHIP_A, CHIP_A, CHIP_H, b2, tones={"side_shift": 1, "top": 1})
    a = CHIP_A

    def sq(h, tone, w=None):
        q = [pr(top(u, v)) for u, v in ((-h, -h), (h, -h), (h, h), (-h, h))]
        out.append(F([q], tone))
        if w:
            out.append(L(q, 3, w, closed=True))
        return q
    sq(a * 0.36, 0, W3)                    # recess
    sq(a * 0.23, 3, W3)                    # the die
    for s in (-1, 1):                      # wire bonds from die to recess, three per side
        for f in (-0.12, 0.0, 0.12):
            for p0, p1 in (((a * 0.23 * s, a * f), (a * 0.34 * s, a * f * 1.3)),
                           ((a * f, a * 0.23 * s), (a * f * 1.3, a * 0.34 * s))):
                out.append(L([pr(top(*p0)), pr(top(*p1))], 3, W3))
    # qubits: a 2 x 2 lattice of crosses with couplers, drawn in paper on the ink die
    qs = [(-0.09, -0.09), (0.09, -0.09), (0.09, 0.09), (-0.09, 0.09)]
    for (u0, v0), (u1, v1) in zip(qs, qs[1:] + qs[:1]):
        out.append(L([pr(top(a * u0, a * v0)), pr(top(a * u1, a * v1))], 0, W3))
    for u, v in qs:
        h = a * 0.045
        out.append(L([pr(top(a * u - h, a * v)), pr(top(a * u + h, a * v))], 0, W2))
        out.append(L([pr(top(a * u, a * v - h)), pr(top(a * u, a * v + h))], 0, W2))
    conns = []                             # SMA connectors along the back edge
    for u in (-0.12, 0.0, 0.12):
        p = top(a * u, a * 0.40)
        o = []
        vcyl(o, p[:2], 0.026, p[2], p[2] + 0.065, wsil=W2, wint=W3)
        conns.append((depth(p), o, (p[0], p[1], p[2] + 0.065)))
    for _, o, _ in sorted(conns, key=lambda x: x[0]):
        out += o
    return [c[2] for c in conns]


def brackets(out):
    """The two extruded brackets, every face and edge of them flagged as the range."""
    n0 = len(out)
    profile = [(0, 0), (BR_L, 0), (BR_L, BR_S), (BR_S, BR_S), (BR_S, BR_H - BR_S),
               (BR_L, BR_H - BR_S), (BR_L, BR_H), (0, BR_H)]
    t = math.radians(BR_YAW)
    # [: serifs point right and a little toward the viewer; extruded away from the viewer
    prism(out, profile, (BR_X[0], BR_Y, 0.0), (math.cos(t), -math.sin(t), 0.0),
          (math.sin(t), math.cos(t), 0.0), BR_D, cap_tone=3, wcap=W2, wside=W2)
    as_range(out, n0, "[")
    # ]: the mirror image
    n0 = len(out)
    prism(out, profile, (BR_X[1], BR_Y, 0.0), (-math.cos(t), -math.sin(t), 0.0),
          (-math.sin(t), math.cos(t), 0.0), BR_D, cap_tone=3, wcap=W2, wside=W2)
    as_range(out, n0, "]")


def flange_top(out):
    R, z, t = PLATES[0]
    items = []
    # SMA feedthroughs where the coax enter
    for i in range(N_COAX):
        r, th = plate_coax(0, i)
        o = []
        vcyl(o, polar(r, th, 0)[:2], 0.032, z, z + 0.05, wsil=W2, wint=W3)
        items.append((depth(polar(r, th, z)), o))
    # central pumping port with a lip and its open bore
    o = []
    vcyl(o, (0, 0), 0.15, z + 0.03, z + 0.24, wsil=W1, wint=W2)
    vcyl(o, (0, 0), 0.19, z + 0.24, z + 0.275, wsil=W1, wint=W2)
    bore = arc((0, 0), 0.12, z + 0.275, 0, 360)
    o.append(F([bore], 3))
    items.append((depth((0, 0, z)), o))
    # a ring of KF ports around the central port, and two larger service ports
    for r, th, rp, hp in ((0.60, -64, 0.075, 0.15), (0.64, 132, 0.07, 0.15), (0.38, -150, 0.05, 0.10),
                          (0.38, 150, 0.05, 0.10), (0.40, 90, 0.05, 0.10), (0.40, -90, 0.05, 0.10),
                          (0.66, -118, 0.045, 0.09), (0.70, 170, 0.045, 0.09)):
        o = []
        c = polar(r, th, 0)[:2]
        vcyl(o, c, rp, z, z + hp, wsil=W2, wint=W3)
        vcyl(o, c, rp * 1.4, z + hp, z + hp + 0.025, wsil=W2, wint=W3)
        o.append(F([arc(c, rp * 0.7, z + hp + 0.025, 0, 360, 24)], 3))
        items.append((depth(polar(r, th, z)), o))
    # a raised boss around the central port, with its own bolt circle
    boss = []
    disc(boss, (0, 0), 0.27, z + 0.03, 0.03, wsil=W2, wint=W3)
    for j in range(12):
        boss.append(F([arc(polar(0.235, j * 30 + 15, 0), 0.011, z + 0.03, 0, 360, 8)], 3))
    items.append((depth((0, 0, z)) - 0.001, boss))
    for _, o in sorted(items, key=lambda x: x[0]):
        out += o


def scene():
    """The hero: every primitive in painter's order, in screen units (y down)."""
    out = []
    dial_stage(out)
    conn_tops = chip_stage(out)
    # below the mixing-chamber plate: three hangers to the bezel, the axis, three coax to the chip
    items = []
    R5, z5, t5 = PLATES[5]
    zb5 = z5 - t5
    for th in (-125, 125, 180):
        o = []
        a = polar(R5 - 0.07, th, zb5)
        b = polar(RC, th, BEZ_H)
        pts = [pr(a), pr(b)]
        o.append(L(pts, 3, 0.028))
        o.append(L(pts, 1, 0.011))
        o.append(F([arc(b[:2], 0.032, BEZ_H, 0, 360, 16)], 3))
        items.append((depth(b), o))
    axis = dashed([pr((0, 0, zb5)), pr((0, 0, 0.0))], 0.06, 0.025, 3, W3)
    items.append((depth((0, 0, 0)), axis))
    for j, ct in enumerate(conn_tops):
        o = []
        r, th = plate_coax(5, COAX_TO_CHIP[j])
        a = polar(r, th, zb5)
        p1 = (a[0], a[1], a[2] - 0.45)
        p2 = (ct[0], ct[1], ct[2] + 0.38)
        coax(o, bezier3(a, p1, p2, ct))
        items.append((depth(ct) + 0.5, o))
    for _, o in sorted(items, key=lambda x: x[0]):
        out += o
    brackets(out)
    for k in range(5, -1, -1):
        plate(out, k)
        if k > 0:
            for _, o in sorted(gap_items(k - 1), key=lambda x: x[0]):
                out += o
    flange_top(out)
    return out


# ----------------------------------------------------------------------------------------
# The small mark: a separate bold redraw on a 16-unit grid (chip between brackets on a ring)
# ----------------------------------------------------------------------------------------
SM_GRID = 16.0                                 # the small mark's unit square, in grid units
SM_RING = (11.7, 6.3, 2.45, 5.12, 1.55)        # centre y; outer rx, ry; inner rx, ry
SM_CHIP = (10.1, 9.0, 2.35, 1.18, 1.9)         # top-face centre x, y; half width; half height; side
SM_BR = (0.8, 1.85, 3.7, 1.65, 2.0, 13.6)      # outer x, stem, serif reach, serif thickness, top, bottom
SM_HALO = 1.05


def small_mark():
    """The favicon companion on a 16-unit grid: the dial as an elliptical ring, the chip as an
    isometric block drifted right of the ring's centre, the two brackets standing on the ring.
    Ink only, brackets in the accent; knockout halos (tone 0, the ground) keep the parts apart
    at 16 px."""
    out = []
    cx, cy = 8.0, SM_RING[0]
    ro_x, ro_y, ri_x, ri_y = SM_RING[1:]

    def ell(rx, ry, n=72):
        return [(cx + rx * math.sin(2 * math.pi * i / n), cy + ry * math.cos(2 * math.pi * i / n)) for i in range(n)]
    out.append(F([ell(ro_x, ro_y), ell(ri_x, ri_y)[::-1]], 3))
    # the aim point: a notch under the ring's front, on the centre line
    nx, ny = 8.0, cy + ro_y + 0.55
    out.append(F([[(nx - 1.15, ny + 1.25), (nx, ny), (nx + 1.15, ny + 1.25)]], 3))
    # the chip, drifted right of the centre: hexagon in ink, top face knocked out, die in ink
    bx, by, w, h, d = SM_CHIP
    hexa = [(bx - w, by), (bx, by - h), (bx + w, by), (bx + w, by + d), (bx, by + h + d), (bx - w, by + d)]
    out.append(L(hexa, 0, SM_HALO, closed=True))
    out.append(F([hexa], 3))
    k = 0.62   # inset of the knocked-out top face, leaving an ink rim
    top = [(bx - w + k * 1.6, by), (bx, by - h + k * 0.8), (bx + w - k * 1.6, by), (bx, by + h - k * 0.8)]
    out.append(F([top], 0))
    die = [(bx - w * 0.36, by), (bx, by - h * 0.36), (bx + w * 0.36, by), (bx, by + h * 0.36)]
    out.append(F([die], 3))
    out.append(L([(bx, by + h + 0.15), (bx, by + h + d - 0.35)], 0, 0.5, cap="butt"))
    # brackets: the range
    x0, st, sl, sw, yt, yb = SM_BR
    for side in (-1, 1):
        def X(x):
            return x if side < 0 else 16.0 - x
        pts = [(X(x0), yt), (X(x0 + sl), yt), (X(x0 + sl), yt + sw), (X(x0 + st), yt + sw),
               (X(x0 + st), yb - sw), (X(x0 + sl), yb - sw), (X(x0 + sl), yb), (X(x0), yb)]
        n0 = len(out)
        out.append(L(pts, 0, SM_HALO, closed=True))
        out.append(F([pts], 3))
        as_range(out, n0, "[" if side < 0 else "]")
    return out


@functools.lru_cache(maxsize=None)
def art(variant):
    """The primitives of a variant, built once. Treat the returned list as read-only."""
    if variant == "hero":
        return scene()
    if variant == "small":
        return small_mark()
    raise ValueError(f"variant must be one of {VARIANTS}, not {variant!r}")


# ----------------------------------------------------------------------------------------
# Placement
# ----------------------------------------------------------------------------------------
def bbox(prims):
    xs, ys = [], []
    for p in prims:
        pad = p.get("w", 0) / 2
        pts = [q for r in p["rings"] for q in r] if p["k"] == "F" else p["pts"]
        for x, y in pts:
            xs += [x - pad, x + pad]
            ys += [y - pad, y + pad]
    return min(xs), min(ys), max(xs), max(ys)


def fit(prims, x, y, w, h):
    """Scale and offset that centre the primitives' bounds in the box (x, y, w, h)."""
    x0, y0, x1, y1 = bbox(prims)
    S = min(w / (x1 - x0), h / (y1 - y0))
    return S, x + (w - S * (x1 - x0)) / 2 - S * x0, y + (h - S * (y1 - y0)) / 2 - S * y0


def transform(variant, x, y, size):
    """(S, ox, oy): page point = (ox + S * X, oy + S * Y) for model point (X, Y), when the
    variant's unit square is drawn at top-left (x, y) with side `size`.

    hero: the unit square is the art's bounds (strokes included) contained and centred in the
    square, so the art touches its top and bottom (it is taller than wide).
    small: the unit square is the 16-unit design grid.
    """
    if variant == "small":
        return size / SM_GRID, x, y
    if variant == "hero":
        return fit(art("hero"), x, y, size, size)
    raise ValueError(f"variant must be one of {VARIANTS}, not {variant!r}")


def box(variant="hero"):
    """The visible art's bounding box (x0, y0, x1, y1) inside the unit square.

    Visible art: every primitive that is not ground-coloured (tone 0 shapes are paper in colour
    and holes in one colour), strokes included at half their width.
    """
    S, ox, oy = transform(variant, 0.0, 0.0, 1.0)
    x0, y0, x1, y1 = bbox([p for p in art(variant) if p["tone"] != 0])
    return (ox + S * x0, oy + S * y0, ox + S * x1, oy + S * y1)


# ----------------------------------------------------------------------------------------
# Emission: primitives to VectorCraft command batches
# ----------------------------------------------------------------------------------------
def hatch_lines(rings, ang, sp):
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    rot = [[(x * ca + y * sa, -x * sa + y * ca) for x, y in r] for r in rings]
    ys = [p[1] for r in rot for p in r]
    y = math.floor(min(ys) / sp) * sp + sp / 2
    segs = []
    while y < max(ys):
        xs = []
        for r in rot:
            for (x1, y1), (x2, y2) in zip(r, r[1:] + r[:1]):
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            if xs[j + 1] - xs[j] > 1e-4:
                segs.append([(xs[j], y), (xs[j + 1], y)])
        y += sp
    return [[(X * ca - Y * sa, X * sa + Y * ca) for X, Y in s] for s in segs]


HATCH_SP = 0.021


def steps_for(prims, S, ox, oy, pal, acc_pal=None):
    """VectorCraft command steps for the primitives. `pal` maps tone -> colour (or "hatch")
    for the machine; `acc_pal` (default `pal`) does the same for the range primitives."""
    steps = []
    acc_pal = acc_pal or pal

    def P(x, y):
        return f"{ox + S * x:.2f} {oy + S * y:.2f}"

    def add_fill(rings, col):
        parts = []
        for k, r in enumerate(rings):
            r = list(r)
            if (area(r) > 0) != (k == 0):     # outer ring one way, holes the other way
                r = r[::-1]
            parts.append("M" + " L".join(P(x, y) for x, y in r) + " Z")
        steps.append({"id": "path.create", "params": {"d": " ".join(parts)}})
        steps.append({"id": "paint.setFill", "params": {"color": col}})
        steps.append({"id": "paint.setStroke", "params": {"none": True}})

    def add_line(pts, col, w, closed=False, cap="round"):
        d = "M" + " L".join(P(x, y) for x, y in pts) + (" Z" if closed else "")
        steps.append({"id": "path.create", "params": {"d": d}})
        steps.append({"id": "paint.setFill", "params": {"none": True}})
        steps.append({"id": "paint.setStroke", "params": {"color": col}})
        steps.append({"id": "stroke.set", "params": {"weight": round(max(w * S, 0.05), 3), "cap": cap, "join": "round"}})

    for p in prims:
        pp = acc_pal if p.get("acc") else pal
        if p["k"] == "F":
            col = pp[p["tone"]]
            if col == "hatch":
                x0, y0, x1, y1 = bbox([p])
                if min(x1 - x0, y1 - y0) < 0.05:        # too small to hatch: solid
                    add_fill(p["rings"], pp[3])
                    continue
                add_fill(p["rings"], pp[0])
                for seg in hatch_lines(p["rings"], p["hatch"], HATCH_SP):
                    add_line(seg, pp[3], W3 * 0.9, cap="butt")
                continue
            add_fill(p["rings"], col)
        else:
            col = pp[p["tone"]]
            if col == "hatch":
                col = pp[0]
            add_line(p["pts"], col, p["w"], p["closed"], p["cap"])
    return steps


BATCH = 2400   # steps per command_batch call


def emit(vc, steps):
    """Run the steps in VectorCraft's active document; returns the ids of the created paths."""
    ids = []
    for i in range(0, len(steps), BATCH):
        r = vc.tool("command_batch", steps=steps[i:i + BATCH])
        if r.get("failed"):
            raise RuntimeError(f"batch failed: {str(r)[:400]}")
        ids += [s["result"]["id"] for s in r["results"]
                if isinstance(s.get("result"), dict) and "id" in s["result"]]
    return ids


def palettes(colours, mono=False, knockouts="cut"):
    """(pal, acc_pal): tone -> colour for the machine and for the range (see the module notes).

    mono=False: the colour version (the table in the module docstring).
    mono=True: tones 0 and 1 are knockouts (colours["paper"] with knockouts="paint", else a
    sentinel that draw_mark cuts away), tone 2 is "hatch", tone 3 is colours["ink"]; the range
    is drawn like the machine.
    """
    if not mono:
        c = resolve(colours)
        pal = {0: c["paper"], 1: c["tint-light"], 2: c["tint-shade"], 3: c["ink"]}
        acc = {0: c["paper"],
               1: mix(c["paper"], c["accent"], TINT_COVERAGE["tint-light"]),
               2: mix(c["paper"], c["accent"], TINT_COVERAGE["tint-shade"]),
               3: c["accent"]}
        return pal, acc
    if knockouts == "paint":
        c = resolve(colours, need=("ink", "paper"))
        hole = c["paper"]
    elif knockouts == "cut":
        c = resolve(colours, need=("ink",))
        hole = knockout_sentinel(c["ink"])
    else:
        raise ValueError(f"knockouts must be 'cut' or 'paint', not {knockouts!r}")
    pal = {0: hole, 1: hole, 2: "hatch", 3: c["ink"]}
    return pal, pal


def colours_used(colours, variant="hero", mono=False):
    """Every colour draw_mark paints for these colours, as upper-case #RRGGBB, for a caller that
    checks its files against an allowed set. In colour that is the roles in use plus, when the
    accent differs from ink, the accent's two facet mixes mix(paper, accent, 0.20) and
    mix(paper, accent, 0.55), which are not roles; in one colour it is the ink alone."""
    if mono:
        return {resolve(colours, need=("ink",))["ink"].upper()}
    pal, acc = palettes(colours)
    return {(acc if p.get("acc") else pal)[p["tone"]].upper() for p in art(variant)}


def knockout_sentinel(ink):
    """The colour the knockouts are painted in before they are cut: white, unless ink is white."""
    return "#000000" if ink.lower() == "#ffffff" else "#FFFFFF"


def _fill_of(vc, node):
    """The solid fill of a merged Path or Compound Path, as lowercase #rrggbb."""
    if node["kind"] == "Path":
        f = node.get("fill")
        return f.lower() if isinstance(f, str) else f
    full = vc.cmd("document.node", id=node["id"])
    for item in full.get("appearance", {}).get("items", []):
        if item.get("kind") == "fill":
            paint = item["paint"]
            if paint.get("type") != "solid":
                return paint.get("type")
            col = paint["color"]
            return "#" + "".join(f"{round(col[k] * 255):02x}" for k in "rgb")
    return None


def cut_knockouts(vc, ids, ink, hole):
    """Turn painted knockouts into holes: outline the strokes of `ids`, merge them (each visible
    region keeps its topmost colour), delete the regions filled with `hole`. Returns the ids of
    the merge result. Raises if anything other than ink and hole regions comes out."""
    vc.cmd("select.set", ids=ids)
    outlined = vc.cmd("object.path.outlineStroke")["ids"]
    vc.cmd("select.set", ids=outlined)
    merged = vc.cmd("object.pathfinder.merge")["ids"]
    holes = []
    for mid in merged:
        node = vc.cmd("document.node", id=mid, summary=True, depth=1)
        for child in (node.get("children", []) if node["kind"] == "Group" else [node]):
            if child["kind"] not in ("Path", "Compound Path"):
                raise RuntimeError(f"merge left a {child['kind']} (id {child['id']})")
            f = _fill_of(vc, child)
            if f == hole.lower():
                holes.append(child["id"])
            elif f != ink.lower():
                raise RuntimeError(f"merge left fill {f!r} (id {child['id']}), expected {ink} or {hole}")
    if holes:
        vc.cmd("edit.clear", ids=holes)
    return merged


# ----------------------------------------------------------------------------------------
# The API
# ----------------------------------------------------------------------------------------
def draw_mark(vc, x, y, size, colours, variant="hero", mono=False, knockouts="cut"):
    """Draw the mark into VectorCraft's ACTIVE document, its unit square mapped to the square
    with top-left (x, y) and side `size` (points, y down). Returns the ids of what it drew.

    colours: {"ink", "paper", "accent": "#rrggbb", optional "tint-light", "tint-shade"}; missing
             tints are mix(paper, ink, 0.20) and mix(paper, ink, 0.55). Paper is painted inside
             the art (top faces, the dial face, knockout halos), so pass the ground colour.
    variant: "hero" (128 px and up) or "small" (the 16 to 32 px redraw).
    mono:    True draws only colours["ink"] (accent and tints unused), with real knockouts.
    knockouts: "cut" (default, real holes) or "paint" (mono only: knockouts painted in
             colours["paper"]; the contract extension described in the module docstring).
    Returns: the created path ids (colour, or mono with "paint"), or the merge result's group
    id (mono with "cut"). Side effects: adds objects to the active document and changes its
    selection; draws no background.
    """
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}, not {variant!r}")
    if knockouts != "cut" and not mono:
        raise ValueError("knockouts applies to mono=True only")
    pal, acc = palettes(colours, mono, knockouts)
    S, ox, oy = transform(variant, x, y, size)
    ids = emit(vc, steps_for(art(variant), S, ox, oy, pal, acc))
    if mono and knockouts == "cut":
        return cut_knockouts(vc, ids, pal[3], pal[0])
    return ids

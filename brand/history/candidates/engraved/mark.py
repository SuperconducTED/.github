"""SuperconducTED round 3, style ENGRAVED EMBLEM / SEAL: the mark API (see ../MARK_API.md).

This module owns every number of the mark. The seal is computed as pure geometry in a
1000 x 1000 model box (centre 500, 500, y down); the small companion mark on a 32 x 32 grid.
`draw_mark` maps either box onto any square of VectorCraft's active document, in any palette;
`build.py` only lays out the deliverables and the sheet through it.

Public interface
  ROLES                     the colour roles of the shared API
  VARIANTS                  ("hero", "small"); no hand-hinted 16 px drawing
  box(variant)              the art's bounding box inside the unit square
  draw_mark(vc, x, y, size, colours, variant="hero", mono=False) -> ids of what it drew
  hero_art(vc)              the cached hero geometry and its lettering stats (build.py prints
                            them; calling it first also outlines the lettering before any
                            caller document is opened)

Story mapping (see NOTES.md):
  chandelier   the dilution refrigerator, six plates narrowing toward the coldest one,
               posts, coax bundles with loops and attenuators, still pot, heat-exchanger coil,
               mixing-chamber pot; the chip hangs below the lowest plate.
  dial         the seal's graduated inner ring; its index at six o'clock is where the frozen
               calibration snapshot says the chip is (a dashed plumb line leads to it).
  drifting chip the solid chip has swung off the plumb line; dotted outlines are its earlier
               positions, the dashed one is the snapshot.
  brackets     two heavy engraved [ ] around the chip and its trail; the same interval is
               inked on the dial between bracket-shaped ends.

Colour roles (the rule in MARK_API.md)
  accent   the range only: the two engraved brackets, and on the hero's dial the inked
           interval (the arc band) with its two bracket-shaped ends (spine and serif each).
           In the small mark: its two brackets.
  ink      everything else: all line work, the chip die, the index, ornaments, lettering.
  paper    only the small mark's disc behind its ring (non-mono), which keeps the favicon
           legible on dark tabs. The hero paints no paper: every light passage is a real gap.
  mono     one colour, colours["ink"], for fills and strokes alike; strokes stay strokes.
  tints    not used by this design (mixed per the contract, then ignored).

Model contract
  Art.lines : list of (stroke width, [points])  stroked open polylines, round caps and joins;
              always ink (no line belongs to the range)
  Art.fills : list of fill groups; a group is a list of contours, a contour is a list of
              ('M'|'L'|'C', [points]); nonzero fill; a group is emitted as one compound path
  Art.roles : the colour role of each fill group, parallel to Art.fills
  Emission order never depends on the colours (lines by width, then fills in drawing order),
  so a palette changes only fill and stroke values, never the path data or its order.
"""
import base64
import math
import re

ROLES = ("ink", "paper", "accent", "tint-light", "tint-shade")
VARIANTS = ("hero", "small")    # no hand-hinted "small16": 16 px is "small" at half size
TINT_MIX = {"tint-light": 0.20, "tint-shade": 0.55}   # t(a) = (1 - a) * paper + a * ink

FONT = "Space Grotesk"
CX = CY = 500.0
HERO_UNITS = 1000.0      # the hero's model box; draw_mark scales it to `size`
SMALL_UNITS = 32.0       # the small mark's grid


# ----------------------------------------------------------------------------------------
# Stroke weight hierarchy (model units; the hero is drawn at 1.024 px per unit)
# ----------------------------------------------------------------------------------------
W_HAIR = 0.85    # hatching, ruling, guilloche, ghost outlines
W_FINE = 1.3     # minor ticks, fine rules, cables, secondary contours
W_MED = 2.2      # primary contours (plates, pots, tubes), mid ticks
W_BOLD = 3.2     # shadow-side contours, bold rule, major ticks, the chip's hanger rod
W_HEAVY = 8.0    # outer seal ring (the brackets, index and chip die are solid fills)


# ----------------------------------------------------------------------------------------
# Art container
# ----------------------------------------------------------------------------------------
class Art:
    def __init__(self):
        self.lines = []
        self.fills = []
        self.roles = []

    def line(self, pts, w):
        if len(pts) >= 2:
            self.lines.append((round(w, 2), [(float(x), float(y)) for x, y in pts]))

    def lines_from(self, polys, w):
        for p in polys:
            self.line(p, w)

    def group(self, contours, role="ink"):
        assert role in ("ink", "accent"), role
        self.fills.append(contours)
        self.roles.append(role)


def poly_contour(pts):
    return [("M", [pts[0]])] + [("L", [p]) for p in pts[1:]]


def area(pts):
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))


def orient(pts, positive=True):
    return list(pts) if (area(pts) > 0) == positive else list(pts)[::-1]


def rot(p, c, ang):
    """Rotate p about c by ang degrees (positive = clockwise on screen, y down)."""
    a = math.radians(ang)
    co, si = math.cos(a), math.sin(a)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * co - dy * si, c[1] + dx * si + dy * co)


def polar(r, deg, c=(CX, CY)):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def arc_pts(r, d0, d1, c=(CX, CY), step=0.5):
    n = max(2, int(abs(d1 - d0) / step) + 1)
    return [polar(r, d0 + (d1 - d0) * k / (n - 1), c) for k in range(n)]


def ell_pts(cx, cy, a, b, t0, t1, step=2.0):
    n = max(2, int(abs(t1 - t0) / step) + 1)
    out = []
    for k in range(n):
        t = math.radians(t0 + (t1 - t0) * k / (n - 1))
        out.append((cx + a * math.cos(t), cy + b * math.sin(t)))
    return out


def dashed(pts, dash, gap):
    """Split a polyline into dashes of length `dash` separated by `gap` (dash ~0 gives dots)."""
    out, cur, pos, on = [], [pts[0]], 0.0, True
    period = dash if on else gap
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        s = 0.0
        while L - s > 1e-9:
            take = min(period - pos, L - s)
            s += take
            pos += take
            p = (x0 + (x1 - x0) * s / L, y0 + (y1 - y0) * s / L)
            if on:
                cur.append(p)
            if pos >= period - 1e-9:
                if on:
                    if len(cur) == 1:
                        cur.append((cur[0][0] + 0.01, cur[0][1]))
                    out.append(cur)
                on = not on
                pos = 0.0
                period = dash if on else gap
                cur = [p]
    if on and len(cur) >= 2:
        out.append(cur)
    return out


def dotted(pts, pitch):
    """Dots (zero-length round-capped dashes) every `pitch` along a polyline."""
    out, acc = [], pitch / 2
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        s = acc
        while s <= L:
            x, y = x0 + (x1 - x0) * s / L, y0 + (y1 - y0) * s / L
            out.append([(x - 0.01, y), (x + 0.01, y)])
            s += pitch
        acc = s - L
    return out


# ----------------------------------------------------------------------------------------
# Occlusion: convex polygons and axis-aligned ellipses; analytic segment clipping
# ----------------------------------------------------------------------------------------
class Occ:
    __slots__ = ("kind", "data", "bb", "sgn")

    def __init__(self, kind, data):
        self.kind, self.data = kind, data
        if kind == "p":
            xs = [p[0] for p in data]
            ys = [p[1] for p in data]
            self.bb = (min(xs), min(ys), max(xs), max(ys))
            self.sgn = 1.0 if area(data) > 0 else -1.0
        else:
            cx, cy, a, b = data
            self.bb = (cx - a, cy - b, cx + a, cy + b)
            self.sgn = 1.0


def inflate_convex(pts, m):
    if m == 0:
        return list(pts)
    pts = orient(pts, True)
    dd = [pts[0]]
    for q in pts[1:]:
        if math.hypot(q[0] - dd[-1][0], q[1] - dd[-1][1]) > 1e-6:
            dd.append(q)
    if len(dd) > 2 and math.hypot(dd[0][0] - dd[-1][0], dd[0][1] - dd[-1][1]) <= 1e-6:
        dd.pop()
    pts = dd
    n = len(pts)
    lines = []
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        L = math.hypot(ex, ey)
        # positive area in y-down coords: interior is on the left of (ex, ey) in math sense;
        # outward normal is (ey, -ex)/L
        nx, ny = ey / L, -ex / L
        lines.append(((ax + nx * m, ay + ny * m), (ex, ey)))
    out = []
    for i in range(n):
        (p, d), (q, e) = lines[i - 1], lines[i]
        den = d[0] * e[1] - d[1] * e[0]
        if abs(den) < 1e-9:
            out.append(q)
            continue
        t = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
        out.append((p[0] + d[0] * t, p[1] + d[1] * t))
    return out


def occ_poly(pts, m=0.0):
    return Occ("p", inflate_convex(pts, m))


def occ_rect(x0, y0, x1, y1, m=0.0):
    return Occ("p", [(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)])


def occ_ell(cx, cy, a, b, m=0.0):
    return Occ("e", (cx, cy, a + m, b + m))


def occ_capsule(p, q, r):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return [occ_ell(p[0], p[1], r, r)]
    nx, ny = -dy / L * r, dx / L * r
    return [Occ("p", [(p[0] + nx, p[1] + ny), (q[0] + nx, q[1] + ny), (q[0] - nx, q[1] - ny), (p[0] - nx, p[1] - ny)]),
            occ_ell(p[0], p[1], r, r), occ_ell(q[0], q[1], r, r)]


def occ_polyline(pts, r):
    out = []
    for p, q in zip(pts, pts[1:]):
        out += occ_capsule(p, q, r)
    return out


def inflate_occs(occs, m):
    out = []
    for o in occs:
        if o.kind == "e":
            cx, cy, a, b = o.data
            out.append(occ_ell(cx, cy, a, b, m))
        else:
            out.append(Occ("p", inflate_convex(o.data, m)))
    return out


def _iv(o, p, q):
    if o.kind == "e":
        cx, cy, a, b = o.data
        fx, fy = (p[0] - cx) / a, (p[1] - cy) / b
        gx, gy = (q[0] - p[0]) / a, (q[1] - p[1]) / b
        A = gx * gx + gy * gy
        B = 2 * (fx * gx + fy * gy)
        C = fx * fx + fy * fy - 1
        if A < 1e-14:
            return (0.0, 1.0) if C <= 0 else None
        disc = B * B - 4 * A * C
        if disc <= 0:
            return None
        r = math.sqrt(disc)
        t0, t1 = max(0.0, (-B - r) / (2 * A)), min(1.0, (-B + r) / (2 * A))
        return (t0, t1) if t0 < t1 else None
    poly, sgn = o.data, o.sgn
    t0, t1 = 0.0, 1.0
    n = len(poly)
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        fp = sgn * (ex * (p[1] - ay) - ey * (p[0] - ax))
        fq = sgn * (ex * (q[1] - ay) - ey * (q[0] - ax))
        if fp < 0 and fq < 0:
            return None
        if fp >= 0 and fq >= 0:
            continue
        t = fp / (fp - fq)
        if fp < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 >= t1:
            return None
    return (t0, t1)


def _bbx(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def clip(pts, occs=(), inside=None):
    """Return the parts of polyline `pts` outside every occluder in `occs` (and, when
    `inside` is given, inside that single region Occ)."""
    if len(pts) < 2:
        return []
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    pb = (min(xs), min(ys), max(xs), max(ys))
    cand = [o for o in occs if _bbx(o.bb, pb)]
    if not cand and inside is None:
        return [list(pts)]
    out, cur = [], None
    for p, q in zip(pts, pts[1:]):
        sb = (min(p[0], q[0]), min(p[1], q[1]), max(p[0], q[0]), max(p[1], q[1]))
        ivs = []
        for o in cand:
            if _bbx(o.bb, sb):
                iv = _iv(o, p, q)
                if iv:
                    ivs.append(iv)
        ivs.sort()
        keep, t = [], 0.0
        for a, b in ivs:
            if a > t:
                keep.append((t, a))
            t = max(t, b)
        if t < 1.0:
            keep.append((t, 1.0))
        if inside is not None:
            reg = _iv(inside, p, q)
            if not reg:
                keep = []
            else:
                keep = [(max(a, reg[0]), min(b, reg[1])) for a, b in keep if min(b, reg[1]) > max(a, reg[0])]
        for k, (a, b) in enumerate(keep):
            pa = (p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a)
            pb_ = (p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b)
            if a < 1e-9 and cur is not None:
                cur.append(pb_)
            else:
                if cur is not None and len(cur) >= 2:
                    out.append(cur)
                cur = [pa, pb_]
            if b < 1.0 - 1e-9:
                if cur is not None and len(cur) >= 2:
                    out.append(cur)
                cur = None
        if not keep:
            if cur is not None and len(cur) >= 2:
                out.append(cur)
            cur = None
    if cur is not None and len(cur) >= 2:
        out.append(cur)
    return [c for c in out if math.hypot(c[-1][0] - c[0][0], c[-1][1] - c[0][1]) > 0.3 or len(c) > 2]


def clip_pred(p, q, pred, step=0.5):
    """Parts of segment pq where pred(x, y) holds (sampled, ends refined by bisection)."""
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = max(2, int(L / step) + 1)
    at = lambda t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)  # noqa: E731
    vals = [pred(*at(k / (n - 1))) for k in range(n)]

    def refine(t_in, t_out):
        for _ in range(14):
            m = (t_in + t_out) / 2
            if pred(*at(m)):
                t_in = m
            else:
                t_out = m
        return t_in

    out, start = [], None
    for k in range(n):
        t = k / (n - 1)
        if vals[k] and start is None:
            start = 0.0 if k == 0 else refine(t, (k - 1) / (n - 1))
        if (not vals[k]) and start is not None:
            end = refine((k - 1) / (n - 1), t)
            out.append([at(start), at(end)])
            start = None
    if start is not None:
        out.append([at(start), at(1.0)])
    return out


# ----------------------------------------------------------------------------------------
# Engraving tone: Lambert shading of a vertical cylinder lit from the upper left
# ----------------------------------------------------------------------------------------
def tone(u):
    """Darkness 0..1 across a cylinder, u = -1 (left edge) .. 1 (right edge)."""
    u = max(-1.0, min(1.0, u))
    br = -0.5 * u + 0.866 * math.sqrt(max(0.0, 1 - u * u))
    T = min(1.0, 1.0 - br)
    if u > 0.86:                       # reflected light: engravers leave a lighter rim
        T -= 0.42 * (u - 0.86) / 0.14
    return max(0.0, T)


def tone_lines(xc, hw, ytop, ybot, pmin=2.7, tmin=0.1, wmin=0.8, wspan=1.1, x_lo=None, x_hi=None):
    """Vertical engraving lines across a cylinder of half width hw centred at xc.
    Local line density is tone(u)/pmin per unit; width grows with tone. Returns [(w, pts)]."""
    out, acc = [], 0.5
    x0 = xc - hw if x_lo is None else x_lo
    x1 = xc + hw if x_hi is None else x_hi
    dx = 0.2
    x = x0 + dx
    while x < x1 - 0.4:
        u = (x - xc) / hw
        T = tone(u)
        T = 0.0 if T < 0.035 else 0.16 + 0.84 * T
        acc += T / pmin * dx
        if acc >= 1.0:
            acc -= 1.0
            if T >= tmin:
                ya, yb = ytop(x), ybot(x)
                if yb - ya > 0.6:
                    out.append((round(wmin + wspan * T * T, 1), [(x, ya), (x, yb)]))
        x += dx
    return out


def cross_lines(xa, xb, ytop, ybot, ang=38.0, pitch=3.0, w=W_HAIR):
    """Diagonal cross-hatching inside the curved band x in [xa, xb], ytop(x) <= y <= ybot(x)."""
    out = []
    if xb <= xa:
        return out
    ys = [ytop(xa), ybot(xa), ytop(xb), ybot(xb)]
    y_lo, y_hi = min(ys) - 2, max(ys) + 2
    t = math.tan(math.radians(ang))
    c0 = y_lo - t * xb - 5
    c1 = y_hi - t * xa + 5
    pred = lambda x, y: xa <= x <= xb and ytop(x) <= y <= ybot(x)  # noqa: E731
    c = c0
    while c <= c1:
        p = (xa - 1, t * (xa - 1) + c)
        q = (xb + 1, t * (xb + 1) + c)
        out += [(w, s) for s in clip_pred(p, q, pred, 0.4)]
        c += pitch / math.cos(math.radians(ang))
    return out


# ----------------------------------------------------------------------------------------
# Layout constants
# ----------------------------------------------------------------------------------------
K = 0.075                                   # ellipse ratio of the slight view from above
# plates (face-centre y, half width a, band thickness t): top flange .. mixing chamber
PL = [(216.0, 196.0, 16.0), (298.0, 192.0, 10.0), (374.0, 186.0, 10.0),
      (444.0, 178.0, 10.0), (508.0, 168.0, 9.0), (568.0, 156.0, 12.0)]

R_RING = 493.0           # heavy outer ring
R_GUIL = 478.0           # guilloche rope centre
R_TXT_OUT = 467.0        # fine rule outside the lettering
R_TXT_IN = 403.0         # fine rule inside the lettering
R_BOLD = 397.0           # bold rule of the dial
R_TICK0 = 394.6          # ticks start here and run inward
R_INNER = 364.0          # inner rule of the dial
R_FIELD = 358.5          # ruled field

PIVOT = (500.0, 603.0)
ROD_L = 118.0            # pivot to holder centre
HOLD = 34.0              # holder half side
DIE = 17.0               # die half side
TRAIL = [(-11.0, "dots"), (0.0, "snapshot"), (9.0, "dots"), (20.0, "now")]


def plate_b(i):
    return PL[i][1] * K


def face_front(i, x):
    y, a, t = PL[i]
    u = (x - CX) / a
    return y + a * K * math.sqrt(max(0.0, 1 - u * u))


def face_back(i, x):
    y, a, t = PL[i]
    u = (x - CX) / a
    return y - a * K * math.sqrt(max(0.0, 1 - u * u))


def band_bot(i, x):
    return face_front(i, x) + PL[i][2]


def chip_centre(theta):
    return (PIVOT[0] + ROD_L * math.sin(math.radians(theta)), PIVOT[1] + ROD_L * math.cos(math.radians(theta)))


def holder_corners(theta, h=HOLD):
    c = chip_centre(theta)
    return [rot((c[0] + sx * h, c[1] + sy * h), c, -theta) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def bracket_geometry():
    xs = []
    for th, _ in TRAIL:
        xs += [p[0] for p in holder_corners(th)]
    x_in_l, x_in_r = min(xs) - 12.0, max(xs) + 12.0
    bar = 13.0
    return dict(xl=x_in_l - bar, xr=x_in_r + bar, yt=644.0, yb=800.0, bar=bar, serif=36.0)


# ----------------------------------------------------------------------------------------
# Generic engraved cylinder
# ----------------------------------------------------------------------------------------
def cylinder(art, xc, hw, top, y_bot, cap=False, w_side=(W_FINE, W_MED), w_bot=W_MED, pmin=2.7, shade=True,
             clip_occs=(), shadow=0.0):
    """A vertical cylinder of half width hw seen slightly from above.
    top: a number (the y of its lid, drawn as a full ellipse when cap) or a function x -> y
    (the edge of the plate it hangs from). Bottom: the front arc of its foot at y_bot.
    Returns occluders for its silhouette."""
    b = hw * K
    tf = top if callable(top) else (lambda x, y0=top: y0 + b * math.sqrt(max(0.0, 1 - ((x - xc) / hw) ** 2)))
    bf = lambda x: y_bot + b * math.sqrt(max(0.0, 1 - ((x - xc) / hw) ** 2))  # noqa: E731
    lines = []
    lines.append((w_side[0], [(xc - hw, tf(xc - hw)), (xc - hw, y_bot)]))
    lines.append((w_side[1], [(xc + hw, tf(xc + hw)), (xc + hw, y_bot)]))
    lines.append((w_bot, ell_pts(xc, y_bot, hw, b, 0, 180, 6)))
    if cap and not callable(top):
        lines.append((W_FINE, ell_pts(xc, top, hw, b, 180, 360, 6)))
        lines.append((W_FINE, ell_pts(xc, top, hw, b, 0, 180, 6)))
    if shade:
        lines += tone_lines(xc, hw, tf, bf, pmin=pmin)
        if hw >= 12:
            lines += cross_lines(xc + 0.5 * hw, xc + 0.86 * hw, lambda x: tf(x) + 1.0, lambda x: bf(x) - 1.0,
                                 ang=-35, pitch=3.0)
    if shadow > 0 and callable(top):
        yy = 1.6
        while yy < shadow:
            lines.append((W_HAIR, [(xc - hw + 0.8, tf(xc - hw + 0.8) + yy), (xc + hw - 0.8, tf(xc + hw - 0.8) + yy)]))
            yy += 1.7 + 0.12 * yy
    for w, p in lines:
        art.lines_from(clip(p, clip_occs), w)
    ytop = (top - b) if not callable(top) else min(top(xc - hw), top(xc), top(xc + hw))
    return [occ_rect(xc - hw, ytop, xc + hw, y_bot), occ_ell(xc, y_bot, hw, b)]


# ----------------------------------------------------------------------------------------
# The chandelier
# ----------------------------------------------------------------------------------------
def draw_plate(art, i, face_occs, casters=()):
    y, a, t = PL[i]
    b = a * K
    # face: back arc (behind whatever stands on it), front arc (the lit edge)
    art.lines_from(clip(ell_pts(CX, y, a, b, 180, 360, 1.0), face_occs), W_FINE)
    art.line(ell_pts(CX, y, a, b, 0, 180, 1.0), W_FINE)
    # machined rings on the face
    for f, w in ((0.86, W_HAIR), (0.62, W_HAIR)):
        art.lines_from(clip(ell_pts(CX, y, a * f, b * f, 0, 360, 1.5), face_occs), w)
    # engraved tone across the face, heavier toward the back right (away from the light)
    face = occ_ell(CX, y, a - 1.2, b - 0.9)
    k, dy = 0, -b + 1.6
    while dy < b - 1.0:
        half = a * math.sqrt(max(0.0, 1 - (dy / b) ** 2))
        x_s = CX + a * (0.12 + 0.30 * ((k * 3) % 5) / 4) - (1 - (dy + b) / (2 * b)) * 0.25 * a
        if x_s < CX + half - 6:
            art.lines_from(clip([(x_s, y + dy), (CX + half, y + dy)], face_occs, inside=face), 0.8)
        k += 1
        dy += 2.5
    # cast shadows of things standing on the face, thrown to the right and back
    for (sx, shw) in casters:
        sh = occ_ell(sx + 0.55 * shw, y - 0.25 * shw * K, 1.2 * shw, shw * K * 1.9)
        yy = sh.bb[1] + 0.8
        while yy < sh.bb[3]:
            seg = [(sh.bb[0] - 1, yy), (sh.bb[2] + 1, yy)]
            for part in clip(seg, face_occs, inside=sh):
                art.lines_from(clip(part, [], inside=face), 0.8)
            yy += 1.45
    # band: sides, heavy lower edge, engraved tone, cross-hatch in the core shadow
    art.line([(CX - a, y), (CX - a, y + t)], W_MED)
    art.line([(CX + a, y), (CX + a, y + t)], W_BOLD)
    art.line(ell_pts(CX, y + t, a, b, 0, 180, 1.0), W_BOLD)
    top = lambda x: face_front(i, x) + 0.9  # noqa: E731
    bot = lambda x: band_bot(i, x) - 0.9  # noqa: E731
    for w, p in tone_lines(CX, a, top, bot, pmin=2.5):
        art.line(p, w)
    for w, p in cross_lines(CX + 0.62 * a, CX + 0.9 * a, top, bot, ang=32, pitch=3.2):
        art.line(p, w)
    # bolt heads along the band, in the light: small rings
    for psi in range(10, 171, 16):
        x = CX + a * math.cos(math.radians(psi))
        if abs((x - CX) / a) > 0.9:
            continue
        yy = (face_front(i, x) + band_bot(i, x)) / 2
        art.line(ell_pts(x, yy, 1.6, 1.6, 0, 360, 30), W_HAIR)


def bundle_lines(centre_pts, offsets):
    """Offset a centreline along its normals (a ribbon of parallel coax)."""
    n = len(centre_pts)
    res = []
    for o in offsets:
        out = []
        for k in range(n):
            p0 = centre_pts[max(0, k - 1)]
            p1 = centre_pts[min(n - 1, k + 1)]
            dx, dy = p1[0] - p0[0], p1[1] - p0[1]
            L = math.hypot(dx, dy) or 1e-9
            nx, ny = dy / L, -dx / L
            out.append((centre_pts[k][0] + nx * o, centre_pts[k][1] + ny * o))
        res.append(out)
    return res


def cable_path(x0, y0, x1, y1, kind, side):
    """Centreline of a coax bundle from (x0, y0) to (x1, y1)."""
    pts = []
    if kind == "s":
        n = 40
        for k in range(n + 1):
            t = k / n
            s = (1 - math.cos(math.pi * t)) / 2
            x = x0 + (x1 - x0) * s + side * 9.0 * math.sin(math.pi * t) ** 2 * math.sin(2 * math.pi * t)
            pts.append((x, y0 + (y1 - y0) * t))
    elif kind == "bow":
        # a service bow: the semi-rigid coax swings out sideways and back
        n = 48
        for k in range(n + 1):
            t = k / n
            x = x0 + (x1 - x0) * t + side * 17.0 * math.sin(math.pi * t) ** 1.6
            pts.append((x, y0 + (y1 - y0) * t))
    elif kind == "dogleg":
        # straight down, a jog outward with rounded corners, straight down again
        n = 60
        for k in range(n + 1):
            t = k / n
            s_ = min(1.0, max(0.0, (t - 0.32) / 0.3))
            s_ = s_ * s_ * (3 - 2 * s_)
            pts.append((x0 + (x1 - x0) * s_, y0 + (y1 - y0) * t))
    else:
        pts = [(x0 + (x1 - x0) * k / 10, y0 + (y1 - y0) * k / 10) for k in range(11)]
    return pts


def draw_gap(art, i):
    """Everything hung between plate i and plate i+1. Returns occluders of things standing
    on plate i+1 (they hide its back edge and its machined rings)."""
    occs = []
    y2, a2, t2 = PL[i + 1]
    # support posts: two in front, two behind (thinner, no tone)
    for psi in (40.0, 140.0, 200.0, 340.0):
        rp = 0.86 * a2
        x = CX + rp * math.cos(math.radians(psi))
        front = math.sin(math.radians(psi)) > 0
        yt = band_bot(i, x)
        yb = y2 + rp * K * math.sin(math.radians(psi))
        hw = 3.6 if front else 2.8
        wl, wr = (W_FINE, W_MED) if front else (W_HAIR, W_FINE)
        art.line([(x - hw, yt), (x - hw, yb)], wl)
        art.line([(x + hw, yt), (x + hw, yb)], wr)
        if front:
            art.line([(x + hw * 0.35, yt + 1), (x + hw * 0.35, yb - 1)], W_HAIR)
            for yy in (7.0, 8.8, 10.8, 13.2):
                art.line([(x - hw + 0.6, yt + yy), (x + hw - 0.6, yt + yy)], W_HAIR)
            for yn in (yt + 3.0, yb - 3.0):        # hex nuts at both ends
                art.line([(x - hw - 2.2, yn - 2.6), (x + hw + 2.2, yn - 2.6), (x + hw + 2.2, yn + 2.6),
                          (x - hw - 2.2, yn + 2.6), (x - hw - 2.2, yn - 2.6)], W_HAIR)
                art.line([(x + 1.2, yn - 2.6), (x + 1.2, yn + 2.6)], W_HAIR)
        occs.append(occ_rect(x - hw - 2.5, yt, x + hw + 2.5, yb + 1.5))
    # coax bundles left and right of the axis
    kinds = {0: "dogleg", 1: "straight", 2: "bow", 3: "straight", 4: "s"}
    kind = kinds[i]
    offs = (-7.5, -2.5, 2.5, 7.5)
    for side in (-1, 1):
        xb = CX + side * 0.42 * a2
        x_top = CX + side * (0.40 if kind == "s" else 0.33) * PL[i][1] if kind in ("s", "dogleg") else xb
        y0 = band_bot(i, x_top) + 0.5
        y1 = y2 + 0.45 * a2 * K
        cl = cable_path(x_top, y0, xb, y1, kind, side)
        cables = bundle_lines(cl, offs)
        att_occs = []
        if kind == "straight" and i == 1:          # attenuators near the top, staggered
            for k, c in enumerate(cables):
                cx_ = c[0][0]
                ya = y0 + 6 + (k % 2) * 13
                art.line([(cx_ - 2.4, ya), (cx_ + 2.4, ya), (cx_ + 2.4, ya + 11), (cx_ - 2.4, ya + 11), (cx_ - 2.4, ya)], W_FINE)
                art.line([(cx_ + 1.0, ya + 1.5), (cx_ + 1.0, ya + 9.5)], W_HAIR)
                att_occs.append(occ_rect(cx_ - 2.6, ya - 0.6, cx_ + 2.6, ya + 11.6))
        for c in cables:
            art.lines_from(clip(c, att_occs), W_FINE)
        occs += att_occs
        for c in cables:                           # connectors where the coax lands
            ex, ey = c[-1]
            art.line([(ex, ey - 4.0), (ex, ey)], W_BOLD)
        for c in cables:
            occs += occ_polyline(c[::4] + [c[-1]], 2.0)
    # the central column
    if i in (0, 1):
        hw = 16.0 if i == 0 else 14.0
        occs += cylinder(art, CX, hw, lambda x, i=i: band_bot(i, x), y2, shadow=10.0)
        art.line(ell_pts(CX, y2, hw + 4, (hw + 4) * K, 180, 360, 6), W_FINE)
        art.line(ell_pts(CX, y2, hw + 4, (hw + 4) * K, 0, 180, 6), W_MED)
        occs.append(occ_ell(CX, y2, hw + 4.5, (hw + 4.5) * K + 1))
        if i == 1:                                  # a clamped flange half way down
            ym = (band_bot(1, CX) + y2) / 2 - 6
            occs += cylinder(art, CX, hw + 6, ym, ym + 8, cap=True, pmin=2.4)
    elif i == 2:
        pot_hw, pot_h = 34.0, 26.0
        top = y2 - pot_h
        occs += cylinder(art, CX, pot_hw, top, y2, cap=True, w_bot=W_BOLD, pmin=2.6)
        occs += cylinder(art, CX, 12.0, lambda x: band_bot(2, x), top, shadow=8.0)
        art.line(ell_pts(CX, top + 9, pot_hw, pot_hw * K, 0, 180, 6), W_HAIR)      # seam
    elif i == 3:
        tube = 5.0
        ys, ye = band_bot(3, CX) + 4.0, y2 - 5.0
        turns, rc = 4.5, 25.0
        front, back, cur, cur_f = [], [], [], None
        n = int(turns * 90)
        for k in range(n + 1):
            ph = 2 * math.pi * turns * k / n
            x = CX + rc * math.cos(ph)
            y = ys + (ye - ys) * k / n + rc * K * 2.2 * math.sin(ph)
            f = math.sin(ph) > 0
            if cur_f is None or f == cur_f:
                cur.append((x, y))
            else:
                (front if cur_f else back).append(cur + [(x, y)])
                cur = [(x, y)]
            cur_f = f
        (front if cur_f else back).append(cur)
        front_occ = []
        for f_ in front:
            front_occ += occ_polyline(f_[::3] + [f_[-1]], 2.2)
        tube_occ = [occ_rect(CX - tube - 1.2, ys - 20, CX + tube + 1.2, ye + 20)]
        for bk in back:
            art.lines_from(clip(bk, tube_occ), W_HAIR + 0.15)
        cylinder(art, CX, tube, lambda x: band_bot(3, x), y2, shade=False, clip_occs=front_occ)
        for f_ in front:
            art.line(f_, W_MED)
        occs.append(occ_rect(CX - rc - 2, ys - 6, CX + rc + 2, ye + 6))
    elif i == 4:
        pot_hw, pot_h = 30.0, 24.0
        top = y2 - pot_h
        occs += cylinder(art, CX, pot_hw, top, y2, cap=True, w_bot=W_BOLD, pmin=2.5)
        occs += cylinder(art, CX, 5.0, lambda x: band_bot(4, x), top, shade=False)
        for yy in (top + 8, top + 16):
            art.line(ell_pts(CX, yy, pot_hw, pot_hw * K, 0, 180, 6), W_HAIR)
    draw_interior(art, i, occs)
    return occs


def draw_interior(art, i, occs):
    """Shadowed interior of the stage between plate i and plate i+1: horizontal ruling at half
    the sky's pitch (so it stays on the pixel grid) crossed by one diagonal, knocked out around
    every post, cable and pot with a thin paper halo."""
    a2 = PL[i + 1][1]
    wg = 0.808 * a2 + 2.8
    halo = inflate_occs(occs, 1.7)

    def inside(x, y):
        return abs(x - CX) <= wg and band_bot(i, x) + 1.4 <= y <= face_back(i + 1, x) - 1.2

    y_lo = band_bot(i, CX - wg) - 1
    y_hi = PL[i + 1][0] + 1
    pitch = 2.0 / 1.024
    n = math.ceil((y_lo * 1.024 - 0.5) / 2.0)
    y = (0.5 + 2.0 * n) / 1.024
    while y < y_hi:
        for seg in clip_pred((CX - wg - 1, y), (CX + wg + 1, y), inside, 0.6):
            art.lines_from(clip(seg, halo), 0.85)
        y += pitch
    t = math.tan(math.radians(42))
    c = y_lo - t * (CX + wg) - 10
    while c < y_hi - t * (CX - wg) + 10:
        p = (CX - wg - 2, t * (CX - wg - 2) + c)
        q = (CX + wg + 2, t * (CX + wg + 2) + c)
        for seg in clip_pred(p, q, inside, 0.6):
            art.lines_from(clip(seg, halo), 0.8)
        c += 3.1 / math.cos(math.radians(42))


def draw_top(art):
    """Above the top flange: the pumping line rising to the seal and two suspension rods."""
    y0, a0, t0 = PL[0]
    occ = []
    # suspension rods to the inner rule
    for side in (-1, 1):
        x = CX + side * 132.0
        y_top = CY - math.sqrt(R_INNER ** 2 - (x - CX) ** 2) + 1.0
        y_bot = y0 - 0.55 * a0 * K
        art.line([(x - 3.0, y_top), (x - 3.0, y_bot)], W_FINE)
        art.line([(x + 3.0, y_top), (x + 3.0, y_bot)], W_MED)
        for yy in range(int(y_top + 6), int(y_bot - 4), 4):      # thread
            art.line([(x - 3.0, yy), (x + 3.0, yy + 1.4)], W_HAIR)
        for yn in (y_bot - 3.0, y_top + 3.5):
            art.line([(x - 5.6, yn - 2.6), (x + 5.6, yn - 2.6), (x + 5.6, yn + 2.6), (x - 5.6, yn + 2.6),
                      (x - 5.6, yn - 2.6)], W_FINE)
            art.line([(x + 1.6, yn - 2.6), (x + 1.6, yn + 2.6)], W_HAIR)
        occ.append(occ_rect(x - 6.0, y_top - 2, x + 6.0, y_bot + 3))
    # pumping line: tube, KF flange, neck to the rule
    occ += cylinder(art, CX, 18.0, 172.0, y0, cap=False)
    occ += cylinder(art, CX, 27.0, 163.0, 172.0, cap=True, pmin=2.3)
    neck_top = CY - R_INNER + 1.0
    cylinder(art, CX, 10.0, lambda x: neck_top, 163.0, shade=True)
    occ.append(occ_rect(CX - 10, neck_top, CX + 10, 163))
    # feedthroughs on the flange face, back half (SMA bulkheads)
    for psi in range(196, 345, 12):
        if 250 < psi < 290:
            continue
        x = CX + 0.78 * a0 * math.cos(math.radians(psi))
        yy = y0 + 0.78 * a0 * K * math.sin(math.radians(psi))
        art.line([(x - 2.0, yy), (x - 2.0, yy - 7.0)], W_HAIR)
        art.line([(x + 2.0, yy), (x + 2.0, yy - 7.0)], W_FINE)
        art.line(ell_pts(x, yy - 7.0, 2.0, 0.8, 0, 360, 30), W_HAIR)
        occ.append(occ_rect(x - 2.6, yy - 9.0, x + 2.6, yy + 0.6))
    return occ


CASTERS = {0: [(CX, 22.0)], 1: [(CX, 20.0)], 2: [(CX, 18.0)], 3: [(CX, 34.0)], 4: [], 5: [(CX, 30.0)]}


def draw_chandelier(art):
    face_occs = {0: draw_top(art)}
    for i in range(5):
        face_occs[i + 1] = draw_gap(art, i)
    for i in range(6):
        draw_plate(art, i, face_occs[i], CASTERS[i])


def chandelier_tiers(m):
    """Knock-out for the field ruling that follows the tiers: each plate, and between plates
    only as wide as the posts and cables, so the ruled sky shows under every overhang."""
    occ = []
    for i, (y, a, t) in enumerate(PL):
        b = a * K
        occ.append(occ_ell(CX, y, a + m, b + m))
        occ.append(occ_rect(CX - a - m, y, CX + a + m, y + t))
        occ.append(occ_ell(CX, y + t, a + m, b + m))
        if i < 5:
            a2 = PL[i + 1][1]
            hw = 0.808 * a2 + 3.0 + m
            occ.append(occ_rect(CX - hw, y + t, CX + hw, PL[i + 1][0]))
    return occ


# ----------------------------------------------------------------------------------------
# Chip, trail, plumb line, brackets, index
# ----------------------------------------------------------------------------------------
def cross_poly(cx, cy, L, w):
    return [(cx - w, cy - L), (cx + w, cy - L), (cx + w, cy - w), (cx + L, cy - w), (cx + L, cy + w), (cx + w, cy + w),
            (cx + w, cy + L), (cx - w, cy + L), (cx - w, cy + w), (cx - L, cy + w), (cx - L, cy - w), (cx - w, cy - w)]


def draw_chip(art, theta):
    c = chip_centre(theta)
    R = lambda p: rot((c[0] + p[0], c[1] + p[1]), c, -theta)  # noqa: E731
    sq = lambda h: [R(p) for p in ((-h, -h), (h, -h), (h, h), (-h, h))]  # noqa: E731
    # holder: heavy outline, inner pocket, screws
    hold = sq(HOLD)
    art.line(hold + [hold[0]], W_BOLD)
    pk = sq(HOLD - 7.0)
    art.line(pk + [pk[0]], W_HAIR)
    for sx in (-1, 1):
        for sy in (-1, 1):
            sc = R((sx * (HOLD - 3.6), sy * (HOLD - 3.6)))
            art.line(ell_pts(sc[0], sc[1], 2.2, 2.2, 0, 360, 20), W_HAIR)
            a = R((sx * (HOLD - 3.6) - 1.5, sy * (HOLD - 3.6) + 1.5))
            b = R((sx * (HOLD - 3.6) + 1.5, sy * (HOLD - 3.6) - 1.5))
            art.line([a, b], W_HAIR)
    # engraved tone on the holder frame: hatching in the band between pocket and edge,
    # heavier on the right and bottom (away from the light)
    for k in range(-int(HOLD) + 2, int(HOLD) - 1, 3):
        for (pa, pb, w) in (((HOLD - 6.2, k), (HOLD - 0.9, k), W_HAIR + 0.25),     # right edge band
                             ((k, HOLD - 6.2), (k, HOLD - 0.9), W_HAIR + 0.25)):   # bottom edge band
            art.line([R(pa), R(pb)], w)
    # bond wires from die to pocket
    for side in range(4):
        for k in (-10.5, -3.5, 3.5, 10.5):
            if side == 0:
                p, q = (DIE + 0.6, k), (HOLD - 7.6, k * 1.25)
            elif side == 1:
                p, q = (-DIE - 0.6, k), (-HOLD + 7.6, k * 1.25)
            elif side == 2:
                p, q = (k, DIE + 0.6), (k * 1.25, HOLD - 7.6)
            else:
                p, q = (k, -DIE - 0.6), (k * 1.25, -HOLD + 7.6)
            art.line([R(p), R(q)], W_HAIR)
    # the die: solid ink, qubits and pads knocked out
    contours = [poly_contour(orient(sq(DIE), True))]
    holes = []
    for qx in (-8.0, 8.0):
        for qy in (-8.0, 8.0):
            holes.append(cross_poly(qx, qy, 4.8, 1.15))
    holes.append([(-14.0, -0.7), (14.0, -0.7), (14.0, 0.7), (-14.0, 0.7)])     # feedline
    for k in (-10.0, -3.4, 3.4, 10.0):                                           # pads
        holes.append([(k - 1.3, -DIE + 1.4), (k + 1.3, -DIE + 1.4), (k + 1.3, -DIE + 3.2), (k - 1.3, -DIE + 3.2)])
        holes.append([(k - 1.3, DIE - 3.2), (k + 1.3, DIE - 3.2), (k + 1.3, DIE - 1.4), (k - 1.3, DIE - 1.4)])
    for h in holes:
        contours.append(poly_contour(orient([R(p) for p in h], False)))
    art.group(contours)
    # clamp on top of the holder, where the rod meets it
    cl = [R(p) for p in ((-6, -HOLD - 6), (6, -HOLD - 6), (6, -HOLD), (-6, -HOLD))]
    art.line(cl + [cl[0]], W_MED)
    return [Occ("p", inflate_convex(orient(hold, True), 3.0)), Occ("p", inflate_convex(orient(cl, True), 2.5))]


def draw_trail(art, now_occ):
    for th, kind in TRAIL:
        if kind == "now":
            continue
        corners = holder_corners(th)
        ring = corners + [corners[0]]
        dense = []
        for p, q in zip(ring, ring[1:]):
            dense += [(p[0] + (q[0] - p[0]) * k / 20, p[1] + (q[1] - p[1]) * k / 20) for k in range(20)]
        dense.append(ring[-1])
        c = chip_centre(th)
        rod_end = rot((c[0], c[1] - HOLD), c, -th)
        rod = [PIVOT, rod_end]
        if kind == "snapshot":
            for seg in clip(dense, now_occ):
                art.lines_from(dashed(seg, 5.0, 3.6), W_FINE)
            # the aim point: a small ring and cross where the snapshot says the chip is
            art.lines_from(clip(ell_pts(c[0], c[1], 5.0, 5.0, 0, 360, 10), now_occ), W_FINE)
            art.lines_from(clip([(c[0] - 11, c[1]), (c[0] + 11, c[1])], now_occ), W_FINE)
        else:
            for seg in clip(dense, now_occ):
                art.lines_from(dotted(seg, 3.8), W_FINE + 0.6)
            for seg in clip(rod, now_occ):
                art.lines_from(dotted(seg, 3.8), W_FINE + 0.2)
    # every recorded position leaves a tick on a small arc scale under the swing
    r_tr = ROD_L + HOLD + 21.0
    ths = [t for t, _ in TRAIL]
    art.lines_from(clip(arc_pts(r_tr, 90 - min(ths) + 3.5, 90 - max(ths) - 3.5, c=PIVOT, step=0.5), now_occ), W_HAIR)
    for th, kind in TRAIL:
        d = 90 - th
        L, w = {"now": (6.5, W_MED), "snapshot": (6.5, W_FINE), "dots": (4.2, W_FINE)}[kind]
        art.lines_from(clip([polar(r_tr - L, d, PIVOT), polar(r_tr + L, d, PIVOT)], now_occ), w)


def draw_pendulum(art):
    # clamp under the mixing chamber plate and the pivot pin
    y_b = band_bot(5, CX)
    cylinder(art, CX, 9.0, lambda x: band_bot(5, x), PIVOT[1] - 3.0, pmin=2.4, shadow=4.0)
    art.line(ell_pts(PIVOT[0], PIVOT[1], 3.6, 3.6, 0, 360, 15), W_MED)
    now = [t for t, k in TRAIL if k == "now"][0]
    now_occ = draw_chip(art, now)
    c = chip_centre(now)
    top = rot((c[0], c[1] - HOLD - 6.0), c, -now)
    art.line([(PIVOT[0] + 4.0 * math.sin(math.radians(now)), PIVOT[1] + 4.0 * math.cos(math.radians(now))), top], W_BOLD)
    draw_trail(art, now_occ)
    # plumb line from the pivot down to the dial's index: the snapshot's aim
    yt = PIVOT[1] + 5.0
    yb = CY + 333.0
    for seg in clip([(CX, yt), (CX, yb)], now_occ):
        art.lines_from(dashed(seg, 5.0, 3.6), W_FINE)
    return now_occ, y_b


def draw_brackets(art):
    g = bracket_geometry()
    xl, xr, yt, yb, bar, sf = g["xl"], g["xr"], g["yt"], g["yb"], g["bar"], g["serif"]

    def shape(x0, s):
        # s = +1 for "[" (serifs to the right), -1 for "]"
        X = lambda d: x0 + s * d  # noqa: E731
        return [(X(0), yt), (X(sf), yt), (X(sf), yt + bar), (X(bar), yt + bar),
                (X(bar), yb - bar), (X(sf), yb - bar), (X(sf), yb), (X(0), yb)]

    def inset(pts, d):
        # inward offset of an orthogonal polygon = outward offset with negative margin
        return inflate_convex_ortho(pts, -d)

    for x0, s in ((xl, 1), (xr, -1)):
        outer = orient(shape(x0, s), True)
        i1 = orient(inset(outer, 3.4), False)
        i2 = orient(inset(outer, 4.7), True)
        art.group([poly_contour(outer), poly_contour(i1), poly_contour(i2)], role="accent")
    return g


def inflate_convex_ortho(pts, m):
    """Offset an orthogonal (axis-aligned, possibly concave) polygon by m (negative = inward)."""
    pts = orient(pts, True)
    n = len(pts)
    out = []
    for k in range(n):
        p0, p1, p2 = pts[k - 1], pts[k], pts[(k + 1) % n]
        e1 = (p1[0] - p0[0], p1[1] - p0[1])
        e2 = (p2[0] - p1[0], p2[1] - p1[1])
        n1 = (e1[1] / math.hypot(*e1), -e1[0] / math.hypot(*e1))
        n2 = (e2[1] / math.hypot(*e2), -e2[0] / math.hypot(*e2))
        out.append((p1[0] + (n1[0] + n2[0]) * m, p1[1] + (n1[1] + n2[1]) * m))
    return out


def draw_index(art):
    apex = polar(R_INNER - 3.0, 90)
    base_l = (CX - 10.5, CY + 334.0)
    base_r = (CX + 10.5, CY + 334.0)
    tri = orient([base_l, base_r, apex], True)
    art.group([poly_contour(tri)])
    return occ_poly(tri, 4.5)


# ----------------------------------------------------------------------------------------
# Rim: rings, guilloche rope, dial, interval on the dial, ornaments, lettering
# ----------------------------------------------------------------------------------------
def draw_rim(art, g, glyph_groups, orn_angles):
    art.line(arc_pts(R_RING, 0, 360, step=0.5), W_HEAVY)
    for ph in (0.0, math.pi):
        pts = []
        for k in range(0, 2881):
            a = 2 * math.pi * k / 2880
            r = R_GUIL + 6.0 * math.sin(96 * a + ph)
            pts.append((CX + r * math.cos(a), CY + r * math.sin(a)))
        art.line(pts, W_HAIR)
    art.line(arc_pts(R_TXT_OUT, 0, 360), W_FINE)
    art.line(arc_pts(R_TXT_IN, 0, 360), W_FINE)
    art.line(arc_pts(R_BOLD, 0, 360), W_BOLD)
    art.line(arc_pts(R_INNER, 0, 360), W_FINE)
    # graduated ring
    for k in range(180):
        d = k * 2.0
        if k % 15 == 0:
            L, w = 26.0, W_BOLD
        elif k % 5 == 0:
            L, w = 17.0, W_MED - 0.4
        else:
            L, w = 9.5, W_FINE - 0.1
        art.line([polar(R_TICK0, d), polar(R_TICK0 - L, d)], w)
    # the interval on the dial: between the brackets' outer bottom corners, seen from the centre
    a_r = math.degrees(math.atan2(g["yb"] - CY, g["xr"] - CX))
    a_l = math.degrees(math.atan2(g["yb"] - CY, g["xl"] - CX))
    band = arc_pts(R_TXT_IN + 1.2, a_r, a_l, step=0.25) + arc_pts(R_BOLD - 1.6, a_l, a_r, step=0.25)
    art.group([poly_contour(orient(band, True))], role="accent")
    for ang, into in ((a_l, -1), (a_r, 1)):
        # bracket ends: a radial spine and a serif pointing into the interval along the arc
        r0, r1, w = R_INNER - 2.0, R_TXT_IN + 1.2, 4.6
        dw = math.degrees(w / R_BOLD)
        spine = arc_pts(r1, ang - dw / 2, ang + dw / 2, step=0.2) + arc_pts(r0, ang + dw / 2, ang - dw / 2, step=0.2)
        ser_len = 5.5
        serif = arc_pts(r0 + 4.6, ang - into * dw / 2, ang + into * ser_len, step=0.2) + arc_pts(r0, ang + into * ser_len, ang - into * dw / 2, step=0.2)
        art.group([poly_contour(orient(spine, True))], role="accent")
        art.group([poly_contour(orient(serif, True))], role="accent")
    # ornaments: stars of tick marks between the words
    rm = (R_TXT_IN + R_TXT_OUT) / 2
    for ang in orn_angles:
        c = polar(rm, ang)
        for k in range(16):
            L = 16.0 if k % 4 == 0 else (10.0 if k % 2 == 0 else 6.5)
            d = ang + k * 22.5
            w = W_MED if k % 4 == 0 else (W_FINE if k % 2 == 0 else W_HAIR + 0.2)
            art.line([polar(4.6, d, c), polar(4.6 + L, d, c)], w)
        art.group([poly_contour(orient(ell_pts(c[0], c[1], 2.7, 2.7, 0, 360, 15), True))])
        for s in (-1, 1):
            for k, r_ in ((1, 2.6), (2, 1.9), (3, 1.3)):
                q = polar(rm, ang + s * (2.6 + 2.2 * k))
                art.group([poly_contour(orient(ell_pts(q[0], q[1], r_, r_, 0, 360, 20), True))])
    for grp in glyph_groups:
        art.group(grp)


# ----------------------------------------------------------------------------------------
# Lettering: outline the words in VectorCraft, then set each glyph on the arc
# ----------------------------------------------------------------------------------------
TOK = re.compile(r"[MLCZmlcz]|[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def parse_path(d):
    toks = TOK.findall(d)
    contours, cur, i, cmd = [], None, 0, None
    while i < len(toks):
        t = toks[i]
        if t in "MLCZmlcz":
            cmd = t.upper()
            if t not in "MLCZ":
                raise ValueError("relative path command in glyph data")
            i += 1
            if cmd == "Z":
                if cur:
                    contours.append(cur)
                cur = None
            continue
        if cmd == "M":
            if cur:
                contours.append(cur)
            cur = [("M", [(float(toks[i]), float(toks[i + 1]))])]
            i += 2
            cmd = "L"
        elif cmd == "L":
            cur.append(("L", [(float(toks[i]), float(toks[i + 1]))]))
            i += 2
        elif cmd == "C":
            ps = [(float(toks[i + 2 * k]), float(toks[i + 2 * k + 1])) for k in range(3)]
            cur.append(("C", ps))
            i += 6
    if cur:
        contours.append(cur)
    return contours


def outline_word(vc, text, size, style):
    """Outline `text` in a scratch document and return its glyph contours.

    The SVG comes back in memory (export without `path` returns dataBase64, the same bytes a
    file export writes), so this writes no file and works under any VectorCraft root the
    caller chose. Side effect: opens and closes the scratch document; VectorCraft then makes
    the caller's document active again (checked 2026-10-16)."""
    vc.cmd("file.new", width=3000, height=600, units="Pixels", name="glyphs")
    t = vc.tool("add_text", x=100, y=300, text=text, font=FONT, size=size, color="#000000")["id"]
    vc.cmd("text.setStyle", id=t, style=style)
    vc.cmd("select.set", ids=[t])
    vc.cmd("type.createOutlines")
    res = vc.tool("export", format="svg", outlineText=True)
    vc.cmd("file.close")
    svg = base64.b64decode(res["dataBase64"]).decode("utf-8")
    glyphs = [parse_path(d) for d in re.findall(r'<path d="([^"]+)"', svg)]
    return glyphs


def glyph_bbox(g):
    xs = [p[0] for c in g for _, ps in c for p in ps]
    ys = [p[1] for c in g for _, ps in c for p in ps]
    return min(xs), min(ys), max(xs), max(ys)


def set_on_arc(glyphs, text, extra, r_base, centre_deg, bottom):
    """Rigidly rotate each glyph onto the baseline circle. extra = added space per character."""
    idx = [j for j, ch in enumerate(text) if ch != " "]
    assert len(idx) == len(glyphs), (text, len(glyphs))
    cxs = []
    for g, j in zip(glyphs, idx):
        x0, _, x1, _ = glyph_bbox(g)
        cxs.append((x0 + x1) / 2 + extra * j)
    lo = min(glyph_bbox(g)[0] + extra * j for g, j in zip(glyphs, idx))
    hi = max(glyph_bbox(g)[2] + extra * j for g, j in zip(glyphs, idx))
    mid = (lo + hi) / 2
    groups, span = [], math.degrees((hi - lo) / r_base)
    for g, j, gc in zip(glyphs, idx, cxs):
        x0, _, x1, _ = glyph_bbox(g)
        own = (x0 + x1) / 2
        s = gc - mid
        if not bottom:
            al = math.radians(centre_deg + math.degrees(s / r_base))
            u = (math.cos(al), math.sin(al))
            tv = (-math.sin(al), math.cos(al))
            f = lambda p: (CX + (r_base - (p[1] - 300)) * u[0] + (p[0] - own) * tv[0],  # noqa: E731
                           CY + (r_base - (p[1] - 300)) * u[1] + (p[0] - own) * tv[1])
        else:
            al = math.radians(centre_deg - math.degrees(s / r_base))
            u = (math.cos(al), math.sin(al))
            tv = (math.sin(al), -math.cos(al))
            f = lambda p: (CX + (r_base + (p[1] - 300)) * u[0] + (p[0] - own) * tv[0],  # noqa: E731
                           CY + (r_base + (p[1] - 300)) * u[1] + (p[0] - own) * tv[1])
        groups.append([[(op, [f(p) for p in ps]) for op, ps in c] for c in g])
    return groups, span


def lettering(vc):
    size, style = 57.0, "Bold"
    top = outline_word(vc, "SUPERCONDUCTED", size, style)
    bot = outline_word(vc, "NOISE ENGINE", size, style)
    r_top, r_bot = R_TXT_IN + 13.0, R_TXT_OUT - 11.0
    # tracking: solve so the top word spans TOP_SPAN degrees
    TOP_SPAN = 146.0
    g0, s0 = set_on_arc(top, "SUPERCONDUCTED", 0.0, r_top, -90, False)
    w0 = math.radians(s0) * r_top
    extra = (math.radians(TOP_SPAN) * r_top - w0) / (len("SUPERCONDUCTED") - 1)
    gt, st = set_on_arc(top, "SUPERCONDUCTED", extra, r_top, -90, False)
    gb, sb = set_on_arc(bot, "NOISE ENGINE", extra, r_bot, 90, True)
    # ornaments half way between the words on each side
    right = ((-90 + st / 2) + (90 - sb / 2)) / 2
    left = 180 - right
    return gt + gb, (right, left), dict(size=size, extra=extra, top_span=st, bottom_span=sb)


# ----------------------------------------------------------------------------------------
# The field ruling (the engraved "sky" of the vignette) with knock-outs
# ----------------------------------------------------------------------------------------
def draw_field(art, knock):
    pitch = 4.0 / 1.024
    region = occ_ell(CX, CY, R_FIELD, R_FIELD)
    # One unbroken stroke per line, uniform weight. (A radial vignette made by cutting the lines
    # into width steps left rings of overlapping round caps that showed at 512 px.)
    y = 0.5 / 1.024
    while y < CY - R_FIELD:
        y += pitch
    while y < CY + R_FIELD:
        dy = y - CY
        half = math.sqrt(max(0.0, R_FIELD ** 2 - dy * dy))
        for seg in clip([(CX - half - 1, y), (CX + half + 1, y)], knock, inside=region):
            art.line([seg[0], seg[-1]], 0.95)
        y += pitch


# ----------------------------------------------------------------------------------------
# Assemble the hero
# ----------------------------------------------------------------------------------------
_HERO_CACHE = {}


def hero_art(vc):
    """The hero's geometry and its lettering stats, as (Art, info), built once per process.

    The geometry is pure Python except the lettering, which VectorCraft outlines in a scratch
    document (see outline_word); the cache keeps that to one round trip however many times
    draw_mark is called. Calling this before opening a document keeps the scratch document
    out of the caller's way entirely; draw_mark calls it lazily otherwise."""
    if "hero" not in _HERO_CACHE:
        _HERO_CACHE["hero"] = _build_hero_art(vc)
    return _HERO_CACHE["hero"]


def _build_hero_art(vc):
    art = Art()
    glyphs, orn, info = lettering(vc)
    draw_chandelier(art)
    now_occ, _ = draw_pendulum(art)
    g = draw_brackets(art)
    idx_occ = draw_index(art)
    draw_rim(art, g, glyphs, orn)
    # knock-outs for the ruled field
    knock = chandelier_tiers(7.0)
    knock.append(occ_rect(CX - 132 - 9, CY - R_INNER - 5, CX - 132 + 9, PL[0][0]))
    knock.append(occ_rect(CX + 132 - 9, CY - R_INNER - 5, CX + 132 + 9, PL[0][0]))
    knock.append(occ_rect(CX - 33, CY - R_INNER - 5, CX + 33, PL[0][0]))
    knock.append(occ_rect(g["xl"] - 6, g["yt"] - 6, g["xr"] + 6, g["yb"] + 6))
    knock.append(occ_poly([(CX - 16, band_bot(5, CX) - 4), (CX + 16, band_bot(5, CX) - 4),
                           (g["xr"] - g["serif"] + 6, g["yt"]), (g["xl"] + g["serif"] - 6, g["yt"])], 5.0))
    knock.append(occ_rect(CX - 5, g["yb"], CX + 5, CY + 340))
    knock.append(idx_occ)
    draw_field(art, knock)
    return art, info


# ----------------------------------------------------------------------------------------
# The small companion mark (favicon), drawn on a 32 x 32 grid
# ----------------------------------------------------------------------------------------
SM = dict(c=16.0, r_out=15.5, r_in=13.0,            # seal ring (2.5 wide)
          bar=2.5, bx_l=6.0, by_t=10.0, by_b=22.0, serif=5.5,  # brackets
          chip=(16.0, 13.0, 22.0, 19.0),           # holder, swung 3 units right of the axis
          rod=((16.0, 2.6), (19.0, 13.0), 1.7),    # hanger from the ring
          idx=(16.0, 23.6, 2.4, 27.8))             # index: apex x, apex y, half base, base y


def disc(cx, cy, r, positive=True, step=2.0):
    return orient(ell_pts(cx, cy, r, r, 0, 360 - step, step), positive)


def small_art(variant="A"):
    art = Art()
    c = SM["c"]
    art.group([poly_contour(disc(c, c, SM["r_out"], True, 1.0)), poly_contour(disc(c, c, SM["r_in"], False, 1.0))])
    b, x0, yt, yb, sf = SM["bar"], SM["bx_l"], SM["by_t"], SM["by_b"], SM["serif"]
    for xl, s_ in ((x0, 1), (SMALL_UNITS - x0, -1)):
        X = lambda d: xl + s_ * d  # noqa: E731
        br = [(X(0), yt), (X(sf), yt), (X(sf), yt + b * 0.85), (X(b), yt + b * 0.85), (X(b), yb - b * 0.85),
              (X(sf), yb - b * 0.85), (X(sf), yb), (X(0), yb)]
        art.group([poly_contour(orient(br, True))], role="accent")
    (px, py), (qx, qy), w = SM["rod"]
    dx, dy = qx - px, qy - py
    L = math.hypot(dx, dy)
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    art.group([poly_contour(orient([(px + nx, py + ny), (qx + nx, qy + ny), (qx - nx, qy - ny), (px - nx, py - ny)], True))])
    x_a, y_a, x_b, y_b = SM["chip"]
    if variant == "A":
        art.group([poly_contour(orient([(x_a, y_a), (x_b, y_a), (x_b, y_b), (x_a, y_b)], True)),
                   poly_contour(orient([(x_a + 2, y_a + 2), (x_b - 2, y_a + 2), (x_b - 2, y_b - 2), (x_a + 2, y_b - 2)], False))])
    else:
        f = 1.6
        art.group([poly_contour(orient([(x_a, y_a), (x_b, y_a), (x_b, y_b), (x_a, y_b)], True)),
                   poly_contour(orient([(x_a + f, y_a + f), (x_b - f, y_a + f), (x_b - f, y_b - f), (x_a + f, y_b - f)], False))])
        d = 1.5
        art.group([poly_contour(orient([(x_a + f + d, y_a + f + d), (x_b - f - d, y_a + f + d),
                                        (x_b - f - d, y_b - f - d), (x_a + f + d, y_b - f - d)], True))])
    ax, ay, hb, by = SM["idx"]
    art.group([poly_contour(orient([(ax - hb, by), (ax + hb, by), (ax, ay)], True))])
    return art


# ----------------------------------------------------------------------------------------
# Emission to VectorCraft
# ----------------------------------------------------------------------------------------
def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def emit(vc, art, ox, oy, s, fill_of, line_colour, roles=None):
    """Draw `art` into the active document at offset (ox, oy) and scale s; return the ids.

    fill_of maps a fill group's role ("ink" or "accent") to its colour; every line is
    line_colour. The order of the paths never depends on the colours: lines grouped by width
    (ascending, at most 1500 polylines per compound path, round caps and joins), then the fill
    groups in drawing order, so a palette changes paint only and the neutral palette reproduces
    the committed files byte for byte. roles, when given, draws only the fill groups with those
    roles, and the lines only when "ink" is among them."""
    T = lambda p: fmt(ox + s * p[0]) + " " + fmt(oy + s * p[1])  # noqa: E731
    ids = []
    by_w = {}
    for w, pts in art.lines:
        by_w.setdefault(w, []).append(pts)
    if roles is None or "ink" in roles:
        for w in sorted(by_w):
            polys = by_w[w]
            for k in range(0, len(polys), 1500):
                d = " ".join("M " + " L ".join(T(p) for p in pts) for pts in polys[k:k + 1500])
                ids.append(vc.tool("draw_path", d=d, fill="none", stroke=line_colour, strokeWidth=round(w * s, 4))["id"])
                vc.cmd("stroke.set", cap="round", join="round")
    for grp, role in zip(art.fills, art.roles):
        if roles is not None and role not in roles:
            continue
        parts = []
        for c in grp:
            for op, ps in c:
                parts.append(op + " " + " ".join(T(p) for p in ps))
            parts.append("Z")
        ids.append(vc.tool("draw_path", d=" ".join(parts), fill=fill_of[role], stroke="none")["id"])
    return ids


def paper_disc(vc, cx, cy, r, fill):
    return vc.tool("draw_path", d="M %.3f %.3f A %.3f %.3f 0 1 0 %.3f %.3f A %.3f %.3f 0 1 0 %.3f %.3f Z" % (
        cx + r, cy, r, r, cx - r, cy, r, r, cx + r, cy), fill=fill, stroke="none")["id"]


# ----------------------------------------------------------------------------------------
# The mark API (../MARK_API.md)
# ----------------------------------------------------------------------------------------
def box(variant="hero"):
    """The art's bounding box (x0, y0, x1, y1) inside the unit square that draw_mark scales.

    hero: the outer edge of the heavy seal ring (radius R_RING plus half of W_HEAVY); nothing
    in the seal reaches beyond it. small: the outer edge of the ring, which the paper disc
    shares. Both are centred, so x0 == y0 and x1 == y1."""
    if variant == "hero":
        lo = (CX - R_RING - W_HEAVY / 2) / HERO_UNITS
        hi = (CX + R_RING + W_HEAVY / 2) / HERO_UNITS
    elif variant == "small":
        lo = (SM["c"] - SM["r_out"]) / SMALL_UNITS
        hi = (SM["c"] + SM["r_out"]) / SMALL_UNITS
    else:
        raise ValueError(f"variant must be 'hero' or 'small', not {variant!r}")
    return (lo, lo, hi, hi)


def _hex(c):
    if not (isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c)):
        raise ValueError(f"colour must be '#rrggbb', not {c!r}")
    return tuple(int(c[k:k + 2], 16) for k in (1, 3, 5))


def palette(colours):
    """Resolve the API's colours: ink, paper and accent are required ('#rrggbb'); a missing
    tint is mixed per sRGB channel as t(a) = (1 - a) * paper + a * ink with a from TINT_MIX.
    This design never paints a tint; resolving them keeps the contract uniform."""
    missing = [k for k in ("ink", "paper", "accent") if k not in colours]
    if missing:
        raise KeyError(f"colours lacks {missing}")
    pal = {k: colours[k] for k in ROLES if k in colours}
    for k in pal:
        _hex(pal[k])
    ink, paper = _hex(pal["ink"]), _hex(pal["paper"])
    for k, a in TINT_MIX.items():
        if k not in pal:
            pal[k] = "#%02X%02X%02X" % tuple(round((1 - a) * p + a * i) for p, i in zip(paper, ink))
    return pal


def draw_mark(vc, x, y, size, colours, variant="hero", mono=False):
    """Draw the mark into VectorCraft's ACTIVE document, its unit square mapped to the square
    with top-left (x, y) and side `size` (points, y down). Returns the ids of what it drew.

    colours: {"ink", "paper", "accent"} as '#rrggbb' (tints optional and unused here).
    variant: "hero" (the seal, 128 px and up) or "small" (the favicon redraw, 16 to 32 px;
             the 16 px file is this drawing rendered at half size, there is no "small16").
    mono:    True paints everything, fills and strokes alike, in colours["ink"]: the accent
             groups turn ink and the small mark's paper disc is left out (its gaps are real
             knock-outs). The engraving stays stroked line work (MARK_API.md test 3 as
             amended 2026-10-16); the hero paints no paper in either mode, so for the hero
             mono=True equals mono=False with accent = ink.
    Side effects: adds paths to the active document and selects the last one; on the first
    hero call in a process (unless hero_art ran first) VectorCraft opens and closes a scratch
    document to outline the lettering, and the caller's document is active again afterwards.
    The hero draws no background; the small mark's only background is its paper disc."""
    return _draw(vc, x, y, size, colours, variant, mono)


def _draw(vc, x, y, size, colours, variant="hero", mono=False, roles=None):
    """draw_mark with a role filter: roles=("accent",) draws only the range (check_api.py
    uses it to build the accent mask)."""
    pal = palette(colours)
    ids = []
    if variant == "hero":
        art = hero_art(vc)[0]
        s = size / HERO_UNITS
    elif variant == "small":
        art = small_art()
        s = size / SMALL_UNITS
        if not mono and (roles is None or "paper" in roles):
            ids.append(paper_disc(vc, x + SM["c"] * s, y + SM["c"] * s, SM["r_out"] * s, pal["paper"]))
    else:
        raise ValueError(f"variant must be 'hero' or 'small', not {variant!r}")
    fill_of = {"ink": pal["ink"], "accent": pal["ink"] if mono else pal["accent"]}
    return ids + emit(vc, art, x, y, s, fill_of, pal["ink"], roles=roles)

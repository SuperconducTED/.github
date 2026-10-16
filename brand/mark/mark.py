"""SuperconducTED round 3, style: technical cutaway. The mark itself, behind the shared API.

Every number of the drawing lives in this file; `build.py` only lays the mark out into
documents and `brand/tools/build_brand.py` can call it in any palette (see ../MARK_API.md).

Story the mark tells (top to bottom, on one shared centre line):
  * the chandelier: a side elevation of a dilution refrigerator, plates in section (hatched),
    support rods, pulse-tube cold head, still pumping line, still pot, continuous (helical)
    and step heat exchangers, mixing chamber pot, coax bundle swaying between stages,
    output lines with an amplifier box and circulator block, and a cold finger;
  * the calibration dial: below the coldest plate the drawing turns into a magnifier ring,
    graduated like a dial; its index and the dash-dot crosshair sit on the fridge's own centre
    line, which is where the frozen calibration (the snapshot) says the chip is;
  * the drifting chip: the solid chip sits off that crosshair; its earlier positions are drawn
    as phantom lines (the drafting convention for alternate positions of a moving part);
  * the interval: bold [ ] brackets span every position, with a numeral-free dimension line
    under them; a second short dimension measures the drift from the crosshair.

API (the contract in ../MARK_API.md)
------------------------------------
* `box(variant)`: the art's bounding box (x0, y0, x1, y1) in the unit square, measured on the
  emitted geometry, strokes included at half their width on every side.
* `draw_mark(vc, x, y, size, colours, variant="hero", mono=False)`: draws into VectorCraft's
  active document and returns the ids of the paths it drew. Variants:
    - "hero": the detailed mark, 1000 design units to the unit square, 128 px and up;
    - "small": the favicon redraw on a 32-unit grid, every edge on a whole unit (crisp at 32 px);
    - "small16": the same small mark hinted on a 16-unit grid (crisp at 16 px). Use it, not
      "small", for a 16 px favicon: a 32-grid master halves to half-pixel edges.
* Colour roles: only `ink` and `accent` are painted. `accent` goes on the range and nothing
  else: the bold [ ] brackets and the numeral-free dimension that spans them (its two extension
  lines, its line and its two arrowheads; in the small marks, the brackets). Everything else is
  `ink`: the refrigerator, the dial, the index, the datum, the chip, the phantom chip, the drift
  path and the drift dimension. The design paints no paper-coloured shape and no tint, so
  `paper`, `tint-light` and `tint-shade` are accepted and ignored.
* `mono=True` paints every role in `colours["ink"]`. Knockouts are real geometry (clipped lines,
  opposite-winding holes), never paper patches. The line work stays stroked, in that one colour.
* Side effects: adds paths to the active document, nothing else (no background). Importing this
  module has no side effects.
* Invariant: with accent equal to ink the drawing is byte for byte the pre-API drawing, because
  adjacent parts of one item that resolve to the same colour are emitted as ONE path.
"""
import bisect
import functools
import math
import re

ROLES = ("ink", "paper", "accent", "tint-light", "tint-shade")
VARIANTS = ("hero", "small", "small16")
UNITS = {"hero": 1000.0, "small": 32.0, "small16": 16.0}   # design units per side of the unit square

# ---------------------------------------------------------------- line-weight hierarchy
# Design space for the hero is 1000 x 1000 units (1 unit = 1.024 px in the 1024 px hero).
W_HEAVY = 7.0   # plate outlines in section, sample-mount outlines
W_MED = 3.4     # rods, tubes, coax, cold-head, ticks every 15 degrees
W_FINE = 1.4    # hatching, centre lines, phantom lines, dimension lines, minor ticks
BAND = 10.0     # the solid outer band of the dial (a solid fill, heavier than any stroke)

HATCH = 6.0     # perpendicular spacing of 45 degree section hatching

# ---------------------------------------------------------------- geometry kernel


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def area(pts):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2.0


def orient(pts, positive=True):
    """Return pts wound so that area() is positive (outer) or negative (hole)."""
    pts = list(pts)
    if (area(pts) > 0) != positive:
        pts.reverse()
    return pts


def rect_pts(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def circle_pts(cx, cy, r, n=None):
    n = n or max(48, int(2 * math.pi * r / 2.5))
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def polar(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def bezier(p0, p1, p2, p3, n=24):
    out = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


# Obstacles / regions: ("circle", cx, cy, r) | ("rect", x0, y0, x1, y1) | ("poly", pts) convex


def interval_in(p, q, ob):
    """Parameter intervals [(t0, t1)] where segment p->q lies inside the region `ob`."""
    kind = ob[0]
    dx, dy = q[0] - p[0], q[1] - p[1]
    if kind == "circle":
        _, cx, cy, r = ob
        fx, fy = p[0] - cx, p[1] - cy
        a = dx * dx + dy * dy
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - r * r
        disc = b * b - 4 * a * c
        if a < 1e-12 or disc <= 0:
            return []
        sq = math.sqrt(disc)
        t0, t1 = max((-b - sq) / (2 * a), 0.0), min((-b + sq) / (2 * a), 1.0)
        return [(t0, t1)] if t0 < t1 else []
    if kind == "rect":
        _, x0, y0, x1, y1 = ob
        t0, t1 = 0.0, 1.0
        for pp, qq in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
            if abs(pp) < 1e-12:
                if qq < 0:
                    return []
            else:
                t = qq / pp
                if pp < 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        return [(t0, t1)] if t0 < t1 else []
    if kind == "poly":
        pts = ob[1]
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        t0, t1 = 0.0, 1.0
        for a, b in zip(pts, pts[1:] + pts[:1]):
            nx, ny = b[1] - a[1], a[0] - b[0]
            if nx * (cx - a[0]) + ny * (cy - a[1]) < 0:
                nx, ny = -nx, -ny          # inward normal
            num = nx * (p[0] - a[0]) + ny * (p[1] - a[1])
            den = nx * dx + ny * dy
            if abs(den) < 1e-12:
                if num < 0:
                    return []
            else:
                t = -num / den
                if den > 0:
                    t0 = max(t0, t)
                else:
                    t1 = min(t1, t)
        return [(t0, t1)] if t0 < t1 else []
    raise ValueError(kind)


def subtract(base, cuts):
    res = list(base)
    for c0, c1 in cuts:
        nxt = []
        for a, b in res:
            if c1 <= a or c0 >= b:
                nxt.append((a, b))
                continue
            if c0 > a:
                nxt.append((a, c0))
            if c1 < b:
                nxt.append((c1, b))
        res = nxt
    return [(a, b) for a, b in res if b - a > 1e-9]


def seg_pieces(p, q, region=None, obs=()):
    base = interval_in(p, q, region) if region else [(0.0, 1.0)]
    cuts = []
    for ob in obs:
        cuts += interval_in(p, q, ob)
    return subtract(base, sorted(cuts))


def clip_polyline(pl, region=None, obs=()):
    """Split polyline into the pieces inside `region` (if given) and outside every obstacle."""
    out, cur = [], []
    for a, b in zip(pl, pl[1:]):
        ivs = seg_pieces(a, b, region, obs)
        for t0, t1 in ivs:
            pa, pb = lerp(a, b, t0), lerp(a, b, t1)
            if cur and t0 < 1e-9:
                cur.append(pb)
            else:
                if len(cur) >= 2:
                    out.append(cur)
                cur = [pa, pb]
        if not ivs or ivs[-1][1] < 1 - 1e-9:
            if len(cur) >= 2:
                out.append(cur)
            cur = []
    if len(cur) >= 2:
        out.append(cur)
    return out


def _cum(pl):
    c = [0.0]
    for a, b in zip(pl, pl[1:]):
        c.append(c[-1] + dist(a, b))
    return c


def _at(pl, cum, s):
    k = min(max(bisect.bisect_right(cum, s) - 1, 0), len(pl) - 2)
    seg = cum[k + 1] - cum[k]
    return lerp(pl[k], pl[k + 1], 0 if seg < 1e-12 else (s - cum[k]) / seg), k


def sub_polyline(pl, cum, s0, s1):
    p0, k0 = _at(pl, cum, s0)
    p1, k1 = _at(pl, cum, s1)
    return [p0] + [pl[k] for k in range(k0 + 1, k1 + 1) if s0 < cum[k] < s1] + [p1]


def dash(pl, pattern, offset=0.0):
    """Dash a polyline with an on/off pattern starting `offset` units into the pattern."""
    cum = _cum(pl)
    L, P = cum[-1], sum(pattern)
    out, s, i = [], -(offset % P), 0
    while s < L:
        ln = pattern[i % len(pattern)]
        if i % 2 == 0:
            a, b = max(s, 0.0), min(s + ln, L)
            if b - a > 0.3:
                out.append(sub_polyline(pl, cum, a, b))
        s += ln
        i += 1
    return out


CENTRE = [26.0, 5.0, 6.0, 5.0]                 # long, gap, short, gap
PHANTOM = [15.0, 3.5, 2.5, 3.5, 2.5, 3.5]      # long, gap, short, gap, short, gap
HIDDEN = [6.0, 3.5]


def centre_line(a, b, m):
    """Dash-dot centre line from a to b whose short dash is centred on m (the crossing)."""
    off = CENTRE[0] + CENTRE[1] + CENTRE[2] / 2
    return dash([m, a], CENTRE, off) + dash([m, b], CENTRE, off)


def closed(pts):
    return list(pts) + [pts[0]]


def rejoin(pieces):
    """Clipping a closed outline restarts it at its first vertex; rejoin the two pieces that meet
    there so a butt-capped outline keeps a clean corner instead of a notch."""
    if len(pieces) > 1 and dist(pieces[0][0], pieces[-1][-1]) < 1e-6:
        pieces = [pieces[-1] + pieces[0][1:]] + pieces[1:-1]
    return pieces


def arrow(tip, toward, length=13.0, half=3.6):
    """Filled arrowhead with its tip at `tip`, pointing away from `toward`."""
    d = dist(tip, toward)
    ux, uy = (tip[0] - toward[0]) / d, (tip[1] - toward[1]) / d
    bx, by = tip[0] - ux * length, tip[1] - uy * length
    return orient([tip, (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)])


def hatch(region, sp=HATCH, slope=1, obs=(), bbox=None):
    """45 degree hatch lines inside a region, globally registered (same grid everywhere).

    slope=+1 draws '/' (lines x + y = c in y-down space), slope=-1 draws '\\' (x - y = c)."""
    if bbox is None:
        if region[0] == "rect":
            bbox = region[1:]
        elif region[0] == "circle":
            _, cx, cy, r = region
            bbox = (cx - r, cy - r, cx + r, cy + r)
        else:
            xs = [x for x, _ in region[1]]
            ys = [y for _, y in region[1]]
            bbox = (min(xs), min(ys), max(xs), max(ys))
    x0, y0, x1, y1 = bbox
    step = sp * math.sqrt(2)
    D = (x1 - x0) + (y1 - y0) + 10
    out = []
    if slope > 0:
        lo, hi = x0 + y0, x1 + y1
    else:
        lo, hi = x0 - y1, x1 - y0
    k = math.ceil(lo / step)
    while k * step <= hi:
        c = k * step
        if slope > 0:
            p, q = (c - (y0 - D), y0 - D), (c - (y1 + D), y1 + D)
        else:
            p, q = (c + (y0 - D), y0 - D), (c + (y1 + D), y1 + D)
        out += clip_polyline([p, q], region, obs)
        k += 1
    return out


# ---------------------------------------------------------------- art: geometry tagged with roles


class Art:
    """An ordered list of items, back to front. Each item is one drawing layer:

        ('S', parts, weight, closed, cap)   stroked polylines
        ('F', parts)                        filled polygons (nonzero winding)

    where parts = [(role, polylines), ...]. emit() resolves each role to a colour and merges
    ADJACENT parts of one item that land on the same colour into one path, so splitting an item
    by role changes nothing when the roles share a colour. Items are never merged with each other.
    """

    def __init__(self):
        self.items = []

    def stroke(self, pls, w, close=False, cap="round", role="ink"):
        self.stroke_parts([(role, pls)], w, close, cap)

    def stroke_parts(self, parts, w, close=False, cap="round"):
        parts = [(r, [pl for pl in pls if len(pl) >= 2]) for r, pls in parts]
        parts = [(r, pls) for r, pls in parts if pls]
        if parts:
            self.items.append(("S", parts, w, close, cap))

    def fill(self, polys, role="ink"):
        self.fill_parts([(role, polys)])

    def fill_parts(self, parts):
        parts = [(r, [p for p in polys if len(p) >= 3]) for r, polys in parts]
        parts = [(r, polys) for r, polys in parts if polys]
        if parts:
            self.items.append(("F", parts))


def _f(v):
    s = f"{v:.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def emit(vc, art, ox, oy, s, paint):
    """Draw `art` at origin (ox, oy), scale s (points per design unit). Returns the path ids.

    paint maps each role the art uses to a colour, or to None to leave that role's parts out
    (check_api.py draws the accent mask that way). Adjacent parts of one item with the same
    colour (compared case-insensitively) become one path; nothing else is merged."""
    ids = []
    for it in art.items:
        runs = []
        for role, pls in it[1]:
            colour = paint[role]
            if colour is None:
                continue
            if runs and runs[-1][0].lower() == colour.lower():
                runs[-1][1].extend(pls)
            else:
                runs.append((colour, list(pls)))
        for colour, pls in runs:
            if it[0] == "S":
                _, _, w, close, cap = it
                d = " ".join("M " + " L ".join(f"{_f(ox + x * s)} {_f(oy + y * s)}" for x, y in pl)
                             + (" Z" if close else "") for pl in pls)
                ids.append(vc.tool("draw_path", d=d, fill="none", stroke=colour, strokeWidth=round(w * s, 3))["id"])
                vc.cmd("stroke.set", cap=cap, join="round")
            else:
                d = " ".join("M " + " L ".join(f"{_f(ox + x * s)} {_f(oy + y * s)}" for x, y in pl) + " Z"
                             for pl in pls)
                ids.append(vc.tool("draw_path", d=d, fill=colour, stroke="none")["id"])
    return ids


# ---------------------------------------------------------------- the hero


X0 = 500.0
# (y_top, thickness, half_width): top flange (room temperature), 50 K, 4 K, still, cold plate,
# mixing chamber. No stage names or temperatures are drawn; they only name the rows here.
PLATES = [(80.0, 26.0, 270.0), (160.0, 16.0, 246.0), (234.0, 16.0, 220.0),
          (310.0, 16.0, 190.0), (398.0, 16.0, 160.0), (478.0, 20.0, 132.0)]
C = (500.0, 748.0)                 # dial centre = the snapshot point
R_OUT, R_IN = 200.0, 200.0 - BAND  # solid band of the dial
R_BASE = 184.0                     # tick baseline (fine circle)

CHIP = 84.0
CHIP_NOW = (60.0, -8.0)            # where the chip is now, relative to C
CHIP_PAST = [(-60.0, 14.0)]        # an earlier position, relative to C (phantom lines)
BR_PAD = 14.0                      # clearance between chip span and bracket inner edge
BR_T, BR_ARM = 12.0, 30.0          # bracket bar thickness and arm length

# coax bundle: x of the bundle centre where it passes each plate (relative to X0), and the
# sideways sway of its curve in each gap; four cables, 7.5 apart at the plates, fanning out
# up to FAN times wider in mid-gap like a real loom.
COAX_X = [-158.0, -146.0, -128.0, -108.0, -88.0, -66.0]
COAX_SWAY = [-18.0, 12.0, -16.0, 11.0, -12.0]
COAX_N, COAX_SP, FAN = 4, 8.0, 0.35
OUT_X = (84.0, 95.0)               # the two output lines (relative to X0)
OUT_SWAY = 14.0                    # their sway between the amplifier and the circulators


def plate_y(k):
    y, t, hw = PLATES[k]
    return y, y + t, hw


def bracket(x_bar, y0, y1, side):
    """Solid square bracket. side=+1 opens to the right ('['), -1 opens to the left (']')."""
    t, a = BR_T, BR_ARM
    if side > 0:
        pts = [(x_bar, y0), (x_bar + a, y0), (x_bar + a, y0 + t), (x_bar + t, y0 + t),
               (x_bar + t, y1 - t), (x_bar + a, y1 - t), (x_bar + a, y1), (x_bar, y1)]
    else:
        pts = [(x_bar, y0), (x_bar - a, y0), (x_bar - a, y0 + t), (x_bar - t, y0 + t),
               (x_bar - t, y1 - t), (x_bar - a, y1 - t), (x_bar - a, y1), (x_bar, y1)]
    return orient(pts)


def chip_fill(cx, cy, s):
    """Solid die with a knocked-out guard ring and a 3 x 3 lattice of cross-shaped qubits.

    Winding: die +1, guard-ring hole -1, refilled core +1, qubits and couplers -1. Couplers abut
    the qubit arms without overlapping them, so no region is ever wound twice the same way."""
    h = s / 2
    polys = [orient(rect_pts(cx - h, cy - h, cx + h, cy + h))]
    g0, g1 = 0.085 * s, 0.11 * s
    polys.append(orient(rect_pts(cx - h + g0, cy - h + g0, cx + h - g0, cy + h - g0), False))
    polys.append(orient(rect_pts(cx - h + g1, cy - h + g1, cx + h - g1, cy + h - g1)))
    sp, arm, aw, cw = s * 0.235, s * 0.085, s * 0.024, s * 0.011
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            x, y = cx + i * sp, cy + j * sp
            plus = [(x - aw, y - arm), (x + aw, y - arm), (x + aw, y - aw), (x + arm, y - aw), (x + arm, y + aw),
                    (x + aw, y + aw), (x + aw, y + arm), (x - aw, y + arm), (x - aw, y + aw), (x - arm, y + aw),
                    (x - arm, y - aw), (x - aw, y - aw)]
            polys.append(orient(plus, False))
            if i < 1:
                polys.append(orient(rect_pts(x + arm, y - cw, x + sp - arm, y + cw), False))
            if j < 1:
                polys.append(orient(rect_pts(x - cw, y + arm, x + cw, y + sp - arm), False))
    return polys


def offset_cables(seg, fan_mask):
    """Offset a bundle centreline into COAX_N parallel cables; fan_mask[j] in [0, 1] widens them."""
    out = []
    for i in range(COAX_N):
        base = (i - (COAX_N - 1) / 2) * COAX_SP
        pl = []
        for j, p in enumerate(seg):
            a = seg[max(j - 1, 0)]
            b = seg[min(j + 1, len(seg) - 1)]
            d = dist(a, b) or 1.0
            nx, ny = -(b[1] - a[1]) / d, (b[0] - a[0]) / d
            off = base * (1 + FAN * fan_mask[j])
            pl.append((p[0] + nx * off, p[1] + ny * off))
        out.append(pl)
    return out


def hero_art():
    A = Art()
    heavy, med, fine = [], [], []
    hatch_lines, hidden, solids = [], [], []
    cx, cy = C
    y0 = PLATES[0][0]
    _, b0, _ = plate_y(0)
    t1, b1, _ = plate_y(1)
    t2, b2, _ = plate_y(2)
    t3, b3, _ = plate_y(3)
    t4, b4, _ = plate_y(4)
    t5, b5, _ = plate_y(5)

    # ---- bores: where a tube or cable crosses a plate, the section stops at the tube wall (the
    # wall itself is the tube's own line, which runs on through the plate); cables sit in an open bore
    holes = {k: [] for k in range(len(PLATES))}
    for k in range(len(PLATES)):
        holes[k].append((X0 + COAX_X[k] - 17, X0 + COAX_X[k] + 17))       # coax bundle bore
    for k in (0, 1, 2, 3):
        holes[k].append((X0 - 52, X0 - 28))                                # still pumping line bore
    holes[0] += [(X0 + 138, X0 + 160), (X0 + 168, X0 + 180)]               # pulse tube, stage 1
    holes[1] += [(X0 + 142, X0 + 156), (X0 + 167, X0 + 176)]               # pulse tube, stage 2
    for k in (3, 4, 5):
        holes[k].append((X0 + OUT_X[0] - 8, X0 + OUT_X[1] + 8))            # output lines bore

    # ---- plates in section: heavy outline stopping at the bores, 45 degree hatch alternating per part
    for k, (y, t, hw) in enumerate(PLATES):
        hob = [("rect", a, y - 6, b, y + t + 6) for a, b in holes[k]]
        heavy += rejoin(clip_polyline(closed(rect_pts(X0 - hw, y, X0 + hw, y + t)), None, hob))
        hatch_lines += hatch(("rect", X0 - hw, y, X0 + hw, y + t), slope=1 if k % 2 == 0 else -1,
                             obs=[("rect", a - 1.5, y - 6, b + 1.5, y + t + 6) for a, b in holes[k]])
        for sx in (-1, 1):   # shield-mount lips under each plate end
            xa, xb = sorted((X0 + sx * (hw - 4), X0 + sx * (hw - 11)))
            solids.append(orient(rect_pts(xa, y + t, xb, y + t + 9)))
    for dx in (-244, -212, -100, 100, 212, 244):   # bolts on the top flange
        solids.append(orient(rect_pts(X0 + dx - 4.5, y0 - 5, X0 + dx + 4.5, y0)))

    # ---- support rods between plates (outer pair, medium)
    for k in range(len(PLATES) - 1):
        _, yb, _ = plate_y(k)
        yt, _, hw2 = plate_y(k + 1)
        for sx in (-1, 1):
            x = X0 + sx * (hw2 - 16)
            med.append([(x, yb), (x, yt)])

    # ---- still pumping line: one tube from the port above the flange, through four plates, into the still
    for x in (X0 - 52, X0 - 28):
        med.append([(x, 53), (x, b3)])
    solids.append(orient(rect_pts(X0 - 66, 45, X0 - 14, 53)))

    # ---- pulse-tube cold head: motor head, regenerator + pulse tube per stage, two heat stations
    head = (X0 + 128, 44, X0 + 192, y0)
    med.append(closed(rect_pts(*head)))
    for yy in (53, 60, 67):
        fine.append([(head[0] + 6, yy), (head[2] - 6, yy)])
    solids.append(orient(rect_pts(X0 + 142, 36, X0 + 178, 44)))
    st1 = ("rect", X0 + 130, t1 - 12, X0 + 188, t1)
    st2 = ("rect", X0 + 136, t2 - 12, X0 + 182, t2)
    for xa, xb in ((X0 + 138, X0 + 160), (X0 + 168, X0 + 180)):
        med.append([(xa, y0), (xa, st1[2])])
        med.append([(xb, y0), (xb, st1[2])])
    for xa, xb in ((X0 + 142, X0 + 156), (X0 + 167, X0 + 176)):
        med.append([(xa, t1), (xa, st2[2])])
        med.append([(xb, t1), (xb, st2[2])])
    for st, sl in ((st1, -1), (st2, 1)):
        med.append(closed(rect_pts(*st[1:])))
        hatch_lines += hatch(st, slope=sl)

    # ---- still pot (in section) under the still plate, helical continuous heat exchanger below
    wall = 5.0
    pot = (X0 - 66, b3, X0 + 26, b3 + 28)
    pot_in = (pot[0] + wall, pot[1], pot[2] - wall, pot[3] - wall)
    med.append(closed(rect_pts(*pot)))
    med.append([(pot_in[0], pot_in[1]), (pot_in[0], pot_in[3]), (pot_in[2], pot_in[3]), (pot_in[2], pot_in[1])])
    hatch_lines += hatch(("rect",) + pot, slope=-1, obs=[("rect", pot_in[0], pot_in[1] - 1, pot_in[2], pot_in[3])])
    fine.append([(pot_in[0] + 5, pot[1] + 13), (pot_in[2] - 5, pot[1] + 13)])     # liquid level in the still
    hx_c, hx_r, hy0, hy1, turns = X0 - 20, 22.0, pot[3] + 6, t4 - 3, 4
    fine.append([(hx_c, pot[3]), (hx_c, hy0)])
    n = 480
    front, back, cur, cur_front = [], [], [], None
    for i in range(n + 1):
        th = 2 * math.pi * turns * i / n
        p = (hx_c + hx_r * math.sin(th), hy0 + (hy1 - hy0) * i / n)
        f = math.cos(th) >= 0
        cur.append(p)
        if cur_front is not None and f != cur_front:
            (front if cur_front else back).append(cur)
            cur = [p]
        cur_front = f
    (front if cur_front else back).append(cur)
    med += front
    for pl in back:
        hidden += dash(pl, HIDDEN, 0)

    # ---- step heat exchangers under the cold plate; mixing-chamber pot (in section) on its plate
    blocks = [(X0 - 40, b4 + 5 + 16 * i, X0, b4 + 16 + 16 * i) for i in range(3)]
    for bx in blocks:
        med.append(closed(rect_pts(*bx)))
        hatch_lines += hatch(("rect",) + bx, slope=1)
    fine.append([(X0 - 20, b4), (X0 - 20, blocks[0][1])])
    for a, b in zip(blocks, blocks[1:]):
        fine.append([(X0 - 20, a[3]), (X0 - 20, b[1])])
    pot5 = (X0 + 30, t5 - 34, X0 + 70, t5)
    lid = (pot5[0] - 5, pot5[1] - 6, pot5[2] + 5, pot5[1])
    p5in = (pot5[0] + wall, pot5[1], pot5[2] - wall, pot5[3] - wall)
    med.append(closed(rect_pts(*pot5)))
    med.append([(p5in[0], p5in[1]), (p5in[0], p5in[3]), (p5in[2], p5in[3]), (p5in[2], p5in[1])])
    hatch_lines += hatch(("rect",) + pot5, slope=-1, obs=[("rect", p5in[0], p5in[1] - 1, p5in[2], p5in[3])])
    solids.append(orient(rect_pts(*lid)))
    fine.append([(p5in[0] + 3, p5in[1] + 14), (p5in[2] - 3, p5in[1] + 14)])     # phase boundary
    fine.append([(X0 - 20, blocks[-1][3]), (X0 - 20, t5 - 10), (pot5[0], t5 - 10)])

    # ---- cold finger from the mixing-chamber plate down to the dial
    cf = ("rect", X0 - 9, b5, X0 + 9, cy - R_OUT - 6)
    med.append(closed(rect_pts(*cf[1:])))
    hatch_lines += hatch(cf, slope=1)
    solids.append(orient(rect_pts(X0 - 26, cy - R_OUT - 6, X0 + 26, cy - R_OUT + 1)))

    # ---- coax bundle: from the feedthrough on the flange, through every plate, swaying in each gap
    dial_keepout = ("circle", cx, cy, R_OUT + 2.5)
    seg, mask = [], []
    xk = X0 + COAX_X[0]
    seg += [(xk, y0 - 14), (xk, b0)]
    mask += [0.0, 0.0]
    for k in range(len(PLATES) - 1):
        _, yb, _ = plate_y(k)
        yt, ybn, _ = plate_y(k + 1)
        ya = yb + (16 if k > 0 else 0)          # clamps sit under plates 1..5
        xa, xb = X0 + COAX_X[k], X0 + COAX_X[k + 1]
        if k > 0:
            seg.append((xa, ya))
            mask.append(0.0)
        xm, ym = (xa + xb) / 2 + COAX_SWAY[k], (ya + yt) / 2
        h = yt - ya
        c1 = bezier((xa, ya), (xa, ya + h / 4), (xm, ym - h / 4), (xm, ym), 20)
        c2 = bezier((xm, ym), (xm, ym + h / 4), (xb, yt - h / 4), (xb, yt), 20)[1:]
        curve = c1[1:] + c2
        seg += curve
        mask += [math.sin(math.pi * (j + 1) / len(curve)) for j in range(len(curve))]
        seg.append((xb, ybn))
        mask.append(0.0)
    xa = X0 + COAX_X[-1]
    end = (X0 - 84, cy - R_OUT + 30)
    tail = [(xa, b5 + 16)] + bezier((xa, b5 + 16), (xa, b5 + 50), (end[0], end[1] - 40), end, 24)[1:]
    seg += tail
    mask += [0.0] + [0.6 * math.sin(math.pi * min(j / 20, 1) / 2) for j in range(1, len(tail))]
    for pl in offset_cables(seg, mask):
        med += clip_polyline(pl, None, [dial_keepout])
    for k in range(1, len(PLATES)):            # attenuator clamps directly under plates 1..5
        _, yb, _ = plate_y(k)
        x = X0 + COAX_X[k]
        solids.append(orient(rect_pts(x - 17, yb, x + 17, yb + 12)))
    x = X0 + COAX_X[0]                          # hermetic feedthrough with four connectors
    med.append(closed(rect_pts(x - 20, y0 - 14, x + 20, y0)))
    for i in range(COAX_N):
        xx = x + (i - (COAX_N - 1) / 2) * COAX_SP
        fine.append([(xx, y0 - 14), (xx, 50)])
        solids.append(orient(rect_pts(xx - 2.6, 44, xx + 2.6, 50)))

    # ---- output lines: amplifier under the 4 K plate, two circulators above the MXC plate
    amp = ("rect", X0 + 70, b2, X0 + 108, b2 + 26)
    circs = [("rect", X0 + 73, b4 + 10, X0 + 105, b4 + 26), ("rect", X0 + 73, b4 + 32, X0 + 105, b4 + 48)]
    xc = X0 + sum(OUT_X) / 2
    ym = (b3 + t4) / 2
    hh = t4 - b3
    oc = [(xc, amp[4]), (xc, b3)]
    oc += bezier((xc, b3), (xc, b3 + hh / 4), (xc + OUT_SWAY, ym - hh / 4), (xc + OUT_SWAY, ym), 16)[1:]
    oc += bezier((xc + OUT_SWAY, ym), (xc + OUT_SWAY, ym + hh / 4), (xc, t4 - hh / 4), (xc, t4), 16)[1:]
    oc += [(xc, cy - 150)]
    half = (OUT_X[1] - OUT_X[0]) / 2
    for sgn in (-1, 1):
        pl = []
        for j, p in enumerate(oc):
            a, b = oc[max(j - 1, 0)], oc[min(j + 1, len(oc) - 1)]
            d = dist(a, b) or 1.0
            pl.append((p[0] - (b[1] - a[1]) / d * sgn * half, p[1] + (b[0] - a[0]) / d * sgn * half))
        med += clip_polyline(pl, None, [dial_keepout] + circs)
    med.append(closed(rect_pts(*amp[1:])))
    for i in range(1, 5):
        fine.append([(amp[1] + 4, b2 + 5 * i + 1), (amp[3] - 4, b2 + 5 * i + 1)])
    for c in circs:
        med.append(closed(rect_pts(*c[1:])))
        fine.append(closed(circle_pts((c[1] + c[3]) / 2, (c[2] + c[4]) / 2, 4.5, 28)))

    # ---- the dial (calibration ring) --------------------------------------------------------
    dial_fill = [orient(circle_pts(cx, cy, R_OUT)), orient(circle_pts(cx, cy, R_IN), False)]
    fine.append(closed(circle_pts(cx, cy, R_BASE)))
    ticks_f, ticks_m, knurl = [], [], []
    for k in range(120):
        deg = -90 + 3 * k
        if abs(((deg + 90 + 180) % 360) - 180) < 5:
            continue            # leave the index clear
        if k % 5 == 0:
            ticks_m.append([polar(C, R_BASE, deg), polar(C, R_BASE - 14, deg)])
        else:
            ticks_f.append([polar(C, R_BASE, deg), polar(C, R_BASE - 8, deg)])
    for k in range(180):        # knurled bezel outside the band, open where the fridge plugs in
        deg = 2 * k
        if 220 <= deg <= 320:
            continue
        knurl.append([polar(C, R_OUT + 4, deg), polar(C, R_OUT + 11, deg)])
    index = orient([polar(C, R_BASE - 22, -90), (cx + 8, cy - R_BASE + 1), (cx - 8, cy - R_BASE + 1)])
    # the snapshot point: a drafting datum (centre-of-mass) symbol, two opposite quadrants solid
    R_DAT = 9.0
    fine.append(closed(circle_pts(cx, cy, R_DAT, 48)))
    datum = [orient([C] + [polar(C, R_DAT, a) for a in range(-90, 1, 6)]),
             orient([C] + [polar(C, R_DAT, a) for a in range(90, 181, 6)])]

    # chip positions, span and brackets
    h = CHIP / 2
    now = (cx + CHIP_NOW[0], cy + CHIP_NOW[1])
    past = [(cx + dx, cy + dy) for dx, dy in CHIP_PAST]
    allc = [now] + past
    left = min(p[0] for p in allc) - h - BR_PAD
    right = max(p[0] for p in allc) + h + BR_PAD
    top = min(p[1] for p in allc) - h - BR_PAD - BR_T + 4
    bot = max(p[1] for p in allc) + h + BR_PAD + BR_T - 4
    brL = bracket(left - BR_T, top, bot, +1)
    brR = bracket(right + BR_T, top, bot, -1)
    chip_keep = ("rect", now[0] - h - 5, now[1] - h - 5, now[0] + h + 5, now[1] + h + 5)
    br_keep = [("rect", left - BR_T - 5, top - 5, left + BR_ARM - BR_T + 5, bot + 5),
               ("rect", right - BR_ARM + BR_T - 5, top - 5, right + BR_T + 5, bot + 5)]

    # centre lines: the fridge axis runs on through the dial; a horizontal one crosses it at C
    for pl in centre_line((X0, 22), (X0, cy + R_OUT + 16), C):
        fine += clip_polyline(pl, None, [chip_keep])
    for pl in centre_line((cx - R_BASE + 26, cy), (cx + R_BASE - 26, cy), C):
        fine += clip_polyline(pl, None, [chip_keep] + br_keep)

    # the earlier position: phantom outline with its own centre mark
    phantom = []
    for p in past:
        sq = closed(rect_pts(p[0] - h, p[1] - h, p[0] + h, p[1] + h))
        for pl in dash(sq, PHANTOM, 6):
            phantom += clip_polyline(pl, None, [chip_keep])
        fine.append([(p[0] - 7, p[1]), (p[0] + 7, p[1])])
        fine.append([(p[0], p[1] - 7), (p[0], p[1] + 7)])

    # the drift path: a dotted arc from the earlier centre into the chip, ending in an arrowhead
    p0 = past[0]
    trail = bezier(p0, (p0[0] + 30, p0[1] + 62), (now[0] - 44, now[1] + 66), now, 80)
    past_keep = ("rect", p0[0] - h - 5, p0[1] - h - 5, p0[0] + h + 5, p0[1] + h + 5)
    pieces = clip_polyline(trail, None, [chip_keep, past_keep])
    dots, trail_arrow = [], []
    for pl in pieces:
        dots += dash(pl, [6.0, 3.5], 0)
    if pieces:
        last = pieces[-1]
        tip = last[-1]
        back_pt = last[-4] if len(last) > 4 else last[0]
        trail_arrow.append(arrow(tip, back_pt, 12, 3.6))

    # dimension lines without numerals. The RANGE dimension (accent) spans the brackets: two
    # extension lines dropped from the bracket bars, the dimension line and its two arrowheads.
    # The DRIFT dimension (ink) measures the chip's offset from the datum, above the brackets.
    range_dims, range_arrows = [], []
    yd = bot + 22
    xl, xr = left - BR_T / 2, right + BR_T / 2
    range_dims.append([(xl, bot + 6), (xl, yd + 9)])
    range_dims.append([(xr, bot + 6), (xr, yd + 9)])
    range_dims.append([(xl + 12, yd), (xr - 12, yd)])
    range_arrows.append(arrow((xl, yd), (xr, yd)))
    range_arrows.append(arrow((xr, yd), (xl, yd)))
    drift_dims, drift_arrows = [], []
    yu = top - 22
    drift_dims.append([(now[0], now[1] - h - 6), (now[0], yu - 9)])
    drift_dims.append([(cx + 12, yu), (now[0] - 12, yu)])
    drift_arrows.append(arrow((cx, yu), (now[0], yu)))
    drift_arrows.append(arrow((now[0], yu), (cx, yu)))

    # ---- assemble in drawing order (back to front); only the range wears the accent
    A.stroke(hatch_lines, W_FINE)
    A.stroke(hidden, W_FINE)
    A.stroke(fine + ticks_f + knurl, W_FINE)
    A.stroke_parts([("accent", range_dims), ("ink", drift_dims)], W_FINE)
    A.stroke(phantom, W_FINE)
    A.stroke(dots, W_FINE)
    A.stroke(med + ticks_m, W_MED)
    A.stroke(heavy, W_HEAVY, cap="butt")
    A.fill(solids)
    A.fill(dial_fill)
    A.fill([index] + datum)
    A.fill_parts([("ink", trail_arrow), ("accent", range_arrows), ("ink", drift_arrows)])
    A.fill([brL, brR], role="accent")
    A.fill(chip_fill(now[0], now[1], CHIP))
    return A


# ---------------------------------------------------------------- the small marks


def small_art():
    """Favicon master on a 32-unit grid, every edge on a whole unit (crisp at 32 px).

    The dial (3-unit band), its snapshot index on the axis, the chip 4 units right of the axis,
    and bold brackets around it (the accent), each kept at least 0.8 units clear of the band."""
    A = Art()
    ring = [orient(circle_pts(16, 16, 15.5, 128)), orient(circle_pts(16, 16, 12.5, 128), False)]
    idx = orient(rect_pts(15, 3, 17, 8))
    chip = orient(rect_pts(17, 13, 23, 19))
    L = orient([(6, 10), (11, 10), (11, 12), (8, 12), (8, 20), (11, 20), (11, 22), (6, 22)])
    R = orient([(26, 10), (21, 10), (21, 12), (24, 12), (24, 20), (21, 20), (21, 22), (26, 22)])
    A.fill(ring)
    A.fill_parts([("ink", [idx, chip]), ("accent", [L, R])])
    return A


def small16_art():
    """The same mark hinted for 16 px on a 16-unit grid: one-pixel brackets, a 3-pixel chip."""
    A = Art()
    ring = [orient(circle_pts(8, 8, 7.75, 96)), orient(circle_pts(8, 8, 6.5, 96), False)]
    idx = orient(rect_pts(7, 1.5, 9, 4))
    chip = orient(rect_pts(8, 7, 11, 10))
    L = orient([(3, 5), (5, 5), (5, 6), (4, 6), (4, 10), (5, 10), (5, 11), (3, 11)])
    R = orient([(13, 5), (11, 5), (11, 6), (12, 6), (12, 10), (11, 10), (11, 11), (13, 11)])
    A.fill(ring)
    A.fill_parts([("ink", [idx, chip]), ("accent", [L, R])])
    return A


# ---------------------------------------------------------------- the API

_ART = {"hero": hero_art, "small": small_art, "small16": small16_art}
_HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def _variant(variant):
    if variant not in _ART:
        raise ValueError(f"variant {variant!r}: expected one of {VARIANTS}")
    return variant


@functools.lru_cache(maxsize=None)
def art(variant="hero"):
    """The variant's Art in design units (0..UNITS[variant]). Cached and shared: do not mutate."""
    return _ART[_variant(variant)]()


@functools.lru_cache(maxsize=None)
def box(variant="hero"):
    """(x0, y0, x1, y1) of the drawn art inside the unit square: every vertex of every path,
    stroked ones padded by half their stroke width (the reach of a round cap or join)."""
    u = UNITS[_variant(variant)]
    x0 = y0 = math.inf
    x1 = y1 = -math.inf
    for it in art(variant).items:
        pad = it[2] / 2 if it[0] == "S" else 0.0
        for _, pls in it[1]:
            for pl in pls:
                for x, y in pl:
                    x0, y0 = min(x0, x - pad), min(y0, y - pad)
                    x1, y1 = max(x1, x + pad), max(y1, y + pad)
    return (x0 / u, y0 / u, x1 / u, y1 / u)


def construction():
    """The hero's key geometry, in design units (1000 per side of the unit square, y down), for
    the brand guide's construction drawing. Computed from the same constants hero_art() uses, so
    the drawing's annotations cannot drift from the art. No side effects."""
    h = CHIP / 2
    now = (C[0] + CHIP_NOW[0], C[1] + CHIP_NOW[1])
    past = [(C[0] + dx, C[1] + dy) for dx, dy in CHIP_PAST]
    allc = [now] + past
    left = min(p[0] for p in allc) - h - BR_PAD
    right = max(p[0] for p in allc) + h + BR_PAD
    return dict(
        units=UNITS["hero"], box=box("hero"), axis_x=X0, datum=C,
        dial=dict(r_out=R_OUT, r_in=R_IN, r_base=R_BASE),
        plates=[dict(y_top=y, thickness=t, half_width=w) for y, t, w in PLATES],
        chip=dict(size=CHIP, now=now, past=past),
        interval=dict(left=left, right=right, bar=BR_T,
                      top=min(p[1] for p in allc) - h - BR_PAD - BR_T + 4,
                      bottom=max(p[1] for p in allc) + h + BR_PAD + BR_T - 4),
        weights=dict(heavy=W_HEAVY, medium=W_MED, fine=W_FINE, band=BAND, bracket=BR_T),
    )


def paint_for(colours, mono=False):
    """Validate a colours dict and return the role -> colour map the art is painted with.

    Requires "ink", and "accent" unless mono; every value "#rrggbb"; keys must be in ROLES.
    paper and the tints are accepted but unused (this design paints neither)."""
    unknown = sorted(set(colours) - set(ROLES))
    if unknown:
        raise ValueError(f"unknown colour roles {unknown}: expected keys from {ROLES}")
    for role in ("ink",) if mono else ("ink", "accent"):
        if role not in colours:
            raise ValueError(f"colours needs {role!r}")
    for role, value in colours.items():
        if not isinstance(value, str) or not _HEX.fullmatch(value):
            raise ValueError(f"colours[{role!r}] = {value!r}: expected '#rrggbb'")
    ink = colours["ink"]
    return {"ink": ink, "accent": ink if mono else colours["accent"]}


def draw_mark(vc, x, y, size, colours, variant="hero", mono=False):
    """Draw the mark into VectorCraft's ACTIVE document, its unit square mapped to the square
    with top-left (x, y) and side `size` (points, y down). Returns the ids of the paths drawn.

    variant: "hero", "small" or "small16" (see the module docstring). mono: paint everything in
    colours["ink"]. Strokes scale with the mark (stroke width = design weight * size / units)."""
    paint = paint_for(colours, mono)
    if not (isinstance(size, (int, float)) and math.isfinite(size) and size > 0):
        raise ValueError(f"size {size!r}: expected a finite positive number")
    return emit(vc, art(variant), x, y, size / UNITS[_variant(variant)], paint)

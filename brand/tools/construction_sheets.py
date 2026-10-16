"""Construction sheets of the technical cutaway mark: five engineering drawings that teach the
mathematics behind the logo, drawn in VectorCraft from the mark's own geometry.

Called by build_brand.Kit.construction() as build(kit, mod), where `kit` is the open Kit (its
VectorCraft session, new() and export()) and `mod` is brand/mark/mark.py as
build_brand.load_mark() imported it. Through kit.export (so the kit's manifest and
check_brand.py cover every file) it writes into <kit>/guide/:

    construction-1-overview                 the hero on its 1000-unit grid, with a title block
    construction-2-refrigerator             plates, rods, bores, coax loom, helix, hatching
    construction-3-dial                     radii, graduations, knurl, index, datum
    construction-4-interval                 chip lattice, drift curve, brackets, dimensions
    construction-5-lines-and-small-marks    line weights, dash patterns, the two small marks

each as .svg and .png (1x, opaque white ground).

Where the numbers come from
---------------------------
No number on a sheet is typed in this file. Each one is
  * a constant of mark.py (X0, PLATES, C, R_OUT, CENTRE, ...) or a value its functions return
    (box(), plate_y(), chip_fill(), bezier(), dash(), hatch(), arrow(), polar());
  * a local variable of mark.py's hero_art(), small_art() or small16_art(), read by running the
    function once under a tracer (class Trace) that copies the frame's locals when it returns
    (pot, hx_r, turns, blocks, left, right, top, bot, ...) and at named source lines inside its
    loops (the coax S-curves, the support rods);
  * a literal that exists only inside an expression of mark.py (the rod inset, the bracket trim,
    the dimension offsets), recovered from captured inputs and outputs, or a measurement of the
    geometry hero_art() emitted (bolts, clamps, connectors: found by shape and position).
Every recomputed point or curve is asserted against what hero_art() emitted, so a change to
mark.py that this module does not understand stops the build instead of drawing a stale sheet.
The words (names, units, formula notation) are the only text typed here. Formulas are ASCII
(theta, pi, sqrt) because the fonts do not all carry Greek letters.

Drawing model
-------------
A Sheet collects drawing operations on numbered layers (paper, grid, mark, guide lines,
dimensions, text pads, text) and emits them in layer order when finished, so a label drawn
early still lands on top. Text is created live in Space Mono or Space Grotesk and converted to
outlines in one pass at the end. Space Mono is monospaced (advance 0.612 em, measured), which
lets the layout compute every label's width before anything is drawn. Before export each sheet
asserts that no two labels overlap and that every label lies inside the sheet.

Side effects: VectorCraft documents opened and closed through kit.new/kit.export; files written
only into <kit>/guide/. Standard library only.
"""
import inspect
import math
import os
import re
import sys

# ---------------------------------------------------------------- appearance (px on the sheet)
PAPER = "#FFFFFF"
GRID_FINE = "#EEF0F3"       # design grid: minor lines
GRID_MAJOR = "#D9DDE2"      # design grid: labelled lines
MARK_INK = "#C4C9CF"        # the mark's ink role, pale, under the construction
MARK_ACCENT = "#8FC6CF"     # the mark's accent role (the range), pale
CON = "#B04A2E"             # construction: dimensions, leaders, formulas
TEXT = "#1F2328"            # names, titles, the sheet frame
FONT, MONO = "Space Grotesk", "Space Mono"
MONO_ADVANCE = 0.612        # Space Mono advance per em (612 of 1000 units, measured on outlines)
BODY = 14                   # labels and formulas; nothing on a sheet is set under SMALL
SMALL = 13
HEAD = 19                   # view titles
TITLE = 30                  # sheet title
LEAD = 1.42                 # line pitch as a multiple of the size
W_LEADER, W_DIM, W_EXT, W_FRAME, W_GUIDE = 1.0, 1.1, 0.8, 1.6, 1.2
ARROW_L, ARROW_HALF = 10.0, 3.0    # construction arrowheads
DOT_R = 2.6                 # leader anchor dot
PAD = 3.0                   # white pad around a label that sits on the drawing
SHOULDER = 22.0             # horizontal shoulder of a leader at its label
LABEL_GAP = 8.0             # vertical gap between stacked callouts
GUIDE_DASH = [7.0, 4.0]     # construction lines that are references, not geometry
FRAME_DASH = [16.0, 4.0, 3.0, 4.0]  # detail-view boundaries (long, short)
MARGIN = 40.0               # sheet margin
SHEETS = 5

# layers, back to front
L_PAPER, L_GRID, L_MARK, L_GUIDE, L_DIM, L_PAD, L_TEXT = range(7)



def fmt(v, nd=3):
    """A number as the sheets print it: up to nd decimals, trailing zeros dropped."""
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def pt(p, nd=2):
    return f"({fmt(p[0], nd)}, {fmt(p[1], nd)})"


def tw(s, size):
    """Width of a Space Mono string (advance box)."""
    return len(s) * MONO_ADVANCE * size


# ---------------------------------------------------------------- reading the mark
class Trace:
    """Run fn() once under sys.settrace and keep its frame's local variables.

    final: the locals when fn returns. at[key]: one snapshot per execution of the single source
    line of fn that contains `key`, taken just BEFORE that line runs. A probe that matches no line,
    or more than one, raises: mark.py has changed and the sheets must be revisited."""

    def __init__(self, fn, probes=()):
        src, first = inspect.getsourcelines(fn)
        line_of = {}
        for key in probes:
            hits = [first + i for i, s in enumerate(src) if key in s]
            if len(hits) != 1:
                raise RuntimeError(f"probe {key!r} matches {len(hits)} lines of {fn.__name__}: mark.py changed?")
            line_of[hits[0]] = key
        self.at = {k: [] for k in probes}
        self.final = {}
        code = fn.__code__

        def local(frame, event, arg):
            if event == "line" and frame.f_lineno in line_of:
                self.at[line_of[frame.f_lineno]].append(dict(frame.f_locals))
            elif event == "return":
                self.final = dict(frame.f_locals)
            return local

        def outer(frame, event, arg):
            return local if frame.f_code is code else None

        old = sys.gettrace()
        sys.settrace(outer)
        try:
            self.result = fn()
        finally:
            sys.settrace(old)

    def __getitem__(self, name):
        if name not in self.final:
            raise RuntimeError(f"hero_art() has no local {name!r}: mark.py changed?")
        return self.final[name]


def src_numbers(fn, key):
    """The numeric literals, in order, of the one source line of fn that contains `key`. For the
    few numbers that live only inside an expression of mark.py; each use is checked against the
    geometry the line produced."""
    src, _ = inspect.getsourcelines(fn)
    hits = [ln for ln in src if key in ln]
    if len(hits) != 1:
        raise RuntimeError(f"{key!r} matches {len(hits)} lines of {fn.__name__}: mark.py changed?")
    return [float(x) for x in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?", hits[0])]


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def is_rect(poly):
    """True when a polygon (or closed polyline) is an axis-aligned rectangle."""
    q = list(poly)
    if len(q) == 5 and q[0] == q[-1]:
        q = q[:4]
    if len(q) != 4:
        return False
    x0, y0, x1, y1 = bbox(q)
    return all((abs(x - x0) < 1e-9 or abs(x - x1) < 1e-9) and (abs(y - y0) < 1e-9 or abs(y - y1) < 1e-9)
               for x, y in q)


def rects(polys, pred=lambda b: True):
    """Bounding boxes of the axis-aligned rectangles among polys that satisfy pred(box)."""
    return [bbox(p) for p in polys if is_rect(p) and pred(bbox(p))]


def near(a, b, tol=1e-6):
    return abs(a - b) <= tol


def bezier_controls(mod, pts):
    """The four control points of the cubic Bezier that mark.bezier() sampled into pts (t = k/n).

    Solves B(t1) and B(t2) at t1 ~ 1/4 and t2 ~ 3/4 for the inner control points, then checks
    every sample. This MEASURES the control points from the emitted curve."""
    n = len(pts) - 1
    p0, p3 = pts[0], pts[-1]
    i1, i2 = max(1, round(n / 4)), min(n - 1, round(3 * n / 4))

    def coeffs(t):
        u = 1 - t
        return u ** 3, 3 * u * u * t, 3 * u * t * t, t ** 3
    a0, a1, a2, a3 = coeffs(i1 / n)
    b0, b1, b2, b3 = coeffs(i2 / n)
    det = a1 * b2 - a2 * b1
    sol = []
    for d in (0, 1):
        r1 = pts[i1][d] - a0 * p0[d] - a3 * p3[d]
        r2 = pts[i2][d] - b0 * p0[d] - b3 * p3[d]
        sol.append(((r1 * b2 - a2 * r2) / det, (a1 * r2 - b1 * r1) / det))
    p1, p2 = (sol[0][0], sol[1][0]), (sol[0][1], sol[1][1])
    chk = mod.bezier(p0, p1, p2, p3, n)
    if max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(chk, pts)) > 1e-6:
        raise RuntimeError("a curve of mark.py is not a cubic Bezier sampled by bezier(): mark.py changed?")
    return [p0, (round(p1[0], 9), round(p1[1], 9)), (round(p2[0], 9), round(p2[1], 9)), p3]


def stage_names(mod):
    """The plate rows' names as mark.py's comment on PLATES gives them (parentheticals dropped);
    'plate k' for every row when that comment cannot be read."""
    src = inspect.getsource(mod)
    m = re.search(r"#\s*\(y_top, thickness, half_width\):(.*?)\.", src, re.S)
    names = []
    if m:
        for part in m.group(1).split(","):
            part = re.sub(r"\(.*?\)", "", part.replace("#", " "))
            names.append(" ".join(part.split()))
    if len(names) != len(mod.PLATES) or not all(names):
        names = [f"plate {k}" for k in range(len(mod.PLATES))]
    return names


class Ctx:
    """What the sheets read from the mark: the module and hero_art()'s captured locals."""

    NEED = ("X0", "PLATES", "C", "R_OUT", "R_IN", "R_BASE", "BAND", "CHIP", "CHIP_NOW", "CHIP_PAST", "BR_PAD",
            "BR_T", "BR_ARM", "COAX_X", "COAX_SWAY", "COAX_N", "COAX_SP", "FAN", "OUT_X", "OUT_SWAY", "CENTRE",
            "PHANTOM", "HIDDEN", "HATCH", "W_HEAVY", "W_MED", "W_FINE", "UNITS", "hero_art", "small_art",
            "small16_art", "chip_fill", "bezier", "dash", "hatch", "centre_line", "arrow", "box", "draw_mark",
            "plate_y", "polar", "art")

    def __init__(self, kit, mod):
        missing = [n for n in self.NEED if not hasattr(mod, n)]
        if missing:
            raise RuntimeError(f"construction sheets are drawn for the technical cutaway mark; {kit.mark_name} "
                               f"lacks {missing}")
        self.kit, self.mod = kit, mod
        self.hero = Trace(mod.hero_art, probes=("curve = c1[1:] + c2", "med.append([(x, yb), (x, yt)])"))
        if self.hero.result.items != mod.art("hero").items:
            raise RuntimeError("the traced hero_art() differs from mark.art('hero')")
        self.small = Trace(mod.small_art)
        self.small16 = Trace(mod.small16_art)
        self.stages = stage_names(mod)
        self.source = "brand/mark/mark.py"
        self.U = mod.UNITS["hero"]
        # The construction() summary of mark.py must agree with what hero_art() drew.
        g, h = mod.construction(), self.hero
        for a, b in ((g["interval"]["left"], h["left"]), (g["interval"]["right"], h["right"]),
                     (g["interval"]["top"], h["top"]), (g["interval"]["bottom"], h["bot"]),
                     (g["chip"]["now"][0], h["now"][0]), (g["chip"]["now"][1], h["now"][1])):
            if not near(a, b):
                raise RuntimeError("mark.construction() disagrees with hero_art()")


def place_blocks(want, heights, top, bottom, gap=LABEL_GAP):
    """Tops for stacked label blocks (already in anchor order) that keep their order, do not
    overlap (gap between them) and minimise the sum of squared distances to `want`.

    With u_i = t_i - sum_{j<i}(h_j + gap) the spacing constraints become u_0 <= u_1 <= ...,
    so the optimum is the isotonic regression of w_i = want_i - sum_{j<i}(h_j + gap), found by
    pool-adjacent-violators, then clamped into [top, bottom - total height] (clamping keeps a
    monotone sequence monotone and optimal)."""
    off, acc = [], 0.0
    for h in heights:
        off.append(acc)
        acc += h + gap
    w = [a - o for a, o in zip(want, off)]
    pools = []                                  # [sum, count]
    for x in w:
        pools.append([x, 1])
        while len(pools) > 1 and pools[-2][0] / pools[-2][1] > pools[-1][0] / pools[-1][1]:
            s, c = pools.pop()
            pools[-1][0] += s
            pools[-1][1] += c
    u = [p[0] / p[1] for p in pools for _ in range(p[1])]
    hi = bottom - (off[-1] + heights[-1]) if heights else bottom
    u = [min(max(x, top), max(hi, top)) for x in u]
    return [x + o for x, o in zip(u, off)]


# ---------------------------------------------------------------- the sheet
class Sheet:
    """One drawing sheet: a VectorCraft document plus a layered display list."""

    def __init__(self, ctx, number, stem, subject, w, h, description):
        self.ctx, self.mod, self.vc = ctx, ctx.mod, ctx.kit.vc
        self.number, self.stem, self.subject, self.w, self.h = number, stem, subject, w, h
        ctx.kit.new(stem, w, h, f"SuperconducTED mark construction, sheet {number} of {SHEETS}: {subject}",
                    description)
        self.ops = []
        self.boxes = []          # text boxes: (x0, y0, x1, y1, text)
        self.details = {}        # detail letter -> its design-space window
        self.fill(L_PAPER, PAPER, [[(0, 0), (w, 0), (w, h), (0, h)]])

    # -------------------------------------------------- primitives (px)
    def _op(self, layer, *payload):
        self.ops.append((layer, len(self.ops)) + payload)

    def stroke(self, layer, colour, width, pls, cap="butt", close=False):
        pls = [list(p) for p in pls if len(p) >= 2]
        if pls:
            self._op(layer, "S", colour, width, cap, close, pls)

    def fill(self, layer, colour, polys):
        polys = [list(p) for p in polys if len(p) >= 3]
        if polys:
            self._op(layer, "F", colour, polys)

    def line(self, pts, w=W_DIM, colour=CON, layer=L_DIM, dash=None, cap="butt"):
        pls = self.mod.dash(list(pts), dash) if dash else [list(pts)]
        self.stroke(layer, colour, w, pls, cap)

    def circle(self, c, r, w=W_DIM, colour=CON, layer=L_DIM, dash=None, a0=0.0, a1=360.0):
        n = max(24, int(abs(a1 - a0) / 360 * 2 * math.pi * r / 2.0))
        pts = [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
                c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]
        self.line(pts, w, colour, layer, dash)

    def dot(self, p, r=DOT_R, colour=CON, layer=L_DIM):
        ring = [(p[0] + r * math.cos(2 * math.pi * k / 16), p[1] + r * math.sin(2 * math.pi * k / 16))
                for k in range(16)]
        self.fill(layer, colour, [ring])

    def square(self, p, r=3.5, colour=CON, layer=L_DIM, w=1.2):
        self.stroke(layer, colour, w, [[(p[0] - r, p[1] - r), (p[0] + r, p[1] - r), (p[0] + r, p[1] + r),
                                        (p[0] - r, p[1] + r), (p[0] - r, p[1] - r)]])

    def arrowhead(self, tip, toward, length=ARROW_L, half=ARROW_HALF, colour=CON, layer=L_DIM):
        d = math.hypot(tip[0] - toward[0], tip[1] - toward[1])
        ux, uy = (tip[0] - toward[0]) / d, (tip[1] - toward[1]) / d
        bx, by = tip[0] - ux * length, tip[1] - uy * length
        self.fill(layer, colour, [[tip, (bx - uy * half, by + ux * half), (bx + uy * half, by - ux * half)]])

    def rect_outline(self, x0, y0, x1, y1, w=W_DIM, colour=CON, layer=L_DIM, dash=None):
        self.line([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], w, colour, layer, dash)

    # -------------------------------------------------- text
    def text(self, s, x, baseline, size=BODY, colour=CON, font=MONO, style="Regular", anchor="start", pad=False):
        """Place one line of text; returns its box (x0, y0, x1, y1). Mono widths are exact
        advance boxes; Space Grotesk is measured on a live outline."""
        if any(c in s for c in "\u2013\u2014"):
            raise ValueError(f"en or em dash in {s!r}")
        width = tw(s, size) if font == MONO else self._measure(s, size, font, style)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        box = (x, baseline - 0.80 * size, x + width, baseline + 0.24 * size)
        self._op(L_TEXT, "T", s, x, baseline, size, colour, font, style)
        self.boxes.append(box + (s,))
        if pad:
            self.fill(L_PAD, PAPER, [[(box[0] - PAD, box[1] - PAD), (box[2] + PAD, box[1] - PAD),
                                      (box[2] + PAD, box[3] + PAD), (box[0] - PAD, box[3] + PAD)]])
        return box

    def _measure(self, s, size, font, style):
        vc = self.vc
        t = vc.tool("add_text", x=0, y=0, text=s, font=font, size=size, color=TEXT)["id"]
        vc.cmd("text.setStyle", id=t, style=style)
        n = vc.cmd("document.node", id=t, summary=True)
        b = n.get("bounds") or n["summary"]["bounds"]
        vc.cmd("select.set", ids=[t])
        vc.cmd("edit.clear")
        return b["width"]

    def block(self, lines, x, top, size=BODY, anchor="start", pad=False):
        """Lines as [(text, colour)] or [(text, colour, size)] from `top` down. Returns (box, attach y)."""
        y = top
        x0 = x1 = None
        first_mid = None
        for ln in lines:
            s, colour = ln[0], ln[1]
            sz = ln[2] if len(ln) > 2 else size
            y += 0.80 * sz
            b = self.text(s, x, y, sz, colour, anchor=anchor, pad=pad)
            if first_mid is None:
                first_mid = y - 0.32 * sz
            x0 = b[0] if x0 is None else min(x0, b[0])
            x1 = b[2] if x1 is None else max(x1, b[2])
            y += (LEAD - 0.80) * sz
        return (x0, top, x1, y), first_mid

    @staticmethod
    def block_height(lines, size=BODY):
        return sum(LEAD * (ln[2] if len(ln) > 2 else size) for ln in lines) - (LEAD - 1.04) * size

    @staticmethod
    def block_width(lines, size=BODY):
        return max(tw(ln[0], ln[2] if len(ln) > 2 else size) for ln in lines)

    # -------------------------------------------------- leaders and callouts
    def leader(self, anchor, attach, side, dot=True, knee_x=None):
        """Leader from a feature (anchor) to a label whose near edge is at attach = (x, y): an
        inclined line ending in a horizontal shoulder, the drafting convention. knee_x moves the
        knee out to a given x, so the shoulder crosses a margin horizontally."""
        if knee_x is None:
            knee_x = attach[0] - SHOULDER if side == "right" else attach[0] + SHOULDER
        self.line([anchor, (knee_x, attach[1]), attach], W_LEADER)
        if dot:
            self.dot(anchor)

    def column(self, items, side, x, top, bottom, size=BODY, knee_x=None, avoid=()):
        """Stack callouts in a column without overlap, each as near its anchor's height as the
        others allow, and draw a leader to each. items: dict(anchor=(px, py), lines=[...]).
        side 'right': text starts at x; 'left': text ends at x. avoid: (y0, y1) bands the
        leader shoulders must not run in (for example the rows of a grid's labels)."""
        items = sorted(items, key=lambda it: it["anchor"][1])
        mid = 0.48 * size                                # first line's middle, below the block top

        def clear(t, direction):
            for _ in range(len(avoid) + 1):
                hit = [(y0, y1) for y0, y1 in avoid if y0 < t + mid < y1]
                if not hit:
                    break
                y0, y1 = hit[0]
                t = (y1 - mid + 0.01) if direction > 0 else (y0 - mid - 0.01)
            return t

        for it in items:
            it["h"] = self.block_height(it["lines"], size)
        tops = place_blocks([it["anchor"][1] - mid for it in items], [it["h"] for it in items], top, bottom)
        for i in range(len(items)):
            t = tops[i] if not i else max(tops[i], tops[i - 1] + items[i - 1]["h"] + LABEL_GAP)
            tops[i] = clear(t, +1)
        if items and tops[-1] + items[-1]["h"] > bottom:  # push up from the bottom
            tops[-1] = clear(bottom - items[-1]["h"], -1)
            for i in range(len(items) - 2, -1, -1):
                tops[i] = clear(min(tops[i], tops[i + 1] - items[i]["h"] - LABEL_GAP), -1)
        if items and tops[0] < top - 0.5:
            raise RuntimeError(f"sheet {self.number}: callout column at x={x:.0f} overflows")
        for it, t in zip(items, tops):
            anchor = "start" if side == "right" else "end"
            box, m = self.block(it["lines"], x, t, size, anchor)
            attach = (x - 6, m) if side == "right" else (x + 6, m)
            self.leader(it["anchor"], attach, side, dot=it.get("dot", True), knee_x=knee_x)

    # -------------------------------------------------- dimensions
    def dim(self, p, q, label, offset=0.0, ext=(), size=BODY, text_side=1, along=0.5, inside=True, pad=True,
            tail=22.0):
        """Linear dimension between p and q (px), drawn offset along the left normal of p->q.
        ext: the feature points the two extension lines start from (default: none). The value
        is set horizontally beside the dimension line's midpoint; text_side picks the side."""
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        nx, ny = uy, -ux
        a = (p[0] + nx * offset, p[1] + ny * offset)
        b = (q[0] + nx * offset, q[1] + ny * offset)
        for f, e in zip(ext, (a, b)):
            if not f:
                continue
            fl = math.hypot(e[0] - f[0], e[1] - f[1])
            if fl > 1e-6:
                ex, ey = (e[0] - f[0]) / fl, (e[1] - f[1]) / fl
                self.line([(f[0] + ex * 3, f[1] + ey * 3), (e[0] + ex * 6, e[1] + ey * 6)], W_EXT)
        if inside:
            self.line([a, b], W_DIM)
            self.arrowhead(a, b)
            self.arrowhead(b, a)
        else:
            self.line([(a[0] - ux * tail, a[1] - uy * tail), a], W_DIM)
            self.line([b, (b[0] + ux * tail, b[1] + uy * tail)], W_DIM)
            self.line([a, b], W_DIM)
            self.arrowhead(a, (a[0] - ux, a[1] - uy))
            self.arrowhead(b, (b[0] + ux, b[1] + uy))
        if label:
            mx, my = a[0] + (b[0] - a[0]) * along, a[1] + (b[1] - a[1]) * along
            if abs(uy) < 0.5:       # mostly horizontal: value above (text_side 1) or below
                base = my - 6 if text_side > 0 else my + 6 + 0.8 * size
                return self.text(label, mx, base, size, CON, anchor="middle", pad=pad)
            base = my + 0.3 * size
            if text_side > 0:
                return self.text(label, mx + 8, base, size, CON, pad=pad)
            return self.text(label, mx - 8, base, size, CON, anchor="end", pad=pad)
        return None

    def angle(self, c, r, a0, a1, label, size=BODY, label_r=None, anchor="start", arrows=True):
        """Angle dimension: an arc of radius r about c from a0 to a1 degrees (y-down, so
        clockwise on screen), arrowheads at both ends, the value at the middle."""
        self.circle(c, r, W_DIM, a0=a0, a1=a1)
        if arrows:
            for a, s in ((a0, 1), (a1, -1)):
                t = math.radians(a)
                tip = (c[0] + r * math.cos(t), c[1] + r * math.sin(t))
                tang = (-math.sin(t) * s, math.cos(t) * s)
                self.arrowhead(tip, (tip[0] + tang[0], tip[1] + tang[1]), 8, 2.6)
        if label:
            m = math.radians((a0 + a1) / 2)
            lr = label_r or r + 10
            px, py = c[0] + lr * math.cos(m), c[1] + lr * math.sin(m)
            return self.text(label, px, py + 0.3 * size, size, CON, anchor=anchor, pad=True)
        return None

    # -------------------------------------------------- page furniture
    def header(self, title, sub):
        self.text(title, MARGIN, 62, TITLE, TEXT, font=FONT, style="Medium")
        self.text(sub, MARGIN, 96, BODY, TEXT)

    def view_title(self, s, x, baseline, sub=None):
        self.text(s, x, baseline, HEAD, TEXT, font=FONT, style="Medium")
        if sub:
            self.text(sub, x, baseline + 22, SMALL, TEXT)

    def title_block(self, x, y, w, scale_line):
        """Drawing title block: the name, the sheet, units, scale, build date and provenance."""
        ctx = self.ctx
        rows = [("SuperconducTED mark: technical cutaway", TEXT, 17, FONT),
                (f"sheet {self.number} of {SHEETS}: {self.subject}", TEXT, BODY, MONO),
                (f"units: design units, {fmt(ctx.U)} per side of the unit square, y down", TEXT, SMALL, MONO),
                (f"scale: {scale_line}", TEXT, SMALL, MONO),
                ("drawn by brand/tools/construction_sheets.py", TEXT, SMALL, MONO),
                (f"every number from {ctx.source}", CON, SMALL, MONO)]
        pitch = 30
        h = pitch * len(rows) + 12
        self.rect_outline(x, y, x + w, y + h, W_FRAME, TEXT, L_DIM)
        for i, (s, colour, size, font) in enumerate(rows):
            yy = y + pitch * i
            if i:
                self.line([(x, yy), (x + w, yy)], 0.8, TEXT)
            self.text(s, x + 12, yy + 21, size, colour, font=font, style="Medium" if font == FONT else "Regular")
        return h

    def frame(self):
        self.rect_outline(16, 16, self.w - 16, self.h - 16, W_FRAME, TEXT, L_DIM)

    # -------------------------------------------------- output
    def check(self):
        bad = []
        bs = self.boxes
        for i in range(len(bs)):
            a = bs[i]
            if a[0] < 18 or a[1] < 18 or a[2] > self.w - 18 or a[3] > self.h - 18:
                bad.append(f"outside the sheet: {a[4]!r}")
            for j in range(i + 1, len(bs)):
                b = bs[j]
                if a[0] < b[2] - 0.5 and b[0] < a[2] - 0.5 and a[1] < b[3] - 0.5 and b[1] < a[3] - 0.5:
                    bad.append(f"labels overlap: {a[4]!r} and {b[4]!r}")
        if bad:
            raise RuntimeError(f"sheet {self.number}: " + "; ".join(bad))

    def finish(self):
        self.check()
        vc, mod = self.vc, self.mod
        texts = []
        for op in sorted(self.ops, key=lambda o: (o[0], o[1])):
            kind = op[2]
            if kind == "S":
                _, _, _, colour, width, cap, close, pls = op
                d = " ".join("M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pl) + (" Z" if close else "")
                             for pl in pls)
                vc.tool("draw_path", d=d, fill="none", stroke=colour, strokeWidth=round(width, 3))
                vc.cmd("stroke.set", cap=cap, join="round")
            elif kind == "F":
                _, _, _, colour, polys = op
                d = " ".join("M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pl) + " Z" for pl in polys)
                vc.tool("draw_path", d=d, fill=colour, stroke="none")
            elif kind == "M":
                _, _, _, variant, X, Y, size, clip = op
                ids = list(mod.draw_mark(vc, X, Y, size, dict(ink=MARK_INK, accent=MARK_ACCENT), variant=variant))
                if clip:
                    x0, y0, x1, y1 = clip
                    cid = vc.tool("draw_path", d=f"M {x0:.2f} {y0:.2f} L {x1:.2f} {y0:.2f} L {x1:.2f} {y1:.2f} "
                                                f"L {x0:.2f} {y1:.2f} Z", fill="none", stroke="none")["id"]
                    vc.cmd("select.set", ids=ids + [cid])
                    vc.cmd("object.clippingMask.make")
            elif kind == "T":
                _, _, _, s, x, baseline, size, colour, font, style = op
                t = vc.tool("add_text", x=round(x, 2), y=round(baseline, 2), text=s, font=font, size=size,
                            color=colour)["id"]
                vc.cmd("text.setStyle", id=t, style=style)
                texts.append(t)
        if texts:
            vc.cmd("select.set", ids=texts)
            vc.cmd("type.createOutlines")
        vc.cmd("select.set", ids=[])
        self.ctx.kit.export(self.stem, folder="guide", print_files=False, png=[("", 1)], source=False,
                            transparent=False)


class View:
    """A window (x0, y0, x1, y1) of a mark's design space drawn at `scale` px per unit with its
    top-left corner at (left, top) on the sheet."""

    def __init__(self, sheet, window, left, top, scale):
        self.sh, self.win, self.left, self.top, self.s = sheet, window, left, top, scale

    def P(self, x, y=None):
        if y is None:
            x, y = x
        return (self.left + (x - self.win[0]) * self.s, self.top + (y - self.win[1]) * self.s)

    def Ps(self, pts):
        return [self.P(p) for p in pts]

    @property
    def px(self):
        x0, y0, x1, y1 = self.win
        return (self.left, self.top, self.left + (x1 - x0) * self.s, self.top + (y1 - y0) * self.s)

    def grid(self, minor, major, label_every=None, size=SMALL, labels=("top", "left"), fmt_=fmt):
        x0, y0, x1, y1 = self.win
        L, T, R, B = self.px
        fine, bold = [], []
        k = math.ceil(x0 / minor - 1e-9)
        while k * minor <= x1 + 1e-9:
            v = k * minor
            (bold if abs(v / major - round(v / major)) < 1e-9 else fine).append([self.P(v, y0), self.P(v, y1)])
            k += 1
        k = math.ceil(y0 / minor - 1e-9)
        while k * minor <= y1 + 1e-9:
            v = k * minor
            (bold if abs(v / major - round(v / major)) < 1e-9 else fine).append([self.P(x0, v), self.P(x1, v)])
            k += 1
        self.sh.stroke(L_GRID, GRID_FINE, 0.8, fine)
        self.sh.stroke(L_GRID, GRID_MAJOR, 1.0, bold)
        if label_every:
            k = math.ceil(x0 / label_every - 1e-9)
            while k * label_every <= x1 + 1e-9:
                v = k * label_every
                if "top" in labels:
                    self.sh.text(fmt_(v), self.P(v, y0)[0], T - 9, size, TEXT, anchor="middle")
                if "bottom" in labels:
                    self.sh.text(fmt_(v), self.P(v, y0)[0], B + 9 + 0.8 * size, size, TEXT, anchor="middle")
                k += 1
            k = math.ceil(y0 / label_every - 1e-9)
            while k * label_every <= y1 + 1e-9:
                v = k * label_every
                if "left" in labels:
                    self.sh.text(fmt_(v), L - 9, self.P(x0, v)[1] + 0.3 * size, size, TEXT, anchor="end")
                if "right" in labels:
                    self.sh.text(fmt_(v), R + 9, self.P(x0, v)[1] + 0.3 * size, size, TEXT)
                k += 1

    def label_bands(self, every, size=SMALL, pad=5.0):
        """The y bands of this view's side labels (every `every` units), for column(avoid=...)."""
        x0, y0, x1, y1 = self.win
        out = []
        k = math.ceil(y0 / every - 1e-9)
        while k * every <= y1 + 1e-9:
            base = self.P(x0, k * every)[1] + 0.3 * size
            out.append((base - 0.8 * size - pad, base + 0.24 * size + pad))
            k += 1
        return out

    def detail_marks(self, details, arm=12.0):
        """Corner marks around each detail's window, tagged with its letter, so a reader can find
        where each enlarged view comes from."""
        for tag, (x0, y0, x1, y1) in sorted(details.items()):
            (a, b), (c, e) = self.P(x0, y0), self.P(x1, y1)
            for cx, cy, sx, sy in ((a, b, 1, 1), (c, b, -1, 1), (c, e, -1, -1), (a, e, 1, -1)):
                self.sh.line([(cx + sx * arm, cy), (cx, cy), (cx, cy + sy * arm)], 1.6, CON, L_GUIDE)
            self.sh.text(tag, a - 5, b - 5, 16, CON, anchor="end", pad=True)

    def border(self):
        L, T, R, B = self.px
        self.sh.rect_outline(L, T, R, B, 1.0, TEXT, L_DIM)

    def mark(self, variant="hero"):
        units = self.sh.mod.UNITS[variant]
        X, Y = self.left - self.win[0] * self.s, self.top - self.win[1] * self.s
        x0, y0, x1, y1 = self.win
        full = x0 <= 0 and y0 <= 0 and x1 >= units and y1 >= units
        self.sh._op(L_MARK, "M", variant, X, Y, units * self.s, None if full else self.px)


# ---------------------------------------------------------------- sheet 1: overview
def windows(ctx):
    """The design-space windows of sheets 2, 3 and 4, from the geometry (drawn as detail frames
    on sheet 1). Margins are layout choices in design units."""
    mod, h = ctx.mod, ctx.hero
    hw0 = mod.PLATES[0][2]
    cx, cy = mod.C
    top = ctx.box[1] * ctx.U
    fridge = (mod.X0 - hw0 - 20, round(top - 8), mod.X0 + hw0 + 20, cy - mod.R_OUT + 52)
    r = mod.R_OUT + 24
    dial = (cx - r, cy - r, cx + r, cy + r)
    chip = (h["left"] - mod.BR_T - 26, h["top"] - 46, h["right"] + mod.BR_T + 26, h["yd"] + 26)
    return fridge, dial, chip


def sheet_overview(ctx):
    mod, h = ctx.mod, ctx.hero
    U = ctx.U
    W, H = 2000, 1430
    sh = Sheet(ctx, 1, "construction-1-overview", "overview", W, H,
               f"The hero mark on its {fmt(ctx.U)}-unit design grid with its key rows, box and datum.")
    S = 1.2
    v = View(sh, (0, 0, U, U), 104, 150, S)
    sh.header("Construction sheet 1 of 5: the mark on its design grid",
              f"The hero is drawn in a square of {fmt(U)} design units, y down; the kit's 1024 px files draw "
              f"1 unit as {fmt(1024 / U)} px. Pale: the mark. Red: its construction.")
    v.grid(U / 20, U / 10, U / 10)
    sh.text("x", v.px[2] + 28, v.top - 9, SMALL, TEXT)
    sh.text("y", v.left - 9, v.px[3] + 24, SMALL, TEXT, anchor="end")
    v.mark()
    L, T, R, B = v.px
    col_x = R + 70
    items = []

    # centre line through the whole square, phased like the mark's own (short dash on C)
    for pl in mod.centre_line((mod.X0, 0), (mod.X0, U), mod.C):
        sh.line(v.Ps(pl), W_GUIDE, CON, L_GUIDE)
    items.append(dict(anchor=v.P(mod.X0, 6), lines=[(f"centre line x = X0 = {fmt(mod.X0)}", CON),
                                                   ("refrigerator axis, dial centre, datum", TEXT)]))

    # visible box
    bx0, by0, bx1, by1 = (c * U for c in ctx.box)
    sh.rect_outline(*v.P(bx0, by0), *v.P(bx1, by1), W_GUIDE, CON, L_GUIDE, dash=GUIDE_DASH)
    fb = ctx.box
    items.append(dict(anchor=v.P(bx1, by0), lines=[
        ("visible box: box('hero') = (x0, y0, x1, y1)", TEXT),
        ("= (" + ", ".join(f"{q:.4f}" for q in fb) + ")", CON),
        (f"width {fb[2] - fb[0]:.4f}, height {fb[3] - fb[1]:.4f} of the square", CON),
        ("every vertex, strokes padded by half their width", TEXT)]))
    sh.dim(v.P(bx0, by1), v.P(bx1, by1), f"{fmt(bx1 - bx0, 1)}", offset=-(U - 12 - by1) * S,
           ext=(v.P(bx0, by1), v.P(bx1, by1)))
    sh.dim(v.P(bx0, by0), v.P(bx0, by1), f"{fmt(by1 - by0, 1)}", offset=-(bx0 - 190) * S,
           ext=(v.P(bx0, by0), v.P(bx0, by1)), text_side=-1)

    # plate rows
    for k, (y, t, hw) in enumerate(mod.PLATES):
        a = v.P(mod.X0 + hw, y)
        items.append(dict(anchor=a, lines=[(f"plate {k}, {ctx.stages[k]}: y_top = {fmt(y)}", CON),
                                           (f"thickness {fmt(t)}, half-width {fmt(hw)}", TEXT)]))

    # dial and datum
    cx, cy = mod.C
    c = v.P(cx, cy)
    sh.circle(c, mod.R_OUT * S, W_GUIDE, CON, L_GUIDE, dash=GUIDE_DASH)
    sh.line([(c[0] - 16, c[1]), (c[0] + 16, c[1])], 1.4)
    sh.line([(c[0], c[1] - 16), (c[0], c[1] + 16)], 1.4)
    a = mod.polar(mod.C, mod.R_OUT, -35)
    items.append(dict(anchor=v.P(a), lines=[(f"dial: R_OUT = {fmt(mod.R_OUT)} (sheet 3)", CON)]))
    items.append(dict(anchor=v.P(h["right"] + mod.BR_T, h["top"] + 6), lines=[
        (f"interval: x from {fmt(h['left'])} to {fmt(h['right'])} (sheet 4)", CON),
        (f"centred on X0: ({fmt(h['left'])} + {fmt(h['right'])}) / 2 = {fmt((h['left'] + h['right']) / 2)}", CON)]))

    # detail windows of sheets 2, 3 and 4 as corner marks, tagged on their left edges
    fr, di, ch = windows(ctx)
    for wx0, wy0, wx1, wy1 in (fr, di, ch):
        (x0, y0), (x1, y1) = v.P(wx0, wy0), v.P(wx1, wy1)
        arm = 26
        for cxp, cyp, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x1, y1, -1, -1), (x0, y1, 1, -1)):
            sh.line([(cxp + sx * arm, cyp), (cxp, cyp), (cxp, cyp + sy * arm)], 1.6, CON, L_GUIDE)
    tags = [(fr, "sheet 2: refrigerator"), (di, "sheet 3: dial"), (ch, "sheet 4: chip, interval")]
    for (wx0, wy0, wx1, wy1), tag in tags:
        a = v.P(wx0, wy0)
        box = sh.text(tag, L + 18, a[1] + 5, BODY, CON, pad=True)
        sh.line([(box[2] + 5, a[1]), a], W_LEADER)
        sh.dot(a)
    # C, labelled from the left along its own horizontal centre line
    box = sh.text(f"C = {pt(mod.C, 1)}: the datum", L + 18, c[1] + 5, BODY, CON, pad=True)
    sh.line([(box[2] + 5, c[1]), c], W_LEADER)
    sh.dot(c)

    sh.column(items, "right", col_x, T - 10, B - 250)
    sh.title_block(col_x - 20, B - 210, W - MARGIN - (col_x - 20),
                   f"1 unit = {fmt(S)} px on this sheet")
    sh.frame()
    sh.finish()


# ---------------------------------------------------------------- sheet 2: the refrigerator
def fridge_data(ctx):
    """Everything sheet 2 shows, read from hero_art() and checked against its output."""
    mod, h = ctx.mod, ctx.hero
    X0 = mod.X0
    d = dict(X0=X0, step=mod.HATCH * math.sqrt(2))
    d["plates"] = [dict(k=k, y=y, t=t, b=y + t, hw=hw) for k, (y, t, hw) in enumerate(mod.PLATES)]
    for k, p in enumerate(d["plates"]):
        if mod.plate_y(k) != (p["y"], p["b"], p["hw"]):
            raise RuntimeError("plate_y() disagrees with PLATES")
    # support rods: one probe snapshot per rod, just before it is appended
    rods = h.at["med.append([(x, yb), (x, yt)])"]
    insets = {round(s["hw2"] - abs(s["x"] - X0), 9) for s in rods}
    if len(insets) != 1:
        raise RuntimeError("support rods no longer share one inset")
    d["rod_inset"] = insets.pop()
    d["rods"] = [dict(k=s["k"], x=s["x"], y0=s["yb"], y1=s["yt"], hw2=s["hw2"]) for s in rods]
    # coax S-curves: control points measured from the two Beziers of each gap
    gaps = []
    for s in h.at["curve = c1[1:] + c2"]:
        b1 = bezier_controls(mod, s["c1"])
        b2 = bezier_controls(mod, [s["c1"][-1]] + s["c2"])
        gaps.append(dict(k=s["k"], xa=s["xa"], ya=s["ya"], xb=s["xb"], yt=s["yt"], xm=s["xm"], ym=s["ym"],
                         h=s["h"], b1=b1, b2=b2))
    fr = {round((g["b1"][1][1] - g["ya"]) / g["h"], 9) for g in gaps} | \
         {round((g["b2"][1][1] - g["ym"]) / g["h"], 9) for g in gaps}
    if len(fr) != 1:
        raise RuntimeError("coax control points are no longer at one fraction of the gap")
    d["ctrl_frac"] = fr.pop()
    drops = {round(g["ya"] - d["plates"][g["k"]]["b"], 9) for g in gaps if g["k"] > 0}
    if len(drops) != 1:
        raise RuntimeError("coax curves no longer start one fixed drop below the clamps")
    d["curve_drop"] = drops.pop()
    d["gaps"] = gaps
    d["tail"] = bezier_controls(mod, h["tail"])
    d["seg"], d["mask"] = h["seg"], h["mask"]
    probe0 = h.at["curve = c1[1:] + c2"][0]
    n = len(probe0["c1"]) - 1 + len(probe0["c2"])
    d["gap_mask"] = [math.sin(math.pi * (j + 1) / n) for j in range(n)]
    j0 = d["seg"].index(probe0["c1"][1])
    if any(abs(a - b) > 1e-12 for a, b in zip(d["mask"][j0:j0 + n], d["gap_mask"])):
        raise RuntimeError("the coax fan is no longer sin(pi (j + 1) / n) along a gap")
    tm = d["mask"][-len(h["tail"]):]
    d["tail_fan"] = round(max(tm), 9)
    d["tail_ramp"] = next(j for j, m in enumerate(tm) if abs(m - d["tail_fan"]) < 1e-12)
    if any(abs(m - d["tail_fan"] * math.sin(math.pi * min(j / d["tail_ramp"], 1) / 2)) > 1e-12
           for j, m in enumerate(tm) if j):
        raise RuntimeError("the coax tail fan changed shape")
    d["xk"] = [X0 + c for c in mod.COAX_X]
    # bores, and the hatch of each plate: family and line indices, measured on the hatch lines
    d["holes"] = h["holes"]
    fams = []
    for p in d["plates"]:
        x0, x1 = X0 - p["hw"], X0 + p["hw"]
        fam, ks = set(), set()
        for pl in h["hatch_lines"]:
            if all(x0 - 1e-6 <= q[0] <= x1 + 1e-6 and p["y"] - 1e-6 <= q[1] <= p["b"] + 1e-6 for q in pl):
                a, b = pl[0], pl[-1]
                if near(a[0] + a[1], b[0] + b[1], 1e-6):
                    f, c = 1, a[0] + a[1]
                elif near(a[0] - a[1], b[0] - b[1], 1e-6):
                    f, c = -1, a[0] - a[1]
                else:
                    raise RuntimeError("a hatch line is not at 45 degrees")
                kk = round(c / d["step"])
                if not near(c, kk * d["step"], 1e-6):
                    raise RuntimeError("hatch line off the global grid c = k * HATCH * sqrt(2)")
                fam.add(f)
                ks.add(kk)
        if len(fam) != 1:
            raise RuntimeError("a plate's hatch mixes directions")
        fams.append(dict(slope=fam.pop(), kmin=min(ks), kmax=max(ks), n=len(ks)))
    d["hatch"] = fams
    a, b = h["hatch_lines"][0][0], h["hatch_lines"][0][-1]
    ang = abs(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))) % 180
    d["hatch_angle"] = round(min(ang, 180 - ang), 6)
    # how far short of a bore the hatch stops: measured on the line ends next to plate 0's bores
    p0 = d["plates"][0]
    ends = [q for pl in h["hatch_lines"] for q in (pl[0], pl[-1])
            if p0["y"] + 1e-6 < q[1] < p0["b"] - 1e-6]
    clear = [a - q[0] for a, _ in d["holes"][0] for q in ends if 0 < a - q[0] < 5] + \
        [q[0] - b for _, b in d["holes"][0] for q in ends if 0 < q[0] - b < 5]
    d["hatch_clear"] = round(min(clear), 9)
    if any(abs(c - d["hatch_clear"]) > 1e-6 for c in clear):
        raise RuntimeError("hatch stops at more than one distance from the bores")
    keep = h["dial_keepout"]
    if keep[0] != "circle" or (keep[1], keep[2]) != tuple(mod.C):
        raise RuntimeError("dial keep-out is no longer a circle about C")
    d["keep_pad"] = keep[3] - mod.R_OUT
    # named parts (locals of hero_art)
    for name in ("pot", "pot_in", "wall", "hx_c", "hx_r", "hy0", "hy1", "turns", "n", "blocks", "pot5", "lid",
                 "p5in", "cf", "head", "st1", "st2", "amp", "circs", "xc", "ym", "hh", "half", "end"):
        d[name] = h[name]
    # parts that exist only as solids or lines: found by shape and position
    sol, fine, med = h["solids"], h["fine"], h["med"]
    y0 = mod.PLATES[0][0]
    d["bolts"] = rects(sol, lambda b: near(b[3], y0) and b[1] < y0 and b[2] - b[0] < 12)
    d["lips"] = rects(sol, lambda b: any(near(b[1], p["b"]) and (near(b[0], X0 - p["hw"] + 4) or
                                                                   near(b[2], X0 + p["hw"] - 4))
                                          for p in d["plates"]))
    d["clamps"] = rects(sol, lambda b: any(near((b[0] + b[2]) / 2, d["xk"][k]) and near(b[1], d["plates"][k]["b"])
                                           for k in range(1, len(d["plates"]))))
    d["cap"] = rects(sol, lambda b: near(b[3], d["head"][1]))
    d["foot"] = rects(sol, lambda b: near(b[1], d["cf"][4]))
    d["connectors"] = rects(sol, lambda b: abs((b[0] + b[2]) / 2 - d["xk"][0]) < 20 and b[3] < y0 - 14)
    d["feedthrough"] = rects(med, lambda b: near(b[3], y0) and near((b[0] + b[2]) / 2, d["xk"][0]))
    pump_x = [hole for hole in d["holes"][0] if hole[1] < X0 and hole[0] > X0 - 100]
    tubes = [pl for pl in med if len(pl) == 2 and pl[0][0] == pl[1][0] and pump_x and
             pl[0][0] in pump_x[0]]
    d["pump"] = dict(x=pump_x[0], y0=min(min(q[1] for q in pl) for pl in tubes),
                     y1=max(max(q[1] for q in pl) for pl in tubes))
    d["port"] = rects(sol, lambda b: near(b[3], d["pump"]["y0"]))
    horiz = [pl for pl in fine if len(pl) == 2 and near(pl[0][1], pl[1][1])]
    d["head_lines"] = sorted(pl[0][1] for pl in horiz if d["head"][0] < pl[0][0] < d["head"][2]
                             and d["head"][1] < pl[0][1] < d["head"][3])
    d["amp_lines"] = sorted(pl[0][1] for pl in horiz if d["amp"][1] < pl[0][0] < d["amp"][3]
                            and d["amp"][2] < pl[0][1] < d["amp"][4])
    d["liquid"] = [pl for pl in horiz if d["pot"][0] < pl[0][0] < d["pot"][2] and d["pot"][1] < pl[0][1] < d["pot"][3]]
    d["phase"] = [pl for pl in horiz if d["pot5"][0] < pl[0][0] < d["pot5"][2]
                  and d["pot5"][1] < pl[0][1] < d["pot5"][3]]
    discs = []
    for c in d["circs"]:
        cc = ((c[1] + c[3]) / 2, (c[2] + c[4]) / 2)
        for pl in fine:
            if len(pl) > 10 and all(math.hypot(q[0] - cc[0], q[1] - cc[1]) < 10 for q in pl):
                discs.append(round(math.hypot(pl[0][0] - cc[0], pl[0][1] - cc[1]), 6))
    d["disc_r"] = discs
    gap = [k for k in range(len(d["plates"]) - 1)
           if near((d["plates"][k]["b"] + d["plates"][k + 1]["y"]) / 2, d["ym"])]
    d["out_gap"] = gap[0] if len(gap) == 1 else None
    below = [p["k"] for p in d["plates"] if p["y"] >= max(c[4] for c in d["circs"])]
    d["circ_plate"] = min(below) if below else None
    if d["out_gap"] is None or d["circ_plate"] is None:
        raise RuntimeError("sheet 2 could not place the output lines or circulators between plates")
    for key in ("bolts", "lips", "clamps", "cap", "foot", "connectors", "feedthrough", "port", "head_lines",
                "amp_lines", "liquid", "phase", "disc_r"):
        if not d[key]:
            raise RuntimeError(f"sheet 2 could not find the {key} in hero_art()'s output: mark.py changed?")
    return d


def plate_at(d, y, edge):
    """Index of the plate whose top (edge 'y') or bottom (edge 'b') lies at y."""
    hits = [p["k"] for p in d["plates"] if near(p[edge], y)]
    if len(hits) != 1:
        raise RuntimeError(f"no single plate has its {edge} at y = {y}: mark.py changed?")
    return hits[0]


def sheet_refrigerator(ctx):
    mod = ctx.mod
    d = fridge_data(ctx)
    X0 = mod.X0
    W, H = 2200, 2990
    sh = Sheet(ctx, 2, "construction-2-refrigerator", "refrigerator", W, H,
               "The refrigerator: plates, rods, bores, coax loom, helix, hatching and parts, dimensioned.")
    sh.header("Construction sheet 2 of 5: the refrigerator",
              f"A sectioned side view of a dilution refrigerator: {len(mod.PLATES)} plates, the parts between them "
              "and the coax loom. Design units, y down.")
    fridge_win = windows(ctx)[0]
    S = 1.7
    v = View(sh, fridge_win, 607, 170, S)
    v.grid(10, 50, 50)
    v.mark()
    L, T, R, B = v.px
    P = v.P
    left_items, right_items = [], []
    plates = d["plates"]

    # coax loom construction over the main view: bundle centreline, control polygons, points
    sh.line(v.Ps([q for q in d["seg"]]), 1.0, CON, L_GUIDE)
    for g in d["gaps"]:
        for b in (g["b1"], g["b2"]):
            sh.line(v.Ps(b), 0.9, CON, L_GUIDE, dash=[4.0, 3.0])
            for q in b[1:3]:
                sh.square(P(q), 2.4, layer=L_GUIDE, w=1.0)
        sh.dot(P(g["xm"], g["ym"]), 2.4)
    for k, x in enumerate(d["xk"]):
        sh.dot(P(x, plates[k]["y"]), 2.2)

    ft = d["feedthrough"][0]
    con = d["connectors"]
    pu, po = d["pump"], d["port"][0]
    left_items.append(dict(anchor=P(ft[0], (ft[1] + ft[3]) / 2), lines=[
        ("coax feedthrough on the flange", TEXT),
        (f"x_0 +/- {fmt((ft[2] - ft[0]) / 2)}, y {fmt(ft[1])} to {fmt(ft[3])}; {len(con)} connectors", CON),
        (f"{fmt(con[0][2] - con[0][0])} x {fmt(con[0][3] - con[0][1])} at x_0 + (i - {fmt((mod.COAX_N - 1) / 2)}) * "
         f"{fmt(mod.COAX_SP)}", CON)]))
    left_items.append(dict(anchor=P(po[0], (po[1] + po[3]) / 2), lines=[
        ("still pumping line: one tube, two walls", TEXT),
        (f"x = X0 - {fmt(X0 - pu['x'][0])}, X0 - {fmt(X0 - pu['x'][1])}; y {fmt(pu['y0'])} to {fmt(pu['y1'])} "
         f"(plate {plate_at(d, pu['y1'], 'b')} bottom)", CON),
        (f"port flange {fmt(po[2] - po[0])} x {fmt(po[3] - po[1])} at y {fmt(po[1])}", CON)]))
    p0 = plates[0]
    left_items.append(dict(anchor=P(X0 - p0["hw"] + 34, p0["y"] + p0["t"] / 2), lines=[
        (f"section hatch at {fmt(d['hatch_angle'])} deg, spacing {fmt(mod.HATCH)}", TEXT),
        ("c = k * HATCH * sqrt(2), alternating (detail B)", CON)]))
    left_items.append(dict(anchor=P(d["xk"][1], plates[1]["y"]), lines=[
        ("coax bundle crosses plate k at", TEXT),
        ("x_k = X0 + COAX_X[k] = " + ", ".join(fmt(x) for x in d["xk"]), CON)]))
    cl = d["clamps"][0]
    left_items.append(dict(anchor=P(cl[0], (cl[1] + cl[3]) / 2), lines=[
        ("clamps under plates " + ", ".join(str(plate_at(d, c[1], "b")) for c in d["clamps"]), TEXT),
        (f"x_k +/- {fmt((cl[2] - cl[0]) / 2)}, {fmt(cl[3] - cl[1])} tall; curve starts "
         f"{fmt(d['curve_drop'])} below", CON)]))
    g1 = d["gaps"][1]
    left_items.append(dict(anchor=P(g1["xm"], g1["ym"]), lines=[
        ("per gap two cubic Beziers through M (detail A)", TEXT),
        ("M = (mid x + COAX_SWAY[k], mid y)", CON),
        ("COAX_SWAY = " + ", ".join(fmt(s) for s in mod.COAX_SWAY), CON)]))
    p2 = plates[2]
    bore = [hb for hb in d["holes"][2] if near((hb[0] + hb[1]) / 2, d["xk"][2])][0]
    left_items.append(dict(anchor=P(bore[0], p2["y"] + p2["t"] / 2), lines=[
        ("bores: the section stops at each tube wall", TEXT),
        (f"cables x_k +/- {fmt((bore[1] - bore[0]) / 2)}; hatch stops {fmt(d['hatch_clear'])} short", CON)]))
    rl = [r for r in d["rods"] if r["x"] < X0]
    rk = rl[2]
    left_items.append(dict(anchor=P(rk["x"], (rk["y0"] + rk["y1"]) / 2), lines=[
        (f"support rods: x = X0 +/- (hw[k+1] - {fmt(d['rod_inset'])})", TEXT),
        ("= X0 +/- " + ", ".join(fmt(r["hw2"] - d["rod_inset"]) for r in rl), CON)]))
    left_items.append(dict(anchor=P(d["pot"][0], (d["pot"][1] + d["pot"][3]) / 2), lines=[
        ("still pot, helix, step exchangers (detail C)", TEXT)]))
    tc = d["tail"]
    tmid = mod.bezier(*tc, 2)[1]
    left_items.append(dict(anchor=P(tmid), lines=[
        ("tail into the dial: one cubic Bezier", TEXT),
        (" ".join(pt(q, 1) for q in tc), CON),
        (f"cables cut at r = R_OUT + {fmt(d['keep_pad'])} from C", CON)]))

    head = d["head"]
    right_items.append(dict(anchor=P(head[2], (head[1] + head[3]) / 2), lines=[
        ("pulse-tube cold head (detail D)", TEXT),
        (f"X0 + {fmt(head[0] - X0)} to X0 + {fmt(head[2] - X0)}, y {fmt(head[1])} to {fmt(head[3])}", CON)]))
    bo = d["bolts"]
    right_items.append(dict(anchor=P(bo[-1][2], (bo[-1][1] + bo[-1][3]) / 2), lines=[
        (f"{len(bo)} bolts {fmt(bo[0][2] - bo[0][0])} x {fmt(bo[0][3] - bo[0][1])} on the flange at X0 +", TEXT),
        ("(" + ", ".join(fmt((b[0] + b[2]) / 2 - X0) for b in bo) + ")", CON)]))
    st1 = d["st1"]
    right_items.append(dict(anchor=P(st1[3], (st1[2] + st1[4]) / 2), lines=[
        (f"heat stations under plates {plate_at(d, d['st1'][4], 'y')} and {plate_at(d, d['st2'][4], 'y')} "
         "(detail D)", TEXT)]))
    lp = [b for b in d["lips"] if b[0] > X0]
    p1 = plates[1]
    lip1 = [b for b in lp if near(b[1], p1["b"])][0]
    right_items.append(dict(anchor=P(lip1[2], (lip1[1] + lip1[3]) / 2), lines=[
        (f"shield lips {fmt(lip1[2] - lip1[0])} x {fmt(lip1[3] - lip1[1])} under each plate end", TEXT),
        (f"x from X0 +/- (hw - {fmt(X0 + p1['hw'] - lip1[0])}) to X0 +/- (hw - {fmt(X0 + p1['hw'] - lip1[2])})",
         CON)]))
    rr = [r for r in d["rods"] if r["x"] > X0][1]
    right_items.append(dict(anchor=P(rr["x"], (rr["y0"] + rr["y1"]) / 2), lines=[
        (f"rods: x = X0 +/- (hw[k+1] - {fmt(d['rod_inset'])})", TEXT),
        (f"this one: {fmt(X0)} + ({fmt(rr['hw2'])} - {fmt(d['rod_inset'])}) = {fmt(rr['x'])}", CON)]))
    amp = d["amp"]
    right_items.append(dict(anchor=P(amp[3], (amp[2] + amp[4]) / 2), lines=[
        (f"amplifier under plate {plate_at(d, amp[2], 'b')}", TEXT),
        (f"X0 + {fmt(amp[1] - X0)} to X0 + {fmt(amp[3] - X0)}, y {fmt(amp[2])} to {fmt(amp[4])}", CON),
        (f"{len(d['amp_lines'])} fine lines at y = " + ", ".join(fmt(y) for y in d["amp_lines"]), CON)]))
    xc, half = d["xc"], d["half"]
    right_items.append(dict(anchor=P(xc + half + mod.OUT_SWAY, d["ym"]), lines=[
        (f"{len(mod.OUT_X)} output lines, one S-curve between plates {d['out_gap']}, {d['out_gap'] + 1}", TEXT),
        (f"OUT_X = X0 + {fmt(mod.OUT_X[0])}, X0 + {fmt(mod.OUT_X[1])}: centre {fmt(xc)} +/- {fmt(half)}", CON),
        (f"sway OUT_SWAY = {fmt(mod.OUT_SWAY)} at y = {fmt(d['ym'])}, gap {fmt(d['hh'])}", CON)]))
    c0, c1 = d["circs"]
    right_items.append(dict(anchor=P(c0[3], (c0[2] + c0[4]) / 2), lines=[
        (f"{len(d['circs'])} circulators above plate {d['circ_plate']}", TEXT),
        (f"X0 + {fmt(c0[1] - X0)} to {fmt(c0[3] - X0)}, y {fmt(c0[2])} to {fmt(c0[4])} and {fmt(c1[2])} to "
         f"{fmt(c1[4])}", CON),
        (f"ferrite disc r = {fmt(d['disc_r'][0])}", CON)]))
    p5 = d["pot5"]
    right_items.append(dict(anchor=P(p5[2], p5[3] - 8), lines=[
        ("mixing-chamber pot (detail C)", TEXT)]))
    cf = d["cf"]
    right_items.append(dict(anchor=P(cf[3], (cf[2] + cf[4]) / 2), lines=[
        ("cold finger (detail C)", TEXT),
        (f"X0 +/- {fmt((cf[3] - cf[1]) / 2)}, y {fmt(cf[2])} to C.y - R_OUT - "
         f"{fmt(mod.C[1] - mod.R_OUT - cf[4])} = {fmt(cf[4])}", CON)]))
    p5_ = plates[5]
    right_items.append(dict(anchor=P(X0 + p5_["hw"], p5_["y"] + p5_["t"] / 2), lines=[
        ("plates in section: table below", TEXT)]))

    bands = v.label_bands(50)
    sh.column(left_items, "left", L - 92, T, B, knee_x=L - 2, avoid=bands)
    sh.column(right_items, "right", R + 92, T, B, knee_x=R + 2, avoid=bands)
    sh.view_title("Main view", L, T - 34)

    # ------------------------------------------------ plate table
    ty = B + 60
    sh.view_title("Plates in section", MARGIN + 10, ty)
    cols = [("k", 0), ("plate", 30), ("y_top", 230), ("t", 300), ("bottom", 345), ("hw", 425),
            ("x span", 480), ("rods below", 590), ("bores x0..x1", 715), ("hatch", 1120)]
    hy = ty + 34
    sh.line([(MARGIN + 10, hy + 8), (MARGIN + 10 + 1370, hy + 8)], 0.8, TEXT)
    for name, dx in cols:
        sh.text(name, MARGIN + 10 + dx, hy, SMALL, TEXT)
    for k, p in enumerate(plates):
        y = hy + 32 + 26 * k
        rods_k = [r for r in d["rods"] if r["k"] == k]
        fam = d["hatch"][k]
        cells = [str(k), ctx.stages[k], fmt(p["y"]), fmt(p["t"]), fmt(p["b"]), fmt(p["hw"]),
                 f"{fmt(X0 - p['hw'])}..{fmt(X0 + p['hw'])}",
                 ", ".join(fmt(r["x"]) for r in rods_k) or "none",
                 " ".join(f"{fmt(a)}..{fmt(b)}" for a, b in sorted(d["holes"][k])),
                 f"{'/' if fam['slope'] > 0 else chr(92)}  k = {fam['kmin']}..{fam['kmax']} ({fam['n']})"]
        for (name, dx), s in zip(cols, cells):
            sh.text(s, MARGIN + 10 + dx, y, SMALL, CON if dx else TEXT)
    ny = hy + 32 + 26 * len(plates) + 4
    sh.line([(MARGIN + 10, ny - 22), (MARGIN + 10 + 1370, ny - 22)], 0.8, TEXT)
    notes = [f"bottom = y_top + t; x span = X0 +/- hw with X0 = {fmt(X0)}; rods below plate k stand on it and "
             f"carry plate k+1: x = X0 +/- (hw[k+1] - {fmt(d['rod_inset'])})",
             f"hatch: '/' lines x + y = c, '{chr(92)}' lines x - y = c, c = k * {fmt(mod.HATCH)} * sqrt(2) = "
             f"k * {fmt(d['step'], 4)}, k integer for every line measured; (n) lines drawn, a line wholly "
             f"inside a bore is dropped"]
    for i, s in enumerate(notes):
        sh.text(s, MARGIN + 10, ny + 4 + 22 * i, SMALL, TEXT)

    sh.title_block(W - MARGIN - 620, B + 70, 620, f"main view 1 unit = {fmt(S)} px; details as marked")
    row2 = ny + 120
    detail_coax(sh, ctx, d, 100, row2)
    detail_hatch(sh, ctx, d, 1290, row2)
    detail_column(sh, ctx, d, 100, row2 + 560)
    detail_head(sh, ctx, d, 1290, row2 + 730)
    v.detail_marks(sh.details)
    sh.frame()
    sh.finish()


def helix_points(d):
    """The helix as hero_art() samples it: theta_i = 2 pi turns i / n, x = xc + r sin(theta),
    y = y0 + (y1 - y0) i / n; split where cos(theta) changes sign (front: cos >= 0)."""
    n, turns = d["n"], d["turns"]
    front, back, cur, cur_f = [], [], [], None
    for i in range(n + 1):
        th = 2 * math.pi * turns * i / n
        p = (d["hx_c"] + d["hx_r"] * math.sin(th), d["hy0"] + (d["hy1"] - d["hy0"]) * i / n)
        f = math.cos(th) >= 0
        cur.append(p)
        if cur_f is not None and f != cur_f:
            (front if cur_f else back).append(cur)
            cur = [p]
        cur_f = f
    (front if cur_f else back).append(cur)
    return front, back


def detail_coax(sh, ctx, d, left, top):
    """Detail A: the construction of one gap of the coax loom (gap 0)."""
    mod = ctx.mod
    g = d["gaps"][0]
    S = 6.0
    win = (min(g["xm"], g["xa"]) - 34, g["ya"] - 10, max(g["xa"], g["xb"]) + 38, g["yt"] + 10)
    sh.details["A"] = win
    sh.view_title(f"Detail A: one gap of the coax loom (gap 0), scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(2, 10, 10)
    v.mark()
    P = v.P
    curve = mod.bezier(*g["b1"], 40) + mod.bezier(*g["b2"], 40)[1:]
    sh.line(v.Ps(curve), 1.6, CON, L_GUIDE)
    for b in (g["b1"], g["b2"]):
        sh.line(v.Ps(b), 1.1, CON, L_GUIDE, dash=[6.0, 4.0])
    names = [("P0", g["b1"][0], 1), ("P1", g["b1"][1], 1), ("P2", g["b1"][2], -1), ("M", g["b1"][3], -1),
             ("Q1", g["b2"][1], -1), ("Q2", g["b2"][2], 1), ("Q3", g["b2"][3], 1)]
    for name, q, side in names:
        c = P(q)
        sh.square(c, 4.0, w=1.4)
        sh.text(name, c[0] + 10 * side, c[1] + 5, BODY, CON, anchor="start" if side > 0 else "end", pad=True)
    # h and h/4 on the right, sway at M
    xr = win[2] - 8
    sh.dim(P(xr, g["ya"]), P(xr, g["yt"]), f"h = {fmt(g['h'])}", offset=0,
           ext=(P(g["xa"] + 4, g["ya"]), P(g["xb"] + 4, g["yt"])), size=SMALL, text_side=-1)
    q1 = g["b2"][1]
    xl = win[0] + 6
    sh.dim(P(xl, g["ym"]), P(xl, q1[1]), f"h/{fmt(1 / d['ctrl_frac'])}", offset=0,
           ext=(P(g["xm"] - 18, g["ym"]), P(q1[0] - 18, q1[1])), size=SMALL, text_side=1, inside=False)
    mid = ((g["xa"] + g["xb"]) / 2, g["ym"])
    sh.line([(P(mid)[0] - 7, P(mid)[1]), (P(mid)[0] + 7, P(mid)[1])], 1.2)
    sh.line([(P(mid)[0], P(mid)[1] - 7), (P(mid)[0], P(mid)[1] + 7)], 1.2)
    yy = g["ym"] + 9
    sh.dim(P(mid[0], yy), P(g["xm"], yy), f"sway {fmt(mod.COAX_SWAY[0])}", offset=0,
           ext=(P(mid[0], g["ym"] + 1.5), P(g["xm"], g["ym"] + 1.5)), size=SMALL, text_side=-1)
    # the four cables at M: offsets along the normal
    j = d["seg"].index(g["b1"][3])
    cables = mod.offset_cables(d["seg"], d["mask"])
    for i, cab in enumerate(cables):
        q = cab[j]
        off = (i - (mod.COAX_N - 1) / 2) * mod.COAX_SP * (1 + mod.FAN * d["mask"][j])
        sh.dot(P(q), 3.0)
        sh.text(fmt(off, 2), P(q)[0], P(q)[1] - 10, SMALL, CON, anchor="middle", pad=True)
    k = d["seg"].index((g["xa"], g["ya"]))
    if abs(d["mask"][j] - 1) > 1e-9 or abs(d["mask"][k]) > 1e-9:
        raise RuntimeError("the coax fan is no longer 0 at the plates and 1 at M")
    n = len(d["gap_mask"])
    q = fmt(1 / d["ctrl_frac"])
    lines = [
        ("Centre curve: two cubic Beziers, P0 P1 P2 M and M Q1 Q2 Q3:", TEXT),
        ("B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 M", CON),
        ("P0 = (x_k, y_a), Q3 = (x_k+1, y_b), h = y_b - y_a", CON),
        ("M = ((x_k + x_k+1)/2 + COAX_SWAY[k], (y_a + y_b)/2)", CON),
        (f"P1 = P0 + (0, h/{q}), P2 = M - (0, h/{q})", CON),
        (f"Q1 = M + (0, h/{q}), Q2 = Q3 - (0, h/{q})", CON),
        ("so the curve is vertical at P0, at M and at Q3.", TEXT),
        (f"gap 0: P0 = {pt(g['b1'][0])}, Q3 = {pt(g['b2'][3])}, h = {fmt(g['h'])}", CON),
        (f"M = (({fmt(g['xa'])} + {fmt(g['xb'])})/2 + ({fmt(mod.COAX_SWAY[0])}), "
         f"({fmt(g['ya'])} + {fmt(g['yt'])})/2) = {pt(g['b1'][3])}", CON),
        (f"Cables i = 0..{mod.COAX_N - 1}, offset along the curve's normal:", TEXT),
        ("off = (i - (COAX_N - 1)/2) * COAX_SP * (1 + FAN * f_j)", CON),
        (f"    = (i - {fmt((mod.COAX_N - 1) / 2)}) * {fmt(mod.COAX_SP)} * (1 + {fmt(mod.FAN)} * f_j)", CON),
        (f"f_j = sin(pi * (j + 1) / {n}), j = 0..{n - 1}: the gap's samples", CON),
        ("f = 0 at the plates: offsets " + ", ".join(
            fmt((i - (mod.COAX_N - 1) / 2) * mod.COAX_SP, 2) for i in range(mod.COAX_N)), CON),
        ("f = 1 at M: offsets " + ", ".join(
            fmt((i - (mod.COAX_N - 1) / 2) * mod.COAX_SP * (1 + mod.FAN), 2) for i in range(mod.COAX_N)), CON),
        ("The normal n = (-t_y, t_x) of the downward tangent t points", TEXT),
        ("to -x, so a positive offset lies left of the centre curve.", TEXT),
        (f"tail: f = {fmt(d['tail_fan'])} * sin(pi/2 * min(j/{d['tail_ramp']}, 1))", CON),
    ]
    sh.block(lines, v.px[2] + 36, top, SMALL)


def detail_column(sh, ctx, d, left, top):
    """Detail C: the centre column: still pot, helix, step exchangers, mixing-chamber pot, cold finger."""
    mod = ctx.mod
    X0 = mod.X0
    S = 2.6
    pot, pot5, cf, foot = d["pot"], d["pot5"], d["cf"], d["foot"][0]
    win = (pot[0] - 9, pot[1] - 8, d["circs"][0][3] + 7, foot[3] + 3)
    sh.details["C"] = win
    sh.view_title(f"Detail C: the centre column, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(5, 10, 20)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    pl = d["plates"]
    # helix: axis, front solid and back dashed, recomputed from its formula and checked
    front, back = helix_points(d)
    hf = ctx.hero["front"]
    if len(front) != len(hf) or any(max(math.hypot(a[0] - b[0], a[1] - b[1]) for a, b in zip(f1, f2)) > 1e-9
                                    for f1, f2 in zip(front, hf)):
        raise RuntimeError("the helix is no longer x = xc + r sin(theta), y = y0 + (y1 - y0) i / n")
    for pl_ in front:
        sh.line(v.Ps(pl_), 1.5, CON, L_GUIDE)
    for pl_ in back:
        sh.line(v.Ps(pl_), 1.2, CON, L_GUIDE, dash=[5.0, 3.5])
    for q in mod.centre_line((d["hx_c"], d["hy0"] - 5), (d["hx_c"], d["hy1"] + 2),
                             (d["hx_c"], (d["hy0"] + d["hy1"]) / 2)):
        sh.line(v.Ps(q), 1.0, CON, L_GUIDE)
    pitch = (d["hy1"] - d["hy0"]) / d["turns"]
    xr = d["hx_c"] + d["hx_r"]
    sh.dim(P(d["hx_c"], pot[3] + 3), P(xr, pot[3] + 3), f"r = {fmt(d['hx_r'])}", offset=0,
           ext=(), size=SMALL, text_side=1, inside=False, along=1.9)
    sh.dim(P(xr + 9, d["hy0"]), P(xr + 9, d["hy0"] + pitch), f"pitch {fmt(pitch, 3)}", offset=0,
           ext=(P(d["hx_c"] + 2, d["hy0"]), P(d["hx_c"] + 2, d["hy0"] + pitch)), size=SMALL, text_side=1,
           inside=False)
    # step exchangers: height and pitch on the left
    bl = d["blocks"]
    xs = bl[0][0] - 8
    sh.dim(P(xs, bl[0][1]), P(xs, bl[0][3]), f"{fmt(bl[0][3] - bl[0][1])}", offset=0,
           ext=(P(bl[0][0], bl[0][1]), P(bl[0][0], bl[0][3])), size=SMALL, text_side=-1, inside=False)
    sh.dim(P(xs - 12, bl[0][1]), P(xs - 12, bl[1][1]), f"{fmt(bl[1][1] - bl[0][1])}", offset=0,
           ext=(P(bl[0][0], bl[0][1]), P(bl[1][0], bl[1][1])), size=SMALL, text_side=-1, inside=False)
    # cold finger: width and length
    yc = (cf[2] + cf[4]) / 2 + 6
    sh.dim(P(cf[1], yc), P(cf[3], yc), f"{fmt(cf[3] - cf[1])}", offset=0, size=SMALL, text_side=1,
           inside=False, along=2.4)
    sh.dim(P(cf[1] - 9, cf[2]), P(cf[1] - 9, cf[4]), f"{fmt(cf[4] - cf[2])}", offset=0,
           ext=(P(cf[1], cf[2]), P(cf[1], cf[4])), size=SMALL, text_side=-1)
    b3, t4, b4, t5, b5 = pl[3]["b"], pl[4]["y"], pl[4]["b"], pl[5]["y"], pl[5]["b"]
    lid, pin = d["lid"], d["pot_in"]

    def rel(x):
        return "X0" if near(x, X0) else f"X0 {'+' if x > X0 else '-'} {fmt(abs(x - X0))}"
    items = [
        dict(anchor=P(pot[2], pot[1] + 6), lines=[
            ("still pot, in section, wall " + fmt(d["wall"]), TEXT),
            (f"x {rel(pot[0])} to {rel(pot[2])}, y b3 = {fmt(b3)} to b3 + {fmt(pot[3] - b3)}", CON)]),
        dict(anchor=P(pin[2] - 6, d["liquid"][0][0][1]), lines=[
            (f"liquid level y = b3 + {fmt(d['liquid'][0][0][1] - b3)} = {fmt(d['liquid'][0][0][1])}", CON)]),
        dict(anchor=P(xr, d["hy0"] + 2.6 * pitch), lines=[
            ("helix (continuous heat exchanger), side view", TEXT),
            ("x = xc + r sin(theta)", CON),
            ("y = y0 + (y1 - y0) * theta / (2 pi turns)", CON),
            (f"xc = X0 - {fmt(X0 - d['hx_c'])} = {fmt(d['hx_c'])}, r = {fmt(d['hx_r'])}, turns = {d['turns']}", CON),
            (f"y0 = pot bottom + {fmt(d['hy0'] - pot[3])} = {fmt(d['hy0'])}, y1 = t4 - {fmt(t4 - d['hy1'])} = "
             f"{fmt(d['hy1'])}", CON),
            (f"{d['n']} samples; front (cos theta >= 0) solid,", CON),
            ("back hidden-dashed, the pattern restarted per half", CON)]),
        dict(anchor=P(bl[0][2], (bl[0][1] + bl[0][3]) / 2), lines=[
            (f"{len(bl)} step heat exchangers, hatched '/'", TEXT),
            (f"x {rel(bl[0][0])} to {rel(bl[0][2])}, top y = b4 + {fmt(bl[0][1] - b4)} + "
             f"{fmt(bl[1][1] - bl[0][1])} i", CON),
            ("= " + ", ".join(fmt(b[1]) for b in bl) + f"; each {fmt(bl[0][3] - bl[0][1])} tall", CON)]),
        dict(anchor=P(pot5[2], pot5[3] - 8), lines=[
            (f"mixing-chamber pot, in section, on plate {plate_at(d, pot5[3], 'y')}", TEXT),
            (f"x {rel(pot5[0])} to {rel(pot5[2])}, y t5 - {fmt(t5 - pot5[1])} to t5 = {fmt(t5)}", CON),
            (f"lid {fmt(lid[2] - lid[0])} x {fmt(lid[3] - lid[1])}; phase boundary y = "
             f"{fmt(d['phase'][0][0][1])}", CON)]),
        dict(anchor=P(cf[3], cf[2] + 10), lines=[
            ("cold finger, hatched '/'", TEXT),
            (f"x = X0 +/- {fmt((cf[3] - cf[1]) / 2)}, y b5 = {fmt(b5)} to C.y - R_OUT - "
             f"{fmt(mod.C[1] - mod.R_OUT - cf[4])} = {fmt(cf[4])}", CON)]),
        dict(anchor=P(foot[2], (foot[1] + foot[3]) / 2), lines=[
            (f"foot: X0 +/- {fmt((foot[2] - foot[0]) / 2)}, y {fmt(foot[1])} to {fmt(foot[3])}, "
             f"on the dial", CON)]),
    ]
    sh.column(items, "right", R + 70, T, B + 40, size=SMALL, knee_x=R + 2, avoid=v.label_bands(20))


def detail_head(sh, ctx, d, left, top):
    """Detail D: the pulse-tube cold head with its tubes and heat stations."""
    mod = ctx.mod
    X0 = mod.X0
    S = 2.6
    head, cap, st1, st2 = d["head"], d["cap"][0], d["st1"], d["st2"]
    win = (head[0] - 13, cap[1] - 14, head[2] + 13, st2[4] + 6)
    sh.details["D"] = win
    sh.view_title(f"Detail D: the pulse-tube cold head, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(5, 10, 20)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    sh.dim(P(head[0], cap[1] - 6), P(head[2], cap[1] - 6), f"{fmt(head[2] - head[0])}", offset=0,
           ext=(P(head[0], head[1]), P(head[2], head[1])), size=SMALL)
    sh.dim(P(head[0] - 6, head[1]), P(head[0] - 6, head[3]), f"{fmt(head[3] - head[1])}", offset=0,
           ext=(P(head[0], head[1]), P(head[0], head[3])), size=SMALL, text_side=1)
    tubes1 = [h for h in d["holes"][0] if h[0] > X0]
    tubes2 = [h for h in d["holes"][1] if h[0] > X0]
    y0 = d["plates"][0]["y"]
    t1 = d["plates"][1]["y"]

    def rel(x):
        return f"X0 + {fmt(x - X0)}"
    items = [
        dict(anchor=P(head[2], (head[1] + head[3]) / 2), lines=[
            ("motor head", TEXT),
            (f"x {rel(head[0])} to {rel(head[2])}, y {fmt(head[1])} to {fmt(head[3])} (flange)", CON),
            (f"{len(d['head_lines'])} fine lines at y = " + ", ".join(fmt(y) for y in d["head_lines"]), CON)]),
        dict(anchor=P(cap[2], (cap[1] + cap[3]) / 2), lines=[
            (f"cap {fmt(cap[2] - cap[0])} x {fmt(cap[3] - cap[1])}: x {rel(cap[0])} to {rel(cap[2])}", CON)]),
        dict(anchor=P(tubes1[1][1], (y0 + st1[2]) / 2 + 12), lines=[
            ("stage 1: regenerator and pulse tube", TEXT),
            (", ".join(f"x {rel(a)} to {rel(b)}" for a, b in tubes1), CON),
            (f"from the flange y = {fmt(y0)} to the station", CON)]),
        dict(anchor=P(st1[3], (st1[2] + st1[4]) / 2), lines=[
            ("heat station 1, hatched '\\'", TEXT),
            (f"x {rel(st1[1])} to {rel(st1[3])}, y t1 - {fmt(t1 - st1[2])} to t1 = {fmt(t1)}", CON)]),
        dict(anchor=P(tubes2[1][1], (t1 + st2[2]) / 2 + 12), lines=[
            ("stage 2 tubes", TEXT),
            (", ".join(f"x {rel(a)} to {rel(b)}" for a, b in tubes2), CON)]),
        dict(anchor=P(st2[3], (st2[2] + st2[4]) / 2), lines=[
            ("heat station 2, hatched '/'", TEXT),
            (f"x {rel(st2[1])} to {rel(st2[3])}, y t2 - {fmt(d['plates'][2]['y'] - st2[2])} to t2 = "
             f"{fmt(d['plates'][2]['y'])}", CON)]),
    ]
    sh.column(items, "right", R + 70, T, B, size=SMALL, knee_x=R + 2, avoid=v.label_bands(20))


def detail_hatch(sh, ctx, d, left, top):
    """Detail B: the section hatching of the left ends of plates 0, 1 and 2."""
    mod = ctx.mod
    pl = d["plates"]
    S = 2.4
    x0 = mod.X0 - pl[0]["hw"] - 4
    win = (x0, pl[0]["y"] - 10, x0 + 90, pl[2]["b"] + 6)
    sh.details["B"] = win
    sh.view_title(f"Detail B: section hatching, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(5, 10, 20)
    v.mark()
    P = v.P
    step = d["step"]
    xm = (win[0] + win[2]) / 2
    items = []
    def inside(k, kq):
        """Line kq of plate k lies wholly inside both the plate and the window, 4 units in."""
        p = pl[k]
        c = kq * step
        xs = [(c - y) if d["hatch"][k]["slope"] > 0 else (c + y) for y in (p["y"], p["b"])]
        return min(xs) >= max(mod.X0 - p["hw"], win[0]) + 4 and max(xs) <= win[2] - 4

    for k in (0, 1, 2):
        p = pl[k]
        slope = d["hatch"][k]["slope"]
        ymid = (p["y"] + p["b"]) / 2
        fam = d["hatch"][k]
        ok = [kq for kq in range(fam["kmin"], fam["kmax"] + 1) if inside(k, kq) and (k or inside(k, kq + 1))]
        kk = min(ok, key=lambda kq: abs(kq * step - ((xm + ymid) if slope > 0 else (xm - ymid))))
        for kq in ((kk, kk + 1) if k == 0 else (kk,)):
            c = kq * step
            seg = [((c - y) if slope > 0 else (c + y), y) for y in (p["y"], p["b"])]
            for piece in mod.clip_polyline(seg, ("rect", mod.X0 - p["hw"], p["y"], mod.X0 + p["hw"], p["b"])):
                sh.line(v.Ps(piece), 1.8, CON, L_GUIDE)
        c = kk * step
        rel = "x + y" if slope > 0 else "x - y"
        a = ((c - p["y"]) if slope > 0 else (c + p["y"]), p["y"])
        items.append(dict(anchor=P(a), lines=[(f"plate {k}: {rel} = c", TEXT),
                                              (f"c = {kk} * {fmt(step, 4)} = {fmt(c, 3)}", CON)]))
        if k == 0:
            # x step of consecutive lines along the plate's bottom edge, and their perpendicular spacing
            yb = p["b"]
            xa_, xb_ = c - yb, (kk + 1) * step - yb
            sh.dim(P(xa_, yb + 4), P(xb_, yb + 4), f"{fmt(step, 3)} = {fmt(mod.HATCH)} * sqrt(2)", offset=0,
                   ext=(P(xa_, yb), P(xb_, yb)), size=SMALL, text_side=-1, inside=False)
            q0 = (c - ymid + 1.5, ymid - 1.5)
            q1 = (q0[0] + mod.HATCH / math.sqrt(2), q0[1] + mod.HATCH / math.sqrt(2))
            sh.dim(P(q0), P(q1), None, offset=0, inside=False)
            items.append(dict(anchor=P((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2),
                              lines=[(f"spacing HATCH = {fmt(mod.HATCH)}, at {fmt(d['hatch_angle'])} deg",
                                      TEXT)]))
    sh.column(items, "right", v.px[2] + 40, top, v.px[3])
    fam = d["hatch"]
    bs = chr(92)
    notes = [
        (f"Lines at {fmt(d['hatch_angle'])} deg, globally registered:", TEXT),
        (f"'/' : x + y = c    '{bs}' : x - y = c", CON),
        (f"c = k * HATCH * sqrt(2) = k * {fmt(step, 4)}, k integer", CON),
        ("one grid for every part, so lines of two '/' parts", TEXT),
        ("would meet if continued across the gap.", TEXT),
        ("k runs from ceil(lo / step) to floor(hi / step):", TEXT),
        ("'/': lo = x0 + y0, hi = x1 + y1", CON),
        (f"'{bs}': lo = x0 - y1, hi = x1 - y0", CON),
        ("Plates alternate (measured): " + ", ".join(
            f"{k} {'/' if f['slope'] > 0 else bs}" for k, f in enumerate(fam)), CON),
        (f"Lines stop {fmt(d['hatch_clear'])} short of every bore.", TEXT),
    ]
    sh.block(notes, left, v.px[3] + 24, SMALL)


# ---------------------------------------------------------------- sheet 3: the dial
def angle_of(c, p):
    return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))


def dial_data(ctx):
    """The dial's numbers, measured on hero_art()'s ticks, knurl, index and datum."""
    mod, h = ctx.mod, ctx.hero
    C = mod.C
    d = dict(C=C, R_OUT=mod.R_OUT, R_IN=mod.R_IN, R_BASE=mod.R_BASE, BAND=mod.BAND)
    if not near(mod.R_IN, mod.R_OUT - mod.BAND):
        raise RuntimeError("R_IN is no longer R_OUT - BAND")

    def radii(lines, end):
        return {round(math.dist(C, ln[end]), 6) for ln in lines}

    def angles(lines):
        return sorted(round(angle_of(C, ln[0]) % 360, 6) for ln in lines)
    tm, tf, kn = h["ticks_m"], h["ticks_f"], h["knurl"]
    if radii(tm, 0) != {mod.R_BASE} or radii(tf, 0) != {mod.R_BASE} or len(radii(tm, 1)) != 1 or \
            len(radii(tf, 1)) != 1:
        raise RuntimeError("graduations no longer hang from R_BASE with two lengths")
    d["major_len"] = mod.R_BASE - radii(tm, 1).pop()
    d["minor_len"] = mod.R_BASE - radii(tf, 1).pop()
    am, af = angles(tm), angles(tf)
    allang = sorted(am + af)
    step = min(b - a for a, b in zip(allang, allang[1:]))
    d["step"] = round(step, 6)
    d["count"] = round(360 / step)
    d["index"] = h["index"]
    apex = max(d["index"], key=lambda q: q[1])
    d["start"] = round(angle_of(C, apex), 6)
    major = min(b - a for a, b in zip(am, am[1:]))
    d["major_every"] = round(major / step)
    d["clear"] = src_numbers(mod.hero_art, "% 360) - 180) <")[-1]
    want, skipped = [], []
    for k in range(d["count"]):
        deg = d["start"] + d["step"] * k
        if abs(((deg - d["start"] + 180) % 360) - 180) < d["clear"]:
            skipped.append((k, deg))
        else:
            want.append(round(deg % 360, 6))
    if sorted(want) != allang:
        raise RuntimeError("the graduations no longer follow -90 + 3k with the index clearance")
    d["skipped"] = skipped
    d["n_major"], d["n_minor"] = len(tm), len(tf)
    # knurl
    if len(radii(kn, 0)) != 1 or len(radii(kn, 1)) != 1:
        raise RuntimeError("knurl marks no longer share two radii")
    d["knurl_r"] = (radii(kn, 0).pop(), radii(kn, 1).pop())
    ak = angles(kn)
    kstep = min(b - a for a, b in zip(ak, ak[1:]))
    d["knurl_step"], d["knurl_count"] = round(kstep, 6), round(360 / kstep)
    lo, hi = src_numbers(mod.hero_art, "<= deg <=")
    gap = [round(kstep * m, 6) for m in range(d["knurl_count"]) if lo <= kstep * m <= hi]
    if sorted(set(round(kstep * m, 6) for m in range(d["knurl_count"])) - set(ak)) != gap:
        raise RuntimeError("the knurl gap is no longer the source's angle range")
    d["knurl_gap"], d["knurl_missing"], d["knurl_drawn"] = (lo, hi), len(gap), len(ak)
    # index triangle and datum
    base = [q for q in d["index"] if q is not apex]
    d["apex"], d["base"] = apex, sorted(base)
    d["apex_in"] = mod.R_BASE - math.dist(C, apex)
    d["index_half"] = (d["base"][1][0] - d["base"][0][0]) / 2
    d["index_lift"] = d["base"][0][1] - (C[1] - mod.R_BASE)
    d["R_DAT"] = h["R_DAT"]
    quads = []
    for poly in h["datum"]:
        ring = [q for q in poly if math.dist(q, C) > 1e-9]
        a = sorted(round(angle_of(C, q), 6) for q in ring)
        quads.append((a[0], a[-1], round(min(y - x for x, y in zip(a, a[1:])), 6)))
    d["quads"] = quads
    # centre lines (ends from the source lines that draw them)
    d["vline"] = src_numbers(mod.hero_art, "centre_line((X0,")
    d["hline"] = src_numbers(mod.hero_art, "centre_line((cx - R_BASE")
    return d


def sheet_dial(ctx):
    mod = ctx.mod
    d = dial_data(ctx)
    C, cx, cy = mod.C, mod.C[0], mod.C[1]
    W, H = 2200, 2420
    sh = Sheet(ctx, 3, "construction-3-dial", "dial", W, H,
               "The calibration dial: radii, graduations, knurl, index, datum and centre lines.")
    sh.header("Construction sheet 3 of 5: the calibration dial",
              "A graduated ring under the coldest plate; its centre C is the datum. Angles in degrees, y down.")
    S = 2.2
    r = mod.R_OUT + 32
    v = View(sh, (cx - r, cy - r, cx + r, cy + r), 520, 180, S)
    v.grid(10, 50, 50)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    c = P(C)
    pol = lambda rr, a: P(mod.polar(C, rr, a))   # noqa: E731

    # angle arcs: 15 deg between two majors, 3 deg between a major and the next minor
    a0 = d["start"] + d["step"] * d["major_every"] * 8
    a1 = a0 + d["step"] * d["major_every"]
    a2 = a1 + d["step"]
    r15, r3 = mod.R_OUT + 22, mod.R_OUT + 22
    for a in (a0, a1, a2):
        sh.line([pol(mod.R_BASE - d["major_len"], a), pol(r15 + 8, a)], W_EXT, CON, L_GUIDE, dash=[5.0, 3.0])
    sh.angle(c, r15 * S, a0, a1, f"{fmt(a1 - a0)} deg", size=BODY, label_r=r15 * S + 14)
    sh.angle(c, r3 * S, a1, a2, None)
    m3 = math.radians(a2 + 1)
    p3 = (c[0] + (r3 * S) * math.cos(m3), c[1] + (r3 * S) * math.sin(m3))
    sh.leader(p3, (p3[0] + 60, p3[1] + 40), "right", dot=False)
    sh.text(f"{fmt(d['step'])} deg", p3[0] + 66, p3[1] + 45, BODY, CON)

    left, right = [], []
    kr = d["knurl_r"]
    right.append(dict(anchor=pol(mod.R_BASE - d["major_len"] / 2, -30), lines=[
        (f"{d['count']} graduations, theta_k = {fmt(d['start'])} + {fmt(d['step'])} k deg", CON),
        (f"from r = R_BASE inward; k % {d['major_every']} == 0: major", CON),
        (f"major: every {fmt(d['step'] * d['major_every'])} deg, length {fmt(d['major_len'])}, medium", CON),
        (f"minor: length {fmt(d['minor_len'])}, fine", CON)]))
    right.append(dict(anchor=P(d["base"][1]), lines=[
        ("index triangle on the axis (detail F)", TEXT),
        (f"no graduation within {fmt(d['clear'])} deg of it:", TEXT),
        ("k = " + ", ".join(str(k) for k, _ in d["skipped"]) + " omitted", CON),
        (f"drawn: {d['n_major']} majors + {d['n_minor']} minors = {d['n_major'] + d['n_minor']}", CON)]))
    right.append(dict(anchor=pol(mod.R_OUT, -60), lines=[
        ("band: solid annulus, R_IN to R_OUT", TEXT),
        (f"R_OUT = {fmt(mod.R_OUT)}, R_IN = R_OUT - BAND = {fmt(mod.R_IN)}", CON)]))
    right.append(dict(anchor=pol(mod.R_BASE, 15), lines=[
        (f"baseline: fine circle R_BASE = {fmt(mod.R_BASE)}", CON)]))
    right.append(dict(anchor=P(cx, cy + mod.R_OUT + d["vline"][1] - 6), lines=[
        ("vertical centre line = the axis x = X0", TEXT),
        (f"y from {fmt(d['vline'][0])} to C.y + R_OUT + {fmt(d['vline'][1])} = "
         f"{fmt(cy + mod.R_OUT + d['vline'][1])}", CON)]))
    left.append(dict(anchor=pol((kr[0] + kr[1]) / 2, 160), lines=[
        (f"knurl: {d['knurl_count']} marks every {fmt(d['knurl_step'])} deg", TEXT),
        (f"r from R_OUT + {fmt(kr[0] - mod.R_OUT)} to R_OUT + {fmt(kr[1] - mod.R_OUT)}", CON)]))
    gl, gh = d["knurl_gap"]
    left.append(dict(anchor=pol((kr[0] + kr[1]) / 2, gl + (gh - gl) / 4), lines=[
        (f"knurl omitted for {fmt(gl)} <= phi <= {fmt(gh)} deg:", TEXT),
        (f"{d['knurl_missing']} marks; {d['knurl_drawn']} drawn. Centred on {fmt((gl + gh) / 2)} deg,", CON),
        ("straight up in y-down: the cold finger enters", CON)]))
    hl = d["hline"]
    left.append(dict(anchor=P(cx - mod.R_BASE + hl[0], cy), lines=[
        ("horizontal centre line through C", TEXT),
        (f"x from C.x - R_BASE + {fmt(hl[0])} = {fmt(cx - mod.R_BASE + hl[0])} to "
         f"{fmt(cx + mod.R_BASE - hl[1])}", CON),
        ("cut around the chip and the brackets", CON)]))
    left.append(dict(anchor=c, lines=[
        (f"C = {pt(C, 1)}: the datum (detail G)", CON)]))
    left.append(dict(anchor=pol(mod.R_OUT - mod.BAND / 2, 140), lines=[
        (f"BAND = {fmt(mod.BAND)}: a solid fill,", CON), ("heavier than any stroke", TEXT)]))
    bands = v.label_bands(50)
    sh.column(left, "left", L - 92, T, B, knee_x=L - 2, avoid=bands)
    sh.column(right, "right", R + 92, T, B, knee_x=R + 2, avoid=bands)
    sh.view_title(f"Main view, scale {fmt(S)}", L, T - 34)

    row2 = B + 90
    detail_index(sh, ctx, d, 330, row2)
    sh.title_block(W - MARGIN - 620, row2 - 30, 620, f"main view 1 unit = {fmt(S)} px; details as marked")
    row3 = row2 + 440
    detail_radial(sh, ctx, d, 100, row3)
    detail_datum(sh, ctx, d, 1250, row3)
    convention(sh, 700, row3 + 250)
    v.detail_marks(sh.details)
    sh.frame()
    sh.finish()


def convention(sh, left, top):
    """The y-down angle convention: 0 deg along +x, 90 deg along +y (down), clockwise on screen."""
    ox, oy, rr = left + 190, top + 150, 92
    sh.view_title("Angles, y down", left, top)
    sh.line([(ox - rr - 20, oy), (ox + rr + 20, oy)], 1.0, TEXT)
    sh.line([(ox, oy - rr - 20), (ox, oy + rr + 20)], 1.0, TEXT)
    sh.arrowhead((ox + rr + 26, oy), (ox, oy), colour=TEXT)
    sh.arrowhead((ox, oy + rr + 26), (ox, oy), colour=TEXT)
    sh.text("+x", ox + rr + 30, oy + 18, SMALL, TEXT)
    sh.text("+y", ox + 10, oy + rr + 34, SMALL, TEXT)
    sh.circle((ox, oy), rr * 0.62, 1.2, a0=8, a1=82)
    sh.arrowhead((ox + rr * 0.62 * math.cos(math.radians(84)), oy + rr * 0.62 * math.sin(math.radians(84))),
                 (ox + rr * 0.62 * math.cos(math.radians(78)), oy + rr * 0.62 * math.sin(math.radians(78))))
    for a, lab, dx, dy, anc in ((0, "0", 8, -8, "start"), (90, "90", -8, 0, "end"), (180, "180", -8, -8, "end"),
                                (270, "270 = -90", 8, 4, "start")):
        q = (ox + rr * math.cos(math.radians(a)), oy + rr * math.sin(math.radians(a)))
        sh.dot(q, 3.0)
        sh.text(lab, q[0] + dx, q[1] + dy, SMALL, CON, anchor=anc, pad=True)
    sh.text("polar(C, r, theta) = (C.x + r cos theta,", left, oy + rr + 70, SMALL, CON)
    sh.text("                     C.y + r sin theta)", left, oy + rr + 90, SMALL, CON)
    sh.text("theta grows clockwise on screen", left, oy + rr + 110, SMALL, TEXT)


def detail_index(sh, ctx, d, left, top):
    """Detail F: the index triangle and the graduations it keeps clear."""
    mod = ctx.mod
    C = mod.C
    S = 5.5
    ap = d["apex"]
    win = (C[0] - 62, C[1] - mod.R_OUT - 2, C[0] + 62, ap[1] + 10)
    sh.details["F"] = win
    sh.view_title(f"Detail F: the index and its clearance, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(2, 10, 10)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    pol = lambda rr, a: P(mod.polar(C, rr, a))   # noqa: E731
    for k, deg in d["skipped"]:
        ln = d["major_len"] if k % d["major_every"] == 0 else d["minor_len"]
        sh.line([pol(mod.R_BASE, deg), pol(mod.R_BASE - ln, deg)], 1.4, CON, L_GUIDE, dash=[4.0, 3.0])
    for a in (d["start"] - d["clear"], d["start"] + d["clear"]):
        sh.line([pol(mod.R_BASE - 30, a), pol(mod.R_BASE + 4, a)], W_EXT, CON, L_GUIDE, dash=[6.0, 3.0])
    sh.angle(P(C), (mod.R_BASE - 27) * S, d["start"], d["start"] + d["clear"], f"{fmt(d['clear'])} deg",
             size=SMALL, label_r=(mod.R_BASE - 27) * S - 4)
    tri = d["index"]
    for q in tri:
        sh.square(P(q), 3.5)
    items = [
        dict(anchor=P(ap), lines=[(f"apex = polar(C, R_BASE - {fmt(d['apex_in'])}, {fmt(d['start'])})", TEXT),
                                  (f"= {pt(ap)}", CON)]),
        dict(anchor=P(d["base"][1]), lines=[(f"(C.x + {fmt(d['index_half'])}, C.y - R_BASE + {fmt(d['index_lift'])})",
                                             TEXT), (f"= {pt(d['base'][1])}", CON)]),
    ]
    sh.column(items, "right", R + 60, T, B, size=SMALL, knee_x=R + 2)
    it2 = [dict(anchor=P(d["base"][0]), lines=[(f"(C.x - {fmt(d['index_half'])}, C.y - R_BASE + "
                                                f"{fmt(d['index_lift'])})", TEXT), (f"= {pt(d['base'][0])}", CON)])]
    sh.column(it2, "left", L - 60, T, B, size=SMALL, knee_x=L - 2)
    lines = [
        (f"Graduation k is skipped when |((theta_k - ({fmt(d['start'])}) + 180) mod 360) - 180| < "
         f"{fmt(d['clear'])}:", TEXT),
        (f"its angle from the index (theta = {fmt(d['start'])}) is under {fmt(d['clear'])} deg. Dashed: the "
         f"{len(d['skipped'])} it removes,", TEXT),
        (", ".join(f"k = {k} at {fmt(deg)} deg" for k, deg in d["skipped"]) +
         f"; the next ones stand at {fmt(d['start'])} +/- {fmt(2 * d['step'])} deg.", CON),
    ]
    sh.block(lines, left, B + 26, SMALL)


def detail_datum(sh, ctx, d, left, top):
    """Detail G: the datum symbol at C and the phase of the centre lines crossing it."""
    mod = ctx.mod
    C = mod.C
    S = 13.0
    rd = d["R_DAT"]
    win = (C[0] - 16, C[1] - 16, C[0] + 12, C[1] + 16)
    sh.details["G"] = win
    sh.view_title(f"Detail G: the datum at C, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(1, 5, 5)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    c = P(C)
    sh.circle(c, rd * S, 1.2, CON, L_GUIDE, dash=[6.0, 4.0])
    off = mod.CENTRE[0] + mod.CENTRE[1] + mod.CENTRE[2] / 2
    items = [
        dict(anchor=P(mod.polar(C, rd, 225)), lines=[(f"circle R_DAT = {fmt(rd)}, fine", CON)]),
        dict(anchor=P(mod.polar(C, rd * 0.6, -45)), lines=[
            (f"filled: theta {fmt(d['quads'][0][0])} to {fmt(d['quads'][0][1])} deg", CON),
            (f"(sampled every {fmt(d['quads'][0][2])} deg, plus C)", TEXT)]),
        dict(anchor=P(mod.polar(C, rd * 0.6, 135)), lines=[
            (f"filled: theta {fmt(d['quads'][1][0])} to {fmt(d['quads'][1][1])} deg", CON)]),
        dict(anchor=P(C[0], C[1] - mod.CENTRE[2] / 2), lines=[
            (f"short dash {fmt(mod.CENTRE[2])}, centred on C:", TEXT),
            ("dashes start at C, pattern offset", TEXT),
            (f"{fmt(mod.CENTRE[0])} + {fmt(mod.CENTRE[1])} + {fmt(mod.CENTRE[2])}/2 = {fmt(off)}", CON)]),
    ]
    sh.dim(P(C[0] + 3, C[1] - mod.CENTRE[2] / 2), P(C[0] + 3, C[1] + mod.CENTRE[2] / 2),
           fmt(mod.CENTRE[2]), offset=0, ext=(P(C[0] + 0.8, C[1] - mod.CENTRE[2] / 2),
                                               P(C[0] + 0.8, C[1] + mod.CENTRE[2] / 2)), size=SMALL, inside=False)
    sh.column(items, "right", R + 60, T, B, size=SMALL, knee_x=R + 2)


def detail_radial(sh, ctx, d, left, top):
    """Detail E: a radial section of the ring at theta = 0, every radius as an ordinate."""
    mod = ctx.mod
    C = mod.C
    S = 9.0
    kr = d["knurl_r"]
    r0 = mod.R_BASE - d["major_len"] - 6
    win = (C[0] + r0, C[1] - 13, C[0] + kr[1] + 5, C[1] + 13)
    sh.details["E"] = win
    sh.view_title(f"Detail E: radial section at theta = 0, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top + 60, S)
    v.grid(1, 5, None)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    stops = [(mod.R_BASE - d["major_len"], f"R_BASE - {fmt(d['major_len'])}", "major tick inner end"),
             (mod.R_BASE - d["minor_len"], f"R_BASE - {fmt(d['minor_len'])}", "minor tick inner end"),
             (mod.R_BASE, "R_BASE", "baseline, ticks start"),
             (mod.R_IN, "R_IN = R_OUT - BAND", "band inner edge"),
             (mod.R_OUT, "R_OUT", "band outer edge"),
             (kr[0], f"R_OUT + {fmt(kr[0] - mod.R_OUT)}", "knurl inner end"),
             (kr[1], f"R_OUT + {fmt(kr[1] - mod.R_OUT)}", "knurl outer end")]
    for rr, _, _ in stops:
        x = P(C[0] + rr, C[1])[0]
        sh.line([(x, T - 30), (x, B + 4)], W_EXT, CON, L_GUIDE)
        sh.text(fmt(rr), x, T - 36, SMALL, CON, anchor="middle")
    sh.text("r =", L - 10, T - 36, SMALL, TEXT, anchor="end")
    lines = [("Every radius of the ring, measured from C along theta = 0:", TEXT)]
    for rr, name, what in stops:
        lines.append((f"{fmt(rr):>4} = {name:<20} {what}", CON))
    lines.append((f"band {fmt(mod.BAND)} = R_OUT - R_IN; ticks at 0 and +/-{fmt(d['step'])} deg, knurl at 0, "
                  f"+/-{fmt(d['knurl_step'])}", TEXT))
    sh.block(lines, R + 50, top, SMALL)


# ---------------------------------------------------------------- sheet 4: chip, drift, interval
def arrow_shape(poly):
    """Tip, base midpoint, length and half-width of a triangle made by mark.arrow()."""
    tip = max(poly, key=lambda q: min(math.dist(q, r) for r in poly if r is not q))
    rest = [q for q in poly if q is not tip]
    bm = ((rest[0][0] + rest[1][0]) / 2, (rest[0][1] + rest[1][1]) / 2)
    ln = math.dist(tip, bm)
    u = ((tip[0] - bm[0]) / ln, (tip[1] - bm[1]) / ln)
    n = (-u[1], u[0])
    rest.sort(key=lambda q: -((q[0] - bm[0]) * n[0] + (q[1] - bm[1]) * n[1]))   # B + half n first
    return tip, bm, ln, math.dist(rest[0], rest[1]) / 2, rest


def interval_data(ctx):
    """The chip positions, drift curve, brackets and dimensions, from hero_art()'s locals."""
    mod, h = ctx.mod, ctx.hero
    d = {k: h[k] for k in ("now", "past", "allc", "left", "right", "top", "bot", "brL", "brR", "trail", "pieces",
                           "dots", "range_dims", "drift_dims", "range_arrows", "drift_arrows", "trail_arrow",
                           "yd", "xl", "xr", "yu", "chip_keep", "past_keep")}
    half = mod.CHIP / 2
    if not near(h["h"], half):
        raise RuntimeError("the chip half-size is no longer CHIP / 2")
    xs, ys = [q[0] for q in d["allc"]], [q[1] for q in d["allc"]]
    d["trim_top"] = d["top"] - (min(ys) - half - mod.BR_PAD - mod.BR_T)
    d["trim_bot"] = (max(ys) + half + mod.BR_PAD + mod.BR_T) - d["bot"]
    if not near(d["left"], min(xs) - half - mod.BR_PAD) or not near(d["right"], max(xs) + half + mod.BR_PAD):
        raise RuntimeError("bracket sides no longer follow min/max x -/+ (s/2 + pad)")
    d["range_off"] = d["yd"] - d["bot"]
    d["drift_off"] = d["top"] - d["yu"]
    ext = d["range_dims"][0]
    d["ext_gap"], d["ext_over"] = ext[0][1] - d["bot"], ext[1][1] - d["yd"]
    d["line_inset"] = d["range_dims"][2][0][0] - d["xl"]
    de = d["drift_dims"][0]
    d["drift_ext_gap"] = (d["now"][1] - half) - de[0][1]
    d["drift_ext_over"] = d["yu"] - de[1][1]
    d["arrows"] = [arrow_shape(a) for a in d["range_arrows"] + d["drift_arrows"]]
    d["trail_head"] = arrow_shape(d["trail_arrow"][0])
    d["ctrl"] = bezier_controls(mod, d["trail"])
    ck, pk = d["chip_keep"], d["past_keep"]
    d["keep"] = (d["now"][0] - half) - ck[1]
    if not near(d["keep"], (d["past"][0][0] - half) - pk[1]):
        raise RuntimeError("the two chip keep-outs no longer share one margin")
    redo = []
    for pl in d["pieces"]:
        redo += mod.dash(pl, mod.HIDDEN, 0)
    if redo != d["dots"]:
        raise RuntimeError("the drift dots no longer use the HIDDEN lengths")
    d["phantom_offset"] = src_numbers(mod.hero_art, "dash(sq, PHANTOM,")[0]
    pc = d["past"][0]
    marks = [pl for pl in h["fine"] if len(pl) == 2 and near((pl[0][0] + pl[1][0]) / 2, pc[0])
             and near((pl[0][1] + pl[1][1]) / 2, pc[1])]
    d["past_mark"] = max(math.dist(*pl) for pl in marks) / 2
    # chip lattice, measured on chip_fill() at unit size
    polys = mod.chip_fill(0.0, 0.0, 1.0)
    die, hole, core, plus, cpl = polys[0], polys[1], polys[2], polys[3], polys[4]
    pb = bbox(plus)
    pcx = (pb[0] + pb[2]) / 2
    d["lat"] = dict(g0=bbox(hole)[0] + 0.5, g1=bbox(core)[0] + 0.5, sp=-pcx, arm=(pb[2] - pb[0]) / 2,
                    aw=min(abs(q[0] - pcx) for q in plus if near(q[1], pb[1])),
                    cw=(bbox(cpl)[3] - bbox(cpl)[1]) / 2,
                    wind=[1 if mod.area(q) > 0 else -1 for q in (die, hole, core, plus, cpl)],
                    n=len(polys))
    sp = d["lat"]["sp"]
    centres = [((bbox(q)[0] + bbox(q)[2]) / 2, (bbox(q)[1] + bbox(q)[3]) / 2) for q in polys if len(q) == len(plus)]
    d["lat"]["idx"] = sorted({round(c[0] / sp) for c in centres})
    d["lat"]["rows"] = sorted({round(c[1] / sp) for c in centres})
    return d


def sheet_interval(ctx):
    mod = ctx.mod
    d = interval_data(ctx)
    C, cx, cy = mod.C, mod.C[0], mod.C[1]
    s_, half, pad, t, a = mod.CHIP, mod.CHIP / 2, mod.BR_PAD, mod.BR_T, mod.BR_ARM
    now, past = d["now"], d["past"][0]
    W, H = 2200, 1880
    sh = Sheet(ctx, 4, "construction-4-interval", "chip, drift and interval", W, H,
               "The chip and its lattice, the drift curve, the brackets and the two dimensions, with equations.")
    sh.header("Construction sheet 4 of 5: the chip, its drift and the interval",
              "Inside the dial: where the chip is now, where it was, and the range drawn around both. Design units, "
              "y down.")
    S = 3.2
    win = (d["left"] - t - 26, d["top"] - 46, d["right"] + t + 26, d["yd"] + 30)
    v = View(sh, win, 560, 180, S)
    v.grid(5, 50, 50)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    # centres
    for q in (now, past, C):
        c = P(q)
        sh.line([(c[0] - 9, c[1]), (c[0] + 9, c[1])], 1.3)
        sh.line([(c[0], c[1] - 9), (c[0], c[1] + 9)], 1.3)
    # the past offset, mirrored above the mark's own drift dimension
    yp = d["yu"] - 12
    sh.dim(P(past[0], yp), P(cx, yp), fmt(cx - past[0]), offset=0,
           ext=(P(past[0], past[1] - half - 4), None), size=BODY)
    sh.line([P(past[0], past[1] - 10), P(past[0], past[1] - half)], W_EXT, CON, L_GUIDE, dash=[5.0, 3.0])
    sh.dim(P(cx, d["yu"] + 8), P(now[0], d["yu"] + 8), fmt(now[0] - cx), offset=0, size=BODY, text_side=-1)
    # drift curve: control polygon and points
    cp = d["ctrl"]
    sh.line(v.Ps(cp), 1.1, CON, L_GUIDE, dash=[6.0, 4.0])
    sh.line(v.Ps(mod.bezier(*cp, 60)), 1.0, CON, L_GUIDE)
    sh.text("P0", P(cp[0])[0] - 12, P(cp[0])[1] + 22, BODY, CON, anchor="end", pad=True)
    for name, q, dx, dy, anc in (("P1", cp[1], -10, 16, "end"), ("P2", cp[2], 10, 18, "start")):
        sh.square(P(q), 4.0, w=1.4)
        sh.text(name, P(q)[0] + dx, P(q)[1] + dy, BODY, CON, anchor=anc, pad=True)
    # bracket dimensions on the right bracket
    sh.dim(P(d["right"], cy + 34), P(d["right"] + t, cy + 34), f"t = {fmt(t)}", offset=0, size=SMALL,
           inside=False, along=2.6)
    sh.dim(P(now[0] + half, cy - 28), P(d["right"], cy - 28), fmt(pad), offset=0, size=SMALL,
           ext=(P(now[0] + half, now[1] - half + 30), None))
    sh.dim(P(d["right"] + t - a, d["top"] - 9), P(d["right"] + t, d["top"] - 9), f"a = {fmt(a)}", offset=0,
           ext=(P(d["right"] + t - a, d["top"]), P(d["right"] + t, d["top"])), size=SMALL)
    xh = d["left"] - t - 12
    sh.dim(P(xh, d["top"]), P(xh, d["bot"]), fmt(d["bot"] - d["top"]), offset=0,
           ext=(P(d["left"] - t, d["top"]), P(d["left"] - t, d["bot"])), size=SMALL, text_side=-1, along=0.3)
    yr = d["yd"] + 18
    sh.dim(P(d["xl"], yr), P(d["xr"], yr), f"{fmt(d['xr'] - d['xl'])} = xr - xl", offset=0,
           ext=(P(d["xl"], d["yd"] + d["ext_over"]), P(d["xr"], d["yd"] + d["ext_over"])), size=SMALL,
           text_side=-1, along=0.3)

    left_items, right_items = [], []
    right_items.append(dict(anchor=P(now[0] + half, now[1] - half + 12), lines=[
        ("chip now = C + CHIP_NOW", TEXT),
        (f"= ({fmt(cx)} + {fmt(mod.CHIP_NOW[0])}, {fmt(cy)} + ({fmt(mod.CHIP_NOW[1])})) = {pt(now)}", CON),
        (f"solid, {fmt(s_)} x {fmt(s_)} (detail H)", CON)]))
    right_items.append(dict(anchor=P(d["right"] + t, d["top"] + t / 2), lines=[
        ("top = min y - s/2 - pad - t + " + fmt(d["trim_top"]), TEXT),
        (f"= {fmt(min(q[1] for q in d['allc']))} - {fmt(half)} - {fmt(pad)} - {fmt(t)} + {fmt(d['trim_top'])} "
         f"= {fmt(d['top'])}", CON)]))
    right_items.append(dict(anchor=P(d["right"], cy + 8), lines=[
        ("right = max x + s/2 + pad", TEXT),
        (f"= {fmt(max(q[0] for q in d['allc']))} + {fmt(half)} + {fmt(pad)} = {fmt(d['right'])}", CON),
        (f"bar from right to right + t = {fmt(d['right'] + t)}", CON)]))
    right_items.append(dict(anchor=P(d["right"] + t, d["bot"] - t / 2), lines=[
        ("bottom = max y + s/2 + pad + t - " + fmt(d["trim_bot"]), TEXT),
        (f"= {fmt(max(q[1] for q in d['allc']))} + {fmt(half)} + {fmt(pad)} + {fmt(t)} - {fmt(d['trim_bot'])} "
         f"= {fmt(d['bot'])}", CON),
        (f"arms {fmt(a)} long, {fmt(t)} thick; solid fill (accent)", CON)]))
    right_items.append(dict(anchor=P(d["xr"], d["yd"] + d["ext_over"]), lines=[
        ("range dimension (accent)", TEXT),
        ("at yd = bottom + " + fmt(d["range_off"]) + f" = {fmt(d['yd'])}", CON),
        (f"from xl = left - t/2 = {fmt(d['xl'])} to xr = right + t/2 = {fmt(d['xr'])}", CON),
        (f"extensions from bottom + {fmt(d['ext_gap'])} to yd + {fmt(d['ext_over'])}", CON),
        (f"line stops {fmt(d['line_inset'])} short of each tip (detail I)", CON)]))
    left_items.append(dict(anchor=P(cx, d["yu"]), lines=[
        ("drift dimension (ink) at y = top - " + fmt(d["drift_off"]) + f" = {fmt(d['yu'])}", TEXT),
        (f"from C.x = {fmt(cx)} to now.x = {fmt(now[0])}; extension from", CON),
        (f"now.y - s/2 - {fmt(d['drift_ext_gap'])} to y - {fmt(d['drift_ext_over'])}", CON)]))
    left_items.append(dict(anchor=P(past[0] - half, past[1] - half + 14), lines=[
        ("earlier position past = C + CHIP_PAST[0]", TEXT),
        (f"= ({fmt(cx)} + ({fmt(mod.CHIP_PAST[0][0])}), {fmt(cy)} + {fmt(mod.CHIP_PAST[0][1])}) = {pt(past)}", CON),
        (f"phantom outline, PHANTOM pattern from offset {fmt(d['phantom_offset'])};", CON),
        (f"centre mark +/- {fmt(d['past_mark'])}", CON)]))
    left_items.append(dict(anchor=P(d["left"], cy + 8), lines=[
        ("left = min x - s/2 - pad", TEXT),
        (f"= {fmt(min(q[0] for q in d['allc']))} - {fmt(half)} - {fmt(pad)} = {fmt(d['left'])}", CON),
        (f"bar from left - t = {fmt(d['left'] - t)} to left", CON)]))
    left_items.append(dict(anchor=P(cp[1]), lines=[
        ("drift path: one cubic Bezier, past to now", TEXT),
        (f"P0 = past, P1 = P0 + {pt((cp[1][0] - cp[0][0], cp[1][1] - cp[0][1]))} = {pt(cp[1])}", CON),
        (f"P2 = now + {pt((cp[2][0] - cp[3][0], cp[2][1] - cp[3][1]))} = {pt(cp[2])}, P3 = now", CON),
        (f"dashed {fmt(mod.HIDDEN[0])} on, {fmt(mod.HIDDEN[1])} off (the HIDDEN lengths), stopping", CON),
        (f"{fmt(d['keep'])} short of both chips; arrowhead {fmt(d['trail_head'][2], 3)} long at the end", CON)]))
    sh.column(left_items, "left", L - 92, T, B, knee_x=L - 2, avoid=v.label_bands(50))
    sh.column(right_items, "right", R + 92, T, B, knee_x=R + 2, avoid=v.label_bands(50))
    sh.view_title(f"Main view, scale {fmt(S)}", L, T - 34)

    row2 = B + 100
    detail_chip(sh, ctx, d, 400, row2)
    detail_arrow(sh, ctx, d, 1500, row2)
    v.detail_marks(sh.details)
    centred = [
        ("The interval is centred on the datum.", TEXT, 17),
        (f"now.x - C.x = {fmt(now[0])} - {fmt(cx)} = {fmt(now[0] - cx)}", CON),
        (f"C.x - past.x = {fmt(cx)} - {fmt(past[0])} = {fmt(cx - past[0])}", CON),
        (f"so (left + right) / 2 = ({fmt(d['left'])} + {fmt(d['right'])}) / 2 = "
         f"{fmt((d['left'] + d['right']) / 2)} = C.x:", CON),
        ("the frozen snapshot sits mid-range, and the range", TEXT),
        ("is drawn around what the chip actually did.", TEXT),
    ]
    sh.block(centred, 1500, row2 + 330, BODY)
    sh.title_block(W - MARGIN - 620, H - MARGIN - 200, 620, f"main view 1 unit = {fmt(S)} px; details as marked")
    sh.frame()
    sh.finish()


def detail_chip(sh, ctx, d, left, top):
    """Detail H: the chip's lattice and the winding that knocks it out."""
    mod = ctx.mod
    now, s_ = d["now"], mod.CHIP
    half = s_ / 2
    S = 6.0
    win = (now[0] - half - 6, now[1] - half - 6, now[0] + half + 6, now[1] + half + 6)
    sh.details["H"] = win
    sh.view_title(f"Detail H: the chip lattice, s = CHIP = {fmt(s_)}, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(1, 10, 10)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    lat = d["lat"]
    g0, g1, sp, arm, aw, cw = (lat[k] * s_ for k in ("g0", "g1", "sp", "arm", "aw", "cw"))
    x0, y0 = now[0] - half, now[1] - half
    sh.dim(P(x0, y0 - 3), P(x0 + g0, y0 - 3), f"g0 = {fmt(g0, 3)}", offset=0, size=SMALL, inside=False, along=2.2,
           text_side=1)
    sh.dim(P(x0 - 3, y0), P(x0 - 3, y0 + g1), f"g1 = {fmt(g1, 3)}", offset=0, size=SMALL, inside=False,
           text_side=-1)
    sh.dim(P(now[0] - sp, now[1] + sp + arm + 4), P(now[0], now[1] + sp + arm + 4), f"sp = {fmt(sp, 3)}", offset=0,
           ext=(P(now[0] - sp, now[1] + sp + arm), P(now[0], now[1] + sp + arm)), size=SMALL, text_side=-1)
    qx, qy = now[0] + sp, now[1] - sp
    sh.dim(P(qx, qy - arm - 2.5), P(qx + arm, qy - arm - 2.5), f"arm {fmt(arm, 3)}", offset=0,
           ext=(P(qx, qy - aw), P(qx + arm, qy - aw)), size=SMALL, inside=False, along=1.9)
    wd, wh, wc, wq, _ = lat["wind"]

    def tally(*ws):
        total = sum(ws)
        return " ".join(f"{w:+d}" for w in ws) + (f" = {total:+d} (ink)" if total else " = 0 (empty)")
    items = [
        dict(anchor=P(x0 + g0 / 2, now[1] + 20), lines=[(f"die: {wd:+d} (ink)", CON)]),
        dict(anchor=P(x0 + (g0 + g1) / 2, now[1] + 30), lines=[("guard ring gap: " + tally(wd, wh), CON)]),
        dict(anchor=P(now[0] - sp / 2, now[1] + sp / 2), lines=[("core: " + tally(wd, wh, wc), CON)]),
        dict(anchor=P(now[0] - sp, now[1] + sp + arm * 0.6), lines=[("qubit: " + tally(wd, wh, wc, wq), CON)]),
    ]
    sh.column(items, "left", L - 50, T + 120, B, size=SMALL, knee_x=L - 2, avoid=v.label_bands(10))
    lines = [
        ("chip_fill(cx, cy, s): one compound shape,", TEXT),
        ("filled by the nonzero winding rule.", TEXT),
        (f"die: square of side s = {fmt(s_)}, wound {lat['wind'][0]:+d}", CON),
        (f"guard ring: hole at inset g0 = {fmt(lat['g0'], 4)} s = {fmt(g0, 3)}, {lat['wind'][1]:+d}", CON),
        (f"core: refilled at inset g1 = {fmt(lat['g1'], 4)} s = {fmt(g1, 3)}, {lat['wind'][2]:+d}", CON),
        (f"qubits: {len(lat['idx'])} x {len(lat['rows'])} crosses at C_chip + (i, j) sp,", CON),
        (f"  sp = {fmt(lat['sp'], 4)} s = {fmt(sp, 3)}, i, j in " + ", ".join(str(i) for i in lat["idx"]), CON),
        (f"  half-length arm = {fmt(lat['arm'], 4)} s = {fmt(arm, 3)}", CON),
        (f"  half-width aw = {fmt(lat['aw'], 4)} s = {fmt(aw, 3)}, wound {lat['wind'][3]:+d}", CON),
        ("couplers from x + arm to x + sp - arm,", CON),
        (f"  half-width cw = {fmt(lat['cw'], 4)} s = {fmt(cw, 3)}, wound {lat['wind'][4]:+d}", CON),
        ("Couplers abut the arms without overlap, so no", TEXT),
        ("region is wound twice the same way.", TEXT),
        (f"{lat['n']} polygons. Signs of area() measured on", TEXT),
        ("die, hole, core, qubit, coupler: " + " ".join(f"{w:+d}" for w in lat["wind"]), CON),
    ]
    sh.block(lines, R + 40, top, SMALL)


def detail_arrow(sh, ctx, d, left, top):
    """Detail I: the construction of an arrowhead (the range dimension's right tip)."""
    tip, bm, length, halfw, corners = d["arrows"][1]
    S = 12.0
    win = (tip[0] - length - 5, tip[1] - 7, tip[0] + 3, tip[1] + 7)
    sh.details["I"] = win
    sh.view_title(f"Detail I: an arrowhead, scale {fmt(S)}", left, top - 34)
    v = View(sh, win, left, top, S)
    v.grid(1, 5, 5)
    v.mark()
    P = v.P
    L, T, R, B = v.px
    for q in [tip, bm] + corners:
        sh.square(P(q), 3.2, w=1.3)
    sh.line([P(bm), P(tip)], 1.2, CON, L_GUIDE, dash=[5.0, 3.0])
    tl, tb, tll, thw, _ = d["trail_head"]
    items = [
        dict(anchor=P(tip), lines=[("tip T", TEXT), (f"= {pt(tip)}", CON)]),
        dict(anchor=P(corners[0]), lines=[(f"B + {fmt(halfw)} n", TEXT), (f"= {pt(corners[0])}", CON)]),
        dict(anchor=P(corners[1]), lines=[(f"B - {fmt(halfw)} n", TEXT), (f"= {pt(corners[1])}", CON)]),
        dict(anchor=P(bm), lines=[(f"B = T - {fmt(length)} u", TEXT), (f"= {pt(bm)}", CON)]),
    ]
    sh.column(items, "right", R + 40, T - 10, B + 40, size=SMALL, knee_x=R + 2)
    lines = [
        ("arrow(tip, toward, length, half):", TEXT),
        ("u = (T - toward) / |T - toward|, n = (-u_y, u_x)", CON),
        ("B = T - length u; corners B +/- half n", CON),
        (f"dimensions: length {fmt(length)}, half {fmt(halfw)}; drift path: "
         f"length {fmt(tll, 3)}, half {fmt(thw, 3)}", CON),
    ]
    sh.block(lines, left, B + 24, SMALL)


# ---------------------------------------------------------------- sheet 5: line types and small marks
def weight_census(mod):
    """Polylines per stroke weight and polygons filled, counted on the hero's Art."""
    out = {}
    for it in mod.art("hero").items:
        n = sum(len(pls) for _, pls in it[1])
        key = ("stroke", it[2]) if it[0] == "S" else ("fill", None)
        out[key] = out.get(key, 0) + n
    return out


def sheet_lines(ctx):
    mod = ctx.mod
    W, H = 2200, 1680
    sh = Sheet(ctx, 5, "construction-5-lines-and-small-marks", "line types and small marks", W, H,
               "The line-weight hierarchy and dash patterns at scale, and the two small marks on their grids.")
    sh.header("Construction sheet 5 of 5: line types and the small marks",
              "Left: every weight and dash pattern of the hero, drawn at scale. Right: the small marks on their "
              "unit grids.")
    census = weight_census(mod)
    dd = dial_data(ctx)
    k1024 = 1024 / ctx.U

    # ------------------------------------------------ weights
    S = 4.0
    x0, y = 60, 190
    sh.view_title(f"Line weights, scale {fmt(S)} (px per design unit)", x0, y - 30)
    rows = [("heavy", "W_HEAVY", mod.W_HEAVY, "stroke", "plate outlines in section, butt caps"),
            ("medium", "W_MED", mod.W_MED, "stroke",
             f"rods, tubes, coax, cold head, {fmt(dd['step'] * dd['major_every'])} deg ticks"),
            ("fine", "W_FINE", mod.W_FINE, "stroke", "hatching, centre, phantom, hidden, dimension lines"),
            ("band", "BAND", mod.BAND, "fill", "the dial's solid ring, R_OUT - R_IN"),
            ("bracket", "BR_T", mod.BR_T, "fill", "the bracket bars and arms (accent)")]
    bar = 220
    for name, const, w, kind, what in rows:
        hpx = w * S
        cy_ = y + max(hpx, 16) / 2
        colour = MARK_ACCENT if const == "BR_T" else MARK_INK
        sh.fill(L_MARK, colour, [[(x0, cy_ - hpx / 2), (x0 + bar, cy_ - hpx / 2), (x0 + bar, cy_ + hpx / 2),
                                  (x0, cy_ + hpx / 2)]])
        sh.dim((x0 + bar + 16, cy_ - hpx / 2), (x0 + bar + 16, cy_ + hpx / 2), None, offset=0, inside=False,
               ext=((x0 + bar, cy_ - hpx / 2), (x0 + bar, cy_ + hpx / 2)), tail=12)
        n = census.get(("stroke", w)) if kind == "stroke" else None
        sh.text(f"{name}  {const} = {fmt(w)}", x0 + bar + 44, cy_ - 4, BODY, CON)
        sh.text(what + (f"; {n} polylines" if n else ""), x0 + bar + 44, cy_ + 15, SMALL, TEXT)
        sh.text(f"{fmt(w * k1024, 2)} px at 1024", x0 + bar + 44 + 540, cy_ - 4, SMALL, TEXT)
        y += max(hpx, 16) + 42
    fills = census.get(("fill", None), 0)
    sh.text(f"Strokes have round caps and joins unless noted; {fills} filled polygons sit above them.", x0, y + 4,
            SMALL, TEXT)

    # ------------------------------------------------ dash patterns
    S2 = 7.0
    y += 70
    sh.view_title(f"Dash patterns, scale {fmt(S2)}, drawn by mark.dash() at the fine weight", x0, y - 30)
    hid_off = src_numbers(mod.hero_art, "hidden += dash(pl, HIDDEN,")[0]
    lit = src_numbers(mod.hero_art, "dots += dash(pl,")
    drift = lit[:-1]
    redo = []
    for pl in ctx.hero["pieces"]:
        redo += mod.dash(pl, drift, lit[-1])
    if redo != ctx.hero["dots"]:
        raise RuntimeError("the drift dots no longer follow the pattern in their source line")
    pats = [("CENTRE", mod.CENTRE, "centre lines: long, gap, short, gap", 2),
            ("PHANTOM", mod.PHANTOM, "the earlier chip: long, then two shorts", 2),
            ("HIDDEN", mod.HIDDEN, f"back half of the helix, offset {fmt(hid_off)}", 6),
            ("drift dots", drift, f"the drift path, offset {fmt(lit[-1])} (a literal, = HIDDEN)", 6)]
    for name, pat, what, periods in pats:
        period = sum(pat)
        sh.text(f"{name} = [" + ", ".join(fmt(q) for q in pat) + f"], period {fmt(period)}", x0, y, BODY, CON)
        sh.text(what, x0 + 520, y, SMALL, TEXT)
        ly = y + 62
        length = period * periods
        pieces = mod.dash([(0.0, 0.0), (length, 0.0)], pat)
        sh.stroke(L_MARK, MARK_INK, mod.W_FINE * S2, [[(x0 + a * S2, ly) for a, _ in pc] for pc in pieces], cap="butt")
        acc = 0.0
        for i, q in enumerate(pat):
            xa, xb = x0 + acc * S2, x0 + (acc + q) * S2
            up = i % 2 == 0 or len(pat) == 2
            yy = ly - 16 if up else ly + 16
            sh.line([(xa, ly - 8), (xa, yy + (-4 if up else 4))], W_EXT)
            sh.line([(xb, ly - 8), (xb, yy + (-4 if up else 4))], W_EXT)
            sh.line([(xa, yy), (xb, yy)], W_DIM)
            sh.arrowhead((xa, yy), (xb, yy), 6, 2.2)
            sh.arrowhead((xb, yy), (xa, yy), 6, 2.2)
            base = yy - 5 if up else yy + 15
            sh.text(fmt(q), (xa + xb) / 2, base, SMALL, CON, anchor="middle")
            acc += q
        y = ly + 64

    # ------------------------------------------------ the crossing
    S3 = 5.0
    y += 20
    off = mod.CENTRE[0] + mod.CENTRE[1] + mod.CENTRE[2] / 2
    sh.view_title(f"Two centre lines crossing, scale {fmt(S3)}", x0, y - 30)
    m = (x0 + 46 * S3, y + 32 * S3)
    span = 45
    pls = mod.centre_line((-span, 0.0), (span, 0.0), (0.0, 0.0)) + \
        mod.centre_line((0.0, -span * 0.6), (0.0, span * 0.6), (0.0, 0.0))
    sh.stroke(L_MARK, MARK_INK, mod.W_FINE * S3, [[(m[0] + a * S3, m[1] + b * S3) for a, b in pl] for pl in pls],
              cap="butt")
    half_s = mod.CENTRE[2] / 2
    sh.dim((m[0] - half_s * S3, m[1] - 34), (m[0] + half_s * S3, m[1] - 34), None, offset=0, inside=False,
           ext=((m[0] - half_s * S3, m[1] - 8), (m[0] + half_s * S3, m[1] - 8)))
    sh.text(f"{fmt(mod.CENTRE[2])}", m[0] + half_s * S3 + 30, m[1] - 30, SMALL, CON)
    sh.dim((m[0] - off * S3, m[1] + 30), (m[0], m[1] + 30), f"offset {fmt(off)}", offset=0, size=SMALL,
           ext=((m[0] - off * S3, m[1] + 8), (m[0], m[1] + 8)), text_side=-1)
    sh.text("m", m[0] + 10, m[1] - 10, BODY, CON, pad=True)
    lines = [
        ("centre_line(a, b, m) dashes from the crossing m outward", TEXT),
        ("to both ends, starting each run this far into the pattern:", TEXT),
        (f"offset = long + gap + short/2 = {fmt(mod.CENTRE[0])} + {fmt(mod.CENTRE[1])} + "
         f"{fmt(mod.CENTRE[2])}/2 = {fmt(off)}", CON),
        ("so the short dash is centred on m: half of it on each side.", TEXT),
        ("dash(pl, pattern, offset): the first run starts at", TEXT),
        ("s = -(offset mod period) and runs alternate on, off.", CON),
        (f"PHANTOM runs start {fmt(src_numbers(mod.hero_art, 'dash(sq, PHANTOM,')[0])} into the pattern; HIDDEN "
         f"at {fmt(hid_off)}.", CON),
    ]
    sh.block(lines, x0 + 2 * span * S3 + 40, y - 6, SMALL)

    # ------------------------------------------------ small marks
    small_grid(sh, ctx, "small", ctx.small, 1350, 200, 14.0)
    small_grid(sh, ctx, "small16", ctx.small16, 1382, 860, 24.0)
    sh.title_block(W - MARGIN - 620, H - MARGIN - 200, 620, "as marked on each drawing")
    sh.frame()
    sh.finish()


def small_grid(sh, ctx, variant, tr, left, top, S):
    """A small mark on its unit grid with every coordinate and the band clearance."""
    mod = ctx.mod
    U = mod.UNITS[variant]
    ring, idx, chip, Lb, Rb = tr["ring"], tr["idx"], tr["chip"], tr["L"], tr["R"]
    rb = bbox(ring[0])
    c = ((rb[0] + rb[2]) / 2, (rb[1] + rb[3]) / 2)
    r_out = max(math.dist(c, q) for q in ring[0])
    r_in = max(math.dist(c, q) for q in ring[1])
    title = {"small": f"Small mark: {fmt(U)}-unit grid, every edge on a whole unit (crisp at {fmt(U)} px), "
                      f"scale {fmt(S)}",
             "small16": f"small16: the same mark hinted on a {fmt(U)}-unit pixel grid, scale {fmt(S)}"}[variant]
    sh.view_title(title, left - 60, top - 34)
    v = View(sh, (0, 0, U, U), left, top, S)
    v.grid(1, 4 if U >= 32 else 2, 4 if U >= 32 else 2)
    v.mark(variant)
    P = v.P
    L, T, R, B = v.px
    ray = -105
    for rr in (r_in, r_out):
        tip = P(mod.polar(c, rr, ray))
        sh.line([P(c), tip], 1.0, CON, L_GUIDE)
        sh.arrowhead(tip, P(c), 8, 2.6)
    sh.dot(P(c), 2.6)
    ib, cb = bbox(idx), bbox(chip)
    for q in list(Lb) + list(Rb) + [(ib[0], ib[1]), (ib[2], ib[3]), (cb[0], cb[1]), (cb[2], cb[3])]:
        sh.dot(P(q), 2.8)
    clear = r_in - max(math.dist(c, q) for q in list(Lb) + list(Rb))
    far = max(list(Lb), key=lambda q: math.dist(c, q))

    def pts(poly):
        return " ".join(f"({fmt(q[0])},{fmt(q[1])})" for q in poly)
    sz = SMALL
    right = [
        dict(anchor=P(mod.polar(c, r_out, ray)), lines=[(f"ring: r = {fmt(r_out)} and {fmt(r_in)} about "
                                                         f"{pt(c)}", CON),
                                                        (f"band {fmt(r_out - r_in)} wide", TEXT)]),
        dict(anchor=P(ib[2], (ib[1] + ib[3]) / 2), lines=[(f"index: x {fmt(ib[0])} to {fmt(ib[2])}, "
                                                           f"y {fmt(ib[1])} to {fmt(ib[3])}", CON),
                                                          ("on the axis x = " + fmt(c[0]), TEXT)]),
        dict(anchor=P(cb[2], cb[1] + 1), lines=[(f"chip: x {fmt(cb[0])} to {fmt(cb[2])}, y {fmt(cb[1])} to "
                                                 f"{fmt(cb[3])}", CON),
                                                (f"centre {fmt((cb[0] + cb[2]) / 2 - c[0])} right of the axis", TEXT)]),
        dict(anchor=P(Rb[0]), lines=[("bracket R (accent):", TEXT), (pts(Rb[:4]), CON), (pts(Rb[4:]), CON)]),
    ]
    left_items = [
        dict(anchor=P(Lb[0]), lines=[("bracket L (accent):", TEXT), (pts(Lb[:4]), CON), (pts(Lb[4:]), CON)]),
        dict(anchor=P(far), lines=[(f"corner {pt(far)} lies", TEXT),
                                   (f"{fmt(math.dist(c, far), 3)} from the centre:", TEXT),
                                   (f"{fmt(r_in)} - {fmt(math.dist(c, far), 3)} = {fmt(clear, 3)}", CON),
                                   ("clear of the band", TEXT)]),
    ]
    bx = mod.box(variant)
    left_items.append(dict(anchor=P(rb[0], c[1]), lines=[
        (f"box('{variant}') * {fmt(U)} =", TEXT), ("(" + ", ".join(fmt(q * U, 3) for q in bx) + ")", CON),
        ("the ring's outer edge", TEXT)]))
    sh.column(right, "right", R + 60, T, B, size=sz, knee_x=R + 2, avoid=v.label_bands(4 if U >= 32 else 2))
    sh.column(left_items, "left", L - 60, T, B, size=sz, knee_x=L - 2, avoid=v.label_bands(4 if U >= 32 else 2))


# ---------------------------------------------------------------- entry point
def build(kit, mod, sheets=None):
    """Draw the construction sheets of `mod` (the technical cutaway) into kit's guide folder.

    sheets: an iterable of sheet numbers (1..5) to draw, default all (for iterating on one)."""
    ctx = Ctx(kit, mod)
    ctx.box = mod.box("hero")
    todo = {1: sheet_overview, 2: sheet_refrigerator, 3: sheet_dial, 4: sheet_interval, 5: sheet_lines}
    for n in sorted(sheets or todo):
        todo[n](ctx)

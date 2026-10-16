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

All art is filled geometry combined in VectorCraft with real booleans (unite, minus front),
so every knockout is a hole: the same mark works in ink on paper, paper on ink, and solid
black on transparent. Each shipped SVG is one compound path (the neutral palette's accent
is the ink, so the mark draws in one colour).

Every number of the mark lives in mark.py, which also implements the shared colour-role
API (../MARK_API.md); this script only lays the mark out into documents, drawing every
deliverable through mark.draw_mark. The small companion is a separate bold redraw on a
32-unit grid; its 16 px version is hand-hinted pixel art (mark.PIX16, variant "small16").
The lab variants of the small mark below are kept for the record of the quality loop.

Usage (Python 3.12, standard library only; the engine path is in tools/vcdriver.py):
    python -I build.py            look renders in _work/, then every deliverable
    python -I build.py ship       only the deliverables, the SVG round trip and magnifier
    python -I build.py look       only the quick look renders in _work/
    python -I build.py hero       only _work/look-hero.png
    python -I build.py lab        the small-mark variants side by side, _work/lab-mag.png
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, HERE)
sys.path.insert(0, TOOLS)
from vcdriver import VC  # noqa: E402
from mark import (J, annulus, bracket, draw_mark, pol, poly, radial_bar, render, rrect,  # noqa: E402
                  sector, small_layers)

INK = "#1A1D24"
PAPER = "#F2EEE6"
BLACK = "#000000"
WHITE = "#FFFFFF"
FONT = "Space Grotesk"

# Colour roles for draw_mark. The neutral palette has accent = ink, so the mark draws in one
# colour as one compound path; REVERSED is the same on the ink ground.
NEUTRAL = {"ink": INK, "paper": PAPER, "accent": INK}
REVERSED = {"ink": PAPER, "paper": INK, "accent": PAPER}
ONE_BLACK = {"ink": BLACK, "paper": WHITE, "accent": BLACK}
ONE_WHITE = {"ink": WHITE, "paper": BLACK, "accent": WHITE}


# ---------------------------------------------------------------- small-mark lab variants
# Explorations from the quality loop, kept for the record (the shipped redraw is
# mark.small_layers, called small_e here).
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


small_e = small_layers   # the shipped redraw, from mark.py
SMALL_VARIANTS = {"d": small_d, "e": small_e, "f": small_f}


def small_lab(vc, work):
    keys = list(SMALL_VARIANTS)
    W = 48 * len(keys) + 8
    new(vc, W, 72, "lab")
    rect(vc, 0, 0, W, 72, PAPER)
    for k, key in enumerate(keys):
        S = SMALL_VARIANTS[key]()
        render(vc, S, 48 * k + 8, 4, 1.0, INK)
        render(vc, S, 48 * k + 16, 48, 0.5, INK)
    draw_mark(vc, 48 * len(keys) - 20, 48, 16, NEUTRAL, variant="small16")
    vc.tool("export", path=os.path.join(work, "lab.png"), scale=1)
    close(vc)
    magnify(os.path.join(work, "lab.png"), os.path.join(work, "lab-mag.png"), 6)


# ---------------------------------------------------------------- VectorCraft plumbing
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
    new(vc, 1000, 1000, "look")
    rect(vc, 0, 0, 1000, 1000, PAPER)
    draw_mark(vc, 0, 0, 1000, NEUTRAL)
    vc.tool("export", path=os.path.join(work, "look-hero.png"), scale=1)
    close(vc)
    for name, (fx, fy) in (("look-zoom-coax.png", (0.16, 0.66)), ("look-zoom-chip.png", (0.42, 0.22))):
        z = 2.6
        new(vc, 600, 600, "zoom")
        rect(vc, 0, 0, 600, 600, PAPER)
        draw_mark(vc, -fx * 1000 * z, -fy * 1000 * z, 1000 * z, NEUTRAL)
        vc.tool("export", path=os.path.join(work, name), scale=1)
        close(vc)
    # Small sizes side by side, at true pixel size, then magnified for inspection.
    new(vc, 520, 200, "looksmall")
    rect(vc, 0, 0, 520, 200, PAPER)
    rect(vc, 260, 0, 260, 200, INK)
    x = 10
    for sz in (128, 64):
        draw_mark(vc, x, 10, sz, NEUTRAL)
        draw_mark(vc, 260 + x, 10, sz, REVERSED)
        x += sz + 10
    for k, sz in enumerate((32, 16)):
        draw_mark(vc, 10 + k * 50, 150, sz, NEUTRAL, variant="small")
        draw_mark(vc, 270 + k * 50, 150, sz, REVERSED, variant="small")
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
    # The hero on paper: SVG (the paper square included) and a 1024 px PNG.
    new(vc, 1000, 1000, "hero")
    rect(vc, 0, 0, 1000, 1000, PAPER)
    draw_mark(vc, 0, 0, 1000, NEUTRAL)
    vc.tool("export", path=os.path.join(out, "hero.svg"))
    vc.tool("export", path=os.path.join(out, "hero-1024.png"), scale=1.024)
    close(vc)
    # Solid black on transparent.
    new(vc, 1000, 1000, "hero-black")
    draw_mark(vc, 0, 0, 1000, ONE_BLACK, mono=True)
    vc.tool("export", path=os.path.join(out, "hero-black.svg"))
    close(vc)
    # Solid white on black.
    new(vc, 1000, 1000, "hero-white-on-black")
    rect(vc, 0, 0, 1000, 1000, BLACK)
    draw_mark(vc, 0, 0, 1000, ONE_WHITE, mono=True)
    vc.tool("export", path=os.path.join(out, "hero-white-on-black.png"), scale=1.024)
    close(vc)
    # The small companion: ink on transparent as SVG; true-size PNGs on paper.
    new(vc, 32, 32, "small")
    draw_mark(vc, 0, 0, 32, NEUTRAL, variant="small")
    vc.tool("export", path=os.path.join(out, "small.svg"))
    close(vc)
    for px, variant in ((32, "small"), (16, "small16")):
        new(vc, px, px, f"small-{px}")
        rect(vc, 0, 0, px, px, PAPER)
        draw_mark(vc, 0, 0, px, NEUTRAL, variant=variant)
        vc.tool("export", path=os.path.join(out, f"small-{px}.png"), scale=1)
        close(vc)
    sheet(vc, out)


def sheet(vc, out):
    """One presentation sheet at true pixel scale (exported at scale 1)."""
    W, Ht = 2000, 1130
    new(vc, W, Ht, "sheet")
    rect(vc, 0, 0, W, Ht, "#E3DED4")
    # The hero, large, on paper.
    rect(vc, 40, 40, 1050, 1050, PAPER)
    draw_mark(vc, 65, 65, 1000, NEUTRAL)
    X = 1130
    # On the dark ink ground, and solid black on white.
    rect(vc, X, 40, 405, 405, INK)
    draw_mark(vc, X + 22.5, 62.5, 360, REVERSED)
    rect(vc, X + 425, 40, 405, 405, WHITE)
    draw_mark(vc, X + 447.5, 62.5, 360, ONE_BLACK, mono=True)
    # The size ladder at true pixels: hero 128 and 64, small mark 32 and 16.
    for k, (ground, art) in enumerate(((PAPER, INK), (INK, PAPER))):
        colours = {"ink": art, "paper": ground, "accent": art}
        y0 = 475 + k * 205
        rect(vc, X, y0, 830, 185, ground)
        x = X + 28
        cy = y0 + 92
        for sz in (128, 64):
            draw_mark(vc, x, cy - sz // 2, sz, colours)
            x += sz + 44
        draw_mark(vc, x, cy - 16, 32, colours, variant="small")
        x += 32 + 44
        draw_mark(vc, x, cy - 8, 16, colours, variant="small16")
        # the small mark magnified, to show its pixel grid
        draw_mark(vc, X + 830 - 28 - 128, cy - 64, 128, colours, variant="small")
    # The lockup.
    y0 = 885
    rect(vc, X, y0, 830, 205, PAPER)
    draw_mark(vc, X + 30, y0 + 32.5, 140, NEUTRAL)
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
            new(vc, 1000, 1000, "look")
            rect(vc, 0, 0, 1000, 1000, PAPER)
            draw_mark(vc, 0, 0, 1000, NEUTRAL)
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

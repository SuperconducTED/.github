"""SuperconducTED logo, round 3: the ISOMETRIC ILLUSTRATION candidate's deliverables.

The drawing itself lives in `mark.py` (geometry, colour roles, emission, one-colour cutting);
this script only lays out documents, calls `mark.draw_mark` for every mark it places, and
exports the files. See mark.py for what the mark shows and how its colours are assigned.

Contract
--------
Inputs: none (the geometry's numbers live in mark.py, the layouts' numbers here). Optional
argv[1] = "quick" renders the hero PNGs, review crops in _work/ and the small mark, and skips
the one-colour hero and the sheet.
Outputs (next to this file): hero.svg, hero-1024.png, hero-128.png (review), hero-black.svg,
hero-white-on-black.png, hero-dark.png (review), small.svg, small-32.png, small-16.png,
sheet.png, and _work/ intermediates.
Side effects: one VectorCraft child process confined to this folder.

Colour sets used here (role -> colour, see mark.py for the roles):
* NEUTRAL, the brief's two neutrals with accent = ink: every file on paper.
* DARK = on_dark(NEUTRAL): ink and paper swapped, so the tint ladder inverts on the ink ground.
* BLACK and WHITE: the one-colour versions, solid black and solid white.
"""
import os
import re
import sys

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "_work")
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "..", "tools"))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)   # python -I leaves the script's folder off sys.path
from vcdriver import VC, fresh_export  # noqa: E402
import mark  # noqa: E402
from mark import INK, NEUTRAL, PAPER, box, draw_mark, on_dark  # noqa: E402

DOC_NAME = "SuperconducTED"
FONT = "Space Grotesk"

DARK = on_dark(NEUTRAL)
BLACK = {"ink": "#000000", "paper": "#FFFFFF", "accent": "#000000"}
WHITE = {"ink": "#FFFFFF", "paper": "#000000", "accent": "#FFFFFF"}


def rect(vc, x, y, w, h, fill):
    vc.tool("draw_shape", shape="rectangle", x=x, y=y, width=w, height=h, fill=fill, stroke="none")


def new_doc(vc, w, h):
    vc.cmd("file.new", width=w, height=h, units="Pixels", name=DOC_NAME)


def centred(bx, by, bw, bh):
    """(x, y, side) of the unit square that centres the hero's visible art in the box
    (bx, by, bw, bh) at the largest size that fits; uses only box("hero")."""
    u0, v0, u1, v1 = box("hero")
    side = min(bw / (u1 - u0), bh / (v1 - v0))
    return bx + (bw - side) / 2, by + (bh - side) / 2, side


# ----------------------------------------------------------------------------------------
# Deliverables
# ----------------------------------------------------------------------------------------
HERO = 1024
HERO_MARGIN = 70
HERO_SQUARE = (HERO_MARGIN, HERO_MARGIN, HERO - 2 * HERO_MARGIN)   # x, y, side of the unit square


def hero_files(vc, quick=False):
    new_doc(vc, HERO, HERO)
    rect(vc, 0, 0, HERO, HERO, PAPER)
    n = len(draw_mark(vc, *HERO_SQUARE, NEUTRAL))
    vc.tool("export", path=os.path.join(HERE, "hero-1024.png"))
    vc.tool("export", path=os.path.join(HERE, "hero-128.png"), scale=128 / HERO)
    if not quick:
        vc.tool("export", path=os.path.join(HERE, "hero.svg"))
        vc.tool("save_file", path=os.path.join(WORK, "hero.vectorcraft"))
    vc.cmd("file.close")
    print("hero paths", n, "box", [round(v, 4) for v in box("hero")])
    # dark ground
    new_doc(vc, HERO, HERO)
    rect(vc, 0, 0, HERO, HERO, INK)
    draw_mark(vc, *HERO_SQUARE, DARK)
    vc.tool("export", path=os.path.join(HERE, "hero-dark.png"))
    vc.cmd("file.close")
    if quick:
        new_doc(vc, HERO, HERO)
        rect(vc, 0, 0, HERO, HERO, "#FFFFFF")
        draw_mark(vc, *HERO_SQUARE, BLACK, mono=True, knockouts="paint")
        vc.tool("export", path=os.path.join(WORK, "hero-mono-preview.png"))
        vc.cmd("file.close")
        # review crops at 2.5x: the dial stage and the middle of the stack, centred on the page
        side = HERO_SQUARE[2] * 2.5
        S, ox, oy = mark.transform("hero", 0.0, 0.0, side)
        for name, pt in (("zoom-dial", (0.2, -0.1, 0.25)), ("zoom-stack", (0.1, 0, 1.6))):
            cx, cy = mark.pr(pt)
            new_doc(vc, HERO, HERO)
            rect(vc, 0, 0, HERO, HERO, PAPER)
            draw_mark(vc, HERO / 2 - (ox + S * cx), HERO / 2 - (oy + S * cy), side, NEUTRAL)
            vc.tool("export", path=os.path.join(WORK, name + ".png"))
            vc.cmd("file.close")
        return
    # one colour, solid black on transparent
    new_doc(vc, HERO, HERO)
    draw_mark(vc, *HERO_SQUARE, BLACK, mono=True)
    write_mono_svg(vc, "#000000", os.path.join(HERE, "hero-black.svg"), "hero-black")
    # solid white on black: the same one-colour drawing with its knockouts painted black
    new_doc(vc, HERO, HERO)
    rect(vc, 0, 0, HERO, HERO, "#000000")
    draw_mark(vc, *HERO_SQUARE, WHITE, mono=True, knockouts="paint")
    vc.tool("export", path=os.path.join(HERE, "hero-white-on-black.png"))
    vc.cmd("file.close")


def write_mono_svg(vc, colour, out_svg, tag):
    """Write the active document (a draw_mark(mono=True) drawing) as a one-colour SVG and close
    it. The SVG goes through one import round trip (export, open, export): VectorCraft's SVG
    import drops the degenerate curve segments the pathfinder merge leaves, and the shipped
    files have always come through that route. Asserts that only `colour` remains, with no
    strokes and no opacity."""
    clean = os.path.join(WORK, tag + "-clean.svg")
    fresh_export(vc, clean)
    vc.cmd("file.close")
    vc.tool("open_file", path=clean)
    fresh_export(vc, out_svg)
    vc.tool("save_file", path=os.path.join(WORK, tag + ".vectorcraft"))
    vc.cmd("file.close")
    text = open(out_svg, encoding="utf-8").read()
    text = re.sub(r"<title>[^<]*</title>", "<title>" + DOC_NAME + "</title>", text, count=1)
    open(out_svg, "w", encoding="utf-8").write(text)
    fills = set(f.lower() for f in re.findall(r'fill="([^"]+)"', text))
    assert fills <= {colour.lower(), "none"}, fills
    assert "opacity" not in text and "stroke=" not in text.replace('stroke="none"', "")
    print(tag, "paths", text.count("<path"), "fills", sorted(fills))


def small_files(vc):
    for size, name in ((32, "small-32.png"), (16, "small-16.png")):
        new_doc(vc, size, size)
        rect(vc, 0, 0, size, size, PAPER)
        draw_mark(vc, 0, 0, size, NEUTRAL, "small")
        vc.tool("export", path=os.path.join(HERE, name))
        vc.cmd("file.close")
    # small.svg: one colour (ink) with transparent knockouts, on a 64 x 64 artboard
    new_doc(vc, 64, 64)
    draw_mark(vc, 0, 0, 64, NEUTRAL, "small", mono=True)
    write_mono_svg(vc, INK, os.path.join(HERE, "small.svg"), "small")
    # review strip: 16, 32 and 128 px, on paper and on ink
    new_doc(vc, 420, 140)
    rect(vc, 0, 0, 420, 140, "#FFFFFF")
    x = 10
    for size in (16, 32, 128):
        for colours in (NEUTRAL, DARK):
            rect(vc, x, 6, size, size, colours["paper"])
            draw_mark(vc, x, 6, size, colours, "small")
            x += size + 8
    vc.tool("export", path=os.path.join(WORK, "small-review.png"))
    vc.cmd("file.close")


def text_outlined(vc, s, x, base, size, colour, style="Medium", tracking=None):
    t = vc.tool("add_text", x=x, y=base, text=s, font=FONT, size=size, color=colour)["id"]
    kw = {"id": t, "style": style}
    if tracking is not None:
        kw["tracking"] = tracking
    vc.cmd("text.setStyle", **kw)
    vc.cmd("select.set", ids=[t])
    return vc.cmd("type.createOutlines")["ids"]


def sheet(vc):
    W, H = 2000, 1300
    new_doc(vc, W, H)
    rect(vc, 0, 0, W, H, "#FFFFFF")
    # the hero, large, on paper
    rect(vc, 40, 40, 1000, 1000, PAPER)
    draw_mark(vc, 40 + 50, 40 + 50, 900, NEUTRAL)
    # dark ground
    rect(vc, 1070, 40, 440, 440, INK)
    draw_mark(vc, 1070 + 30, 40 + 30, 380, DARK)
    # solid black, the flattened one-colour file placed as it ships
    rect(vc, 1530, 40, 430, 440, "#FFFFFF")
    vc.cmd("file.place", path=os.path.join(HERE, "hero-black.svg"), link=False, rect=[1530 + 25, 40 + 25, 380, 390])
    # hero at 128 and 64 px, on paper and on ink
    x = 1070
    for size in (128, 64):
        for colours in (NEUTRAL, DARK):
            rect(vc, x, 510, size, size, colours["paper"])
            draw_mark(vc, x + size * 0.06, 510 + size * 0.06, size * 0.88, colours)
            x += size + 18
    # small mark at 32 and 16 px, on paper and on ink
    for size in (32, 16):
        for colours in (NEUTRAL, DARK):
            rect(vc, x, 510, size, size, colours["paper"])
            draw_mark(vc, x, 510, size, colours, "small")
            x += size + 14
    # white on black
    rect(vc, 1070, 690, 300, 350, "#000000")
    draw_mark(vc, *centred(1070 + 20, 690 + 20, 260, 310), WHITE, mono=True, knockouts="paint")
    # lockup on paper: the hero mark and the word
    rect(vc, 1390, 690, 570, 350, PAPER)
    draw_mark(vc, *centred(1410, 715, 130, 300), NEUTRAL)
    text_outlined(vc, "SuperconducTED", 1556, 878, 44, INK, "Medium")
    text_outlined(vc, "NOISE ENGINE", 1558, 916, 16, INK, "Medium", tracking=300)
    # small-mark lockup on ink
    rect(vc, 40, 1070, 1920, 190, INK)
    draw_mark(vc, 70, 1101, 128, DARK, "small")
    text_outlined(vc, "SuperconducTED", 230, 1195, 72, PAPER, "Medium")
    draw_mark(vc, *centred(1050, 1085, 90, 160), DARK)
    text_outlined(vc, "SuperconducTED", 1160, 1175, 52, PAPER, "Medium")
    text_outlined(vc, "NOISE ENGINE", 1162, 1215, 18, PAPER, "Medium", tracking=260)
    vc.tool("export", path=os.path.join(HERE, "sheet.png"))
    vc.tool("save_file", path=os.path.join(WORK, "sheet.vectorcraft"))
    vc.cmd("file.close")


def main():
    quick = len(sys.argv) > 1 and sys.argv[1] == "quick"
    os.makedirs(WORK, exist_ok=True)
    c = mark.resolve(NEUTRAL)
    print("primitives", len(mark.art("hero")), "tints", c["tint-light"], c["tint-shade"],
          "dark tints", mark.resolve(DARK)["tint-light"], mark.resolve(DARK)["tint-shade"])
    with VC(HERE) as vc:
        hero_files(vc, quick)
        small_files(vc)
        if not quick:
            sheet(vc)
    print("ok")


if __name__ == "__main__":
    main()

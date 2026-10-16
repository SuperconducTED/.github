"""SuperconducTED round 3, style: technical cutaway / engineering drawing. The deliverables.

The mark itself (every number of the drawing and the colour-role API) lives in `mark.py`; this
script only lays it out into documents, drawing every mark through `mark.draw_mark` in the
neutral colours of ../MARK_API.md (ink #1A1D24, paper #F2EEE6, accent = ink), so the accent
changes nothing here. Rerun it to regenerate every file (about 1.5 s).

Contract
--------
* Inputs: none (layout numbers here, mark numbers in mark.py). Requires the VectorCraft CLI and
  the shared driver brand/tools/vcdriver.py.
* Outputs (this folder only): hero.svg, hero-1024.png, hero-black.svg, hero-white-on-black.png,
  small.svg, small-32.png, small-16.svg, small-16.png, sheet.png, plus the git-ignored check
  renders check-hero-128.png and check-hero-64.png.
* Side effects: one VectorCraft engine process; files written only inside this folder; no
  bytecode cache written anywhere (sys.dont_write_bytecode).
* Invariant: every one-colour version is drawn with mono=True, so it is one colour with real
  knockouts (clipped lines, opposite-winding holes), never a paper-coloured patch.
"""
import os
import sys

sys.dont_write_bytecode = True   # importing mark and vcdriver must not write __pycache__ anywhere
HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "tools")
sys.path.insert(0, HERE)
sys.path.insert(1, TOOLS)
from mark import draw_mark  # noqa: E402
from vcdriver import VC  # noqa: E402

OUT = HERE
INK, PAPER = "#1A1D24", "#F2EEE6"
BLACK, WHITE = "#000000", "#FFFFFF"
FONT = "Space Grotesk"

NEUTRAL = {"ink": INK, "paper": PAPER, "accent": INK}      # MARK_API's neutral colours
REVERSED = {"ink": PAPER, "paper": INK, "accent": PAPER}   # the same two tones, paper on an ink ground
ONE_BLACK = {"ink": BLACK}                                 # with mono=True: solid black
ONE_WHITE = {"ink": WHITE}                                 # with mono=True: solid white

# ---------------------------------------------------------------- documents


def rect(vc, x, y, w, h, fill, stroke=None, sw=1.0):
    a = dict(shape="rectangle", x=x, y=y, width=w, height=h, fill=fill, stroke=stroke or "none")
    if stroke:
        a["strokeWidth"] = sw
    vc.tool("draw_shape", **a)


def text(vc, s, x, base, size, colour, style="Regular", tracking=None):
    t = vc.tool("add_text", x=x, y=base, text=s, font=FONT, size=size, color=colour)["id"]
    kw = dict(id=t, style=style)
    if tracking is not None:
        kw["tracking"] = tracking
    vc.cmd("text.setStyle", **kw)
    vc.cmd("select.set", ids=[t])
    vc.cmd("type.createOutlines")


def doc(vc, w, h, name):
    vc.cmd("file.new", width=w, height=h, units="Pixels", name="SuperconducTED")  # the SVG <title>: the one permitted word


def path(name):
    return os.path.join(OUT, name)


def build_hero_files(vc):
    doc(vc, 1024, 1024, "hero")
    rect(vc, 0, 0, 1024, 1024, PAPER)
    draw_mark(vc, 0, 0, 1024, NEUTRAL)
    vc.tool("export", path=path("hero.svg"))
    vc.tool("export", path=path("hero-1024.png"), scale=1)
    vc.tool("export", path=path("check-hero-128.png"), scale=0.125)
    vc.tool("export", path=path("check-hero-64.png"), scale=0.0625)
    vc.cmd("file.close")

    doc(vc, 1024, 1024, "hero-black")
    draw_mark(vc, 0, 0, 1024, ONE_BLACK, mono=True)
    vc.tool("export", path=path("hero-black.svg"))
    vc.cmd("file.close")

    doc(vc, 1024, 1024, "hero-white-on-black")
    rect(vc, 0, 0, 1024, 1024, BLACK)
    draw_mark(vc, 0, 0, 1024, ONE_WHITE, mono=True)
    vc.tool("export", path=path("hero-white-on-black.png"), scale=1)
    vc.cmd("file.close")

    doc(vc, 32, 32, "small")
    rect(vc, 0, 0, 32, 32, PAPER)
    draw_mark(vc, 0, 0, 32, NEUTRAL, variant="small")
    vc.tool("export", path=path("small.svg"))
    vc.tool("export", path=path("small-32.png"), scale=1)
    vc.cmd("file.close")

    doc(vc, 16, 16, "small-16")
    rect(vc, 0, 0, 16, 16, PAPER)
    draw_mark(vc, 0, 0, 16, NEUTRAL, variant="small16")
    vc.tool("export", path=path("small-16.svg"))
    vc.tool("export", path=path("small-16.png"), scale=1)
    vc.cmd("file.close")


def build_sheet(vc):
    W, H = 2000, 1540
    doc(vc, W, H, "sheet")
    rect(vc, 0, 0, W, H, PAPER)
    # A: the hero, large (1000 px), on paper with a hairline frame
    rect(vc, 40, 40, 1000, 1000, PAPER, INK, 1.0)
    draw_mark(vc, 40, 40, 1000, NEUTRAL)
    # B: paper on ink, C: black on white, D: white on black
    P = 430
    rect(vc, 1080, 40, P, P, INK)
    draw_mark(vc, 1080, 40, P, REVERSED)
    rect(vc, 1530, 40, P, P, WHITE)
    draw_mark(vc, 1530, 40, P, ONE_BLACK, mono=True)
    rect(vc, 1080, 490, P, P, BLACK)
    draw_mark(vc, 1080, 490, P, ONE_WHITE, mono=True)
    # E: sizes. Row 1 on paper, row 2 on ink: hero 128, hero 64, small 32, small 16
    rect(vc, 1530, 490, P, P, PAPER, INK, 1.0)
    for row, (ground, colours) in enumerate(((PAPER, NEUTRAL), (INK, REVERSED))):
        y = 520 + row * 200
        x = 1556
        for size, variant in ((128, "hero"), (64, "hero"), (32, "small"), (16, "small16")):
            rect(vc, x, y, size, size, ground)
            draw_mark(vc, x, y, size, colours, variant=variant)
            x += size + 34
    # F: lockup as a title block: mark cell, name, rule, descriptor
    y = 1080
    rect(vc, 40, y, 1920, 420, PAPER, INK, 2.0)
    vc.tool("draw_path", d=f"M 500 {y} L 500 {y + 420}", fill="none", stroke=INK, strokeWidth=1.0)
    draw_mark(vc, 70, y + 10, 400, NEUTRAL)
    text(vc, "SuperconducTED", 556, y + 222, 132, INK, "Medium")
    vc.tool("draw_path", d=f"M 500 {y + 300} L 1960 {y + 300}", fill="none", stroke=INK, strokeWidth=1.0)
    text(vc, "NOISE ENGINE", 560, y + 375, 40, INK, "Medium", tracking=420)
    # right-hand cell: the favicon companion, so the lockup shows the whole system
    vc.tool("draw_path", d=f"M 1690 {y} L 1690 {y + 300}", fill="none", stroke=INK, strokeWidth=1.0)
    draw_mark(vc, 1745, y + 70, 160, NEUTRAL, variant="small")
    vc.tool("export", path=path("sheet.png"), scale=1)
    vc.cmd("file.close")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with VC(OUT) as vc:
        build_hero_files(vc)
        build_sheet(vc)
    print("ok")


if __name__ == "__main__":
    main()

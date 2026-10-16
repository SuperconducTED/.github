"""SuperconducTED round 3, style ENGRAVED EMBLEM / SEAL: the deliverables and the sheet.

The mark itself lives in mark.py (every number of the geometry) behind the shared API of
../MARK_API.md. This script only chooses documents, grounds, placements and colours, and draws
every mark through mark.draw_mark. With the neutral palette (accent = ink) it reproduces the
committed hero.svg, hero-black.svg and small.svg byte for byte and every committed PNG pixel
for pixel; check_api.py proves that and the accent and mono rules.

Usage:  python -I build.py [hero|all]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)        # python -I leaves the script's folder off sys.path
from vcdriver import VC  # noqa: E402
from mark import FONT, draw_mark, hero_art  # noqa: E402

INK, PAPER = "#1A1D24", "#F2EEE6"
WORK = os.path.join(HERE, "work")


def neutral(ink=INK, ground=PAPER):
    """The neutral palette of the committed deliverables: the accent is the ink, so the range
    reads in the same tone as the machine; `ground` is the paper role (the small mark's disc)."""
    return {"ink": ink, "paper": ground, "accent": ink}


def rect(vc, x, y, w, h, fill, r=0):
    a = dict(shape="rectangle", x=x, y=y, width=w, height=h, fill=fill, stroke="none")
    if r:
        a["radius"] = r
    vc.tool("draw_shape", **a)


def hero_on_paper(vc):
    """The hero on paper at 1024 px, with the review renders at 128 and 64 px."""
    vc.cmd("file.new", width=1024, height=1024, units="Pixels", name="hero")
    rect(vc, 0, 0, 1024, 1024, PAPER)
    draw_mark(vc, 0, 0, 1024, neutral())
    vc.tool("export", path=os.path.join(HERE, "hero-1024.png"))
    vc.tool("export", path=os.path.join(WORK, "hero-128.png"), scale=0.125)
    vc.tool("export", path=os.path.join(WORK, "hero-64.png"), scale=0.0625)


def deliverables(vc):
    # hero on paper: PNG 1024 and SVG
    hero_on_paper(vc)
    vc.tool("export", path=os.path.join(HERE, "hero.svg"), format="svg", outlineText=True)
    vc.cmd("file.close")
    # solid black on transparent: the mono version (one colour, strokes kept)
    vc.cmd("file.new", width=1024, height=1024, units="Pixels", name="hero-black")
    draw_mark(vc, 0, 0, 1024, neutral("#000000", "#FFFFFF"), mono=True)
    vc.tool("export", path=os.path.join(HERE, "hero-black.svg"), format="svg", outlineText=True)
    vc.cmd("file.close")
    # solid white on black, mono
    vc.cmd("file.new", width=1024, height=1024, units="Pixels", name="hero-white")
    rect(vc, 0, 0, 1024, 1024, "#000000")
    draw_mark(vc, 0, 0, 1024, neutral("#FFFFFF", "#000000"), mono=True)
    vc.tool("export", path=os.path.join(HERE, "hero-white-on-black.png"))
    vc.cmd("file.close")
    # the small companion mark: ink on a paper disc, 32 grid
    vc.cmd("file.new", width=32, height=32, units="Pixels", name="small")
    draw_mark(vc, 0, 0, 32, neutral(), "small")
    vc.tool("export", path=os.path.join(HERE, "small.svg"), format="svg", outlineText=True)
    vc.tool("export", path=os.path.join(HERE, "small-32.png"))
    vc.tool("export", path=os.path.join(HERE, "small-16.png"), scale=0.5)
    vc.cmd("file.close")


def sheet(vc):
    """Presentation sheet. Hero placements use power-of-two sizes (1024, 512, 256, 128, 64)
    so the field ruling, laid on a 4 px pitch at 1024, divides the pixel grid everywhere.
    On an ink ground the small mark is the mono version in paper (no disc)."""
    W, H = 2000, 1448
    vc.cmd("file.new", width=W, height=H, units="Pixels", name="sheet")
    rect(vc, 0, 0, W, H, PAPER)
    on_ink = neutral(PAPER, INK)
    # 1. the hero, large, on paper
    draw_mark(vc, 40, 40, 1024, neutral())
    # 2. on a dark ink ground, and solid black on white
    x2 = 1104
    rect(vc, x2, 40, 512, 512, INK)
    draw_mark(vc, x2, 40, 512, on_ink)
    rect(vc, x2, 592, 512, 512, "#FFFFFF")
    draw_mark(vc, x2, 592, 512, neutral("#000000", "#FFFFFF"), mono=True)
    # 3. small sizes: hero 128 and 64 on paper and on ink; small mark 32 and 16
    x3 = 1656
    draw_mark(vc, x3, 40, 128, neutral())
    rect(vc, x3 + 152, 40, 128, 128, INK)
    draw_mark(vc, x3 + 152, 40, 128, on_ink)
    draw_mark(vc, x3, 208, 64, neutral())
    rect(vc, x3 + 152, 208, 64, 64, INK)
    draw_mark(vc, x3 + 152, 208, 64, on_ink)
    y = 312
    draw_mark(vc, x3, y, 32, neutral(), "small")
    draw_mark(vc, x3 + 56, y + 8, 16, neutral(), "small")
    rect(vc, x3 + 152, y - 8, 104, 48, INK)
    draw_mark(vc, x3 + 160, y, 32, on_ink, "small", mono=True)
    draw_mark(vc, x3 + 216, y + 8, 16, on_ink, "small", mono=True)
    # the small mark enlarged, to show its drawing
    draw_mark(vc, x3, 392, 128, neutral(), "small")
    rect(vc, x3 + 152, 392, 128, 128, INK)
    draw_mark(vc, x3 + 152, 392, 128, on_ink, "small", mono=True)
    # 4. lockups: the seal with the word, and the small mark with the word
    draw_mark(vc, 40, 1144, 256, neutral())
    t = vc.tool("add_text", x=330, y=1290, text="SuperconducTED", font=FONT, size=128, color=INK)["id"]
    vc.cmd("text.setStyle", id=t, style="Medium", tracking=-10)
    t2 = vc.tool("add_text", x=336, y=1352, text="NOISE ENGINE", font=FONT, size=34, color=INK)["id"]
    vc.cmd("text.setStyle", id=t2, style="Medium", tracking=420)
    draw_mark(vc, 1416, 1236, 64, neutral(), "small")
    t3 = vc.tool("add_text", x=1496, y=1290, text="SuperconducTED", font=FONT, size=52, color=INK)["id"]
    vc.cmd("text.setStyle", id=t3, style="Medium", tracking=-10)
    vc.tool("export", path=os.path.join(HERE, "sheet.png"))
    vc.cmd("file.close")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "hero"
    os.makedirs(WORK, exist_ok=True)
    with VC(HERE) as vc:
        # outline the lettering now, before any deliverable document is opened
        art, info = hero_art(vc)
        print("lines", len(art.lines), "fills", len(art.fills), info)
        if mode == "hero":
            hero_on_paper(vc)
            vc.cmd("file.close")
        else:
            deliverables(vc)
            sheet(vc)
    print("ok")


if __name__ == "__main__":
    main()

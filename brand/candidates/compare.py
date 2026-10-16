"""Side-by-side comparison of the four round-3 candidates, composed in VectorCraft.

Usage (from the repository root, after each candidate's build.py has run):
    python -I brand/candidates/compare.py brand/candidates

Reads <folder>/<style>/hero-1024.png, hero-white-on-black.png, small-32.png and small-16.png
and writes <folder>/compare.png.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
from vcdriver import VC  # noqa: E402

COLS = [("engraved", "1  Engraved seal"), ("cutaway", "2  Technical cutaway"),
        ("radial", "3  Radial astrolabe"), ("isometric", "4  Isometric")]
INK, PAPER = "#1A1D24", "#F2EEE6"


def place(vc, path, x, y, w, h):
    oid = vc.cmd("file.place", path=path, link=False)["ids"][0]
    vc.cmd("select.set", ids=[oid])
    vc.cmd("object.setBounds", x=x, y=y, width=w, height=h, reference=0)


def text(vc, s, x, base, size, colour, style="Regular"):
    t = vc.tool("add_text", x=x, y=base, text=s, font="Space Grotesk", size=size, color=colour)["id"]
    if style != "Regular":
        vc.cmd("text.setStyle", id=t, style=style)


def main():
    root = os.path.abspath(sys.argv[1])
    W, H = 2000, 980
    with VC(root) as vc:
        vc.cmd("file.new", width=W, height=H, units="Pixels", name="compare")
        vc.tool("draw_shape", shape="rectangle", x=0, y=0, width=W, height=H, fill="#FFFFFF", stroke="none")
        for i, (key, label) in enumerate(COLS):
            x = 20 + i * 495
            text(vc, label, x, 44, 26, INK, "Medium")
            place(vc, os.path.join(root, key, "hero-1024.png"), x, 64, 475, 475)
            place(vc, os.path.join(root, key, "hero-white-on-black.png"), x, 556, 230, 230)
            # real-size samples on paper and on ink
            vc.tool("draw_shape", shape="rectangle", x=x + 245, y=556, width=230, height=230, fill=PAPER, stroke="none")
            place(vc, os.path.join(root, key, "hero-1024.png"), x + 255, 566, 128, 128)
            place(vc, os.path.join(root, key, "hero-1024.png"), x + 395, 566, 64, 64)
            place(vc, os.path.join(root, key, "small-32.png"), x + 395, 650, 32, 32)
            place(vc, os.path.join(root, key, "small-16.png"), x + 440, 658, 16, 16)
            text(vc, "128 px    64 / 32 / 16 px", x + 255, 760, 14, "#555555")
        text(vc, "Top: hero at 475 px. Bottom left: one-colour white on black. Bottom right: real pixel sizes "
                 "(hero at 128 and 64 px, small mark at 32 and 16 px).", 20, 840, 18, "#333333")
        text(vc, "All four carry the chandelier, the calibration dial, the drifting chip and the interval brackets. "
                 "Two neutral tones only; palette still open.", 20, 872, 18, "#333333")
        vc.tool("export", path=os.path.join(root, "compare.png"))
        vc.cmd("file.close")
    print("ok")


if __name__ == "__main__":
    main()

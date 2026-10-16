"""Install Space Grotesk into VectorCraft, for the brand lettering and lockups.

Usage:
    python -I brand/tools/install_fonts.py <folder holding the Space Grotesk TTFs>

Get the fonts first: SpaceGrotesk-Regular.ttf, SpaceGrotesk-Medium.ttf and
SpaceGrotesk-Bold.ttf from fonts/ttf/static in the designer's repository,
https://github.com/floriankarsten/space-grotesk (SIL Open Font License 1.1). Put them in a
folder of their own.

What it does, and nothing else:
  0. If VectorCraft already lists Regular, Medium and Bold for "Space Grotesk", says so and stops.
  1. Asks VectorCraft to look for the Regular, Medium and Bold faces in that folder
     (text.findFontFiles), then installs what it finds (text.addFontFiles). VectorCraft copies
     the files into its own Fonts folder (%APPDATA%\\VectorCraft\\Fonts on Windows) and never
     replaces a file already there. Delete them from that folder to uninstall.
  2. Prints the styles VectorCraft now lists for the family "Space Grotesk".
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcdriver import VC  # noqa: E402

STYLES = ("Regular", "Medium", "Bold")


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 2)
    folder = os.path.abspath(sys.argv[1])
    with VC(folder) as vc:
        try:
            have = set(vc.cmd("text.fontList", family="Space Grotesk")["styles"])
        except RuntimeError:
            have = set()
        if have >= set(STYLES):
            print("Space Grotesk is already installed:", sorted(have))
            return
        vc.cmd("text.findFontFiles", folder=folder,
               fonts=[{"family": "Space Grotesk", "style": s} for s in STYLES])
        for _ in range(60):
            state = vc.cmd("text.findFontFiles")
            if state.get("state") != "searching":
                break
            time.sleep(1)
        files = sorted({f for font in state.get("fonts", []) for f in font.get("files", [])})
        if not files:
            raise SystemExit(f"No Space Grotesk Regular, Medium or Bold TTF found in {folder}")
        result = vc.cmd("text.addFontFiles", files=files)
        for item in result.get("copied", []) + result.get("kept", []):
            print("installed:", item["to"])
        print("Space Grotesk ->", vc.cmd("text.fontList", family="Space Grotesk")["styles"])


if __name__ == "__main__":
    main()

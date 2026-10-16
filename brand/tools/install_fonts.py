"""Install the brand typefaces into VectorCraft: Space Grotesk and Space Mono.

Usage:
    python -I brand/tools/install_fonts.py <folder> [<folder> ...]

Each folder holds TTFs downloaded from the official sources (both SIL Open Font License 1.1):
  * Space Grotesk: SpaceGrotesk-Regular.ttf, -Medium.ttf and -Bold.ttf from fonts/ttf/static
    in the designer's repository, https://github.com/floriankarsten/space-grotesk
  * Space Mono: SpaceMono-Regular.ttf and SpaceMono-Bold.ttf from ofl/spacemono in Google
    Fonts' repository, https://github.com/google/fonts

What it does, and nothing else:
  0. Skips every family whose styles VectorCraft already lists.
  1. Asks VectorCraft to look for the missing faces in the given folders (text.findFontFiles)
     and installs what it finds (text.addFontFiles). VectorCraft copies the files into its own
     Fonts folder (%APPDATA%\\VectorCraft\\Fonts on Windows) and never replaces a file already
     there. Delete them from that folder to uninstall.
  2. Prints the styles VectorCraft now lists for each family, and exits non-zero if any brand
     face is still missing.

`text.fontList` matches family names loosely (asking for "Space Grotesk Medium" answers with
"Space Grotesk"), so a family only counts as present when the name it answers with is the one
asked for.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vcdriver import VC  # noqa: E402

FAMILIES = {"Space Grotesk": ("Regular", "Medium", "Bold"), "Space Mono": ("Regular", "Bold")}


def installed_styles(vc, family):
    try:
        info = vc.cmd("text.fontList", family=family)
    except RuntimeError:
        return set()
    return set(info.get("styles", [])) if info.get("family", "").lower() == family.lower() else set()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 2)
    folders = [os.path.abspath(f) for f in sys.argv[1:]]
    root = os.path.commonpath(folders)
    with VC(root) as vc:
        wanted = [{"family": fam, "style": s} for fam, styles in FAMILIES.items()
                  for s in styles if s not in installed_styles(vc, fam)]
        files = set()
        for folder in folders if wanted else []:
            vc.cmd("text.findFontFiles", folder=folder, fonts=wanted)
            for _ in range(60):
                state = vc.cmd("text.findFontFiles")
                if state.get("state") != "searching":
                    break
                time.sleep(1)
            files |= {f for font in state.get("fonts", []) for f in font.get("files", [])}
        if files:
            result = vc.cmd("text.addFontFiles", files=sorted(files))
            for item in result.get("copied", []) + result.get("kept", []):
                print("installed:", item["to"])
        missing = []
        for fam, styles in FAMILIES.items():
            have = installed_styles(vc, fam)
            print(f"{fam}: {sorted(have)}")
            missing += [f"{fam} {s}" for s in styles if s not in have]
        if missing:
            raise SystemExit("Still missing: " + ", ".join(missing))


if __name__ == "__main__":
    main()

"""Verify the exported SVGs, not the in-memory geometry.

For every filled path in each SVG: split its `d` into subpaths, compute each subpath's signed
area (straight segments only, which is all build.py emits for fills), and evaluate the nonzero
winding number at sample points that must be HOLES (chip qubit centres, dial interior, small-mark
ring interior) and points that must be INK. Exits non-zero on any failure.

Usage: python check_svg.py
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
NUM = r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?"


def fill_paths(svg):
    out = []
    for m in re.finditer(r'<path d="([^"]+)"([^>]*)>', svg):
        d, attrs = m.group(1), m.group(2)
        if 'fill="none"' in attrs or "fill=" not in attrs:
            continue
        subs = []
        for chunk in re.split(r"(?=M)", d):
            pts = [(float(a), float(b)) for a, b in re.findall(rf"({NUM})\s+({NUM})", chunk)]
            if len(pts) >= 3:
                subs.append(pts)
        out.append((attrs, subs))
    return out


def winding(pt, poly):
    """Nonzero winding number of a closed polygon around pt (y-down coordinates)."""
    wn, (x, y) = 0, pt
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        cross = (x1 - x0) * (y - y0) - (x - x0) * (y1 - y0)
        if y0 <= y < y1 and cross > 0:
            wn += 1
        elif y1 <= y < y0 and cross < 0:
            wn -= 1
    return wn


def inked(pt, paths):
    return any(sum(winding(pt, s) for s in subs) != 0 for _, subs in paths)


def main():
    fails = 0
    s = 1.024   # hero design units to SVG px
    hero = fill_paths(open(os.path.join(HERE, "hero-black.svg"), encoding="utf-8").read())
    # chip now at C + (60, -8) = (560, 740) design units, size 84, qubit pitch 0.235 * 84
    cx, cy, size = 560.0, 740.0, 84.0
    sp = 0.235 * size
    checks = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            checks.append(("hero qubit hole", (cx + i * sp, cy + j * sp), False))
    checks += [("hero chip body (between qubits)", (cx + sp / 2, cy + sp / 2), True),
               ("hero chip guard-ring gap", (cx - size / 2 + 0.0975 * size, cy), False),
               ("hero chip rim", (cx - size / 2 + 2, cy), True),
               ("hero dial interior", (500.0, 748.0 + 120), False),
               ("hero dial band", (500.0, 748.0 + 195), True),
               ("hero datum quadrant (top right, solid)", (504.0, 744.0), True),
               ("hero datum quadrant (top left, open)", (496.0, 744.0), False)]
    for name, (x, y), want in checks:
        got = inked((x * s, y * s), hero)
        ok = got == want
        fails += not ok
        print(f"{'ok ' if ok else 'FAIL'} {name}: inked={got}")

    for fname, pts in (("small.svg", [("ring interior", (16, 27), False), ("ring band", (16, 30), True),
                                      ("chip", (20, 16), True), ("between bracket and chip", (14, 16), False)]),
                       ("small-16.svg", [("ring interior", (8, 13.5), False), ("ring band", (8, 15.2), True),
                                         ("chip", (9.5, 8.5), True), ("left bracket bar", (3.5, 8), True)])):
        paths = [p for p in fill_paths(open(os.path.join(HERE, fname), encoding="utf-8").read())
                 if "#f2eee6" not in p[0].lower()]
        for name, pt, want in pts:
            got = inked(pt, paths)
            ok = got == want
            fails += not ok
            print(f"{'ok ' if ok else 'FAIL'} {fname} {name}: inked={got}")
    print("FAILURES:", fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

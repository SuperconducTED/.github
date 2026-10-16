"""Acceptance tests of ../history/candidates/MARK_API.md for the cutaway mark, measured on exported files.

  (a) Rebuild: runs build.py (neutral colours: ink #1A1D24, paper #F2EEE6, accent = ink) and
      compares hero.svg, hero-black.svg, small.svg, small-16.svg byte for byte, and hero-1024.png,
      hero-white-on-black.png, small-32.png, small-16.png, sheet.png pixel for pixel (decoded
      IDAT; VectorCraft PNGs embed a creation time, so their bytes always differ) against the
      committed copies in _work/orig/. Those copies are made by hand BEFORE any change; this
      script never writes them, and it stops if they are missing.
  (b) Accent: renders each variant twice, accent = ink and accent = #D9480F, plus a mask of the
      accent elements alone (black on transparent: every pixel with alpha > 0). Every pixel that
      differs must lie in the mask (strays = differing pixels outside it, which must be 0).
      Guards against a vacuous pass: the mask and the difference must be non-empty, some pixels
      must be exactly #D9480F, and a mutated drawing (the ink parts of the accent-bearing layers
      recoloured, which turns the drift dimension, the trail arrowhead and the small marks'
      chip and index accent) must produce strays.
  (c) Mono: draws each variant with mono=True and a distinct accent and checks the SVG: exactly
      one paint colour over every fill and stroke, no opacity attribute, no gradient, filter,
      image, text or other element besides svg, title, g and path. The hero must equal the
      committed hero-black.svg byte for byte. Guard: a mono=False render with the accent must
      fail the same check. The cutaway is line work, so the mono hero keeps its stroked paths
      (all in the one colour); the count is reported, not hidden.
  Then runs check_svg.py.

Usage: python -I check_api.py        (writes review renders into _work/, exits non-zero on failure)
"""
import os
import re
import struct
import subprocess
import sys
import time
import zlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(os.path.dirname(HERE), "tools"))
import mark  # noqa: E402
from build import BLACK, NEUTRAL  # noqa: E402
from vcdriver import VC, fresh_export  # noqa: E402

WORK = os.path.join(HERE, "_work")
ORIG = os.path.join(WORK, "orig")
SVGS = ["hero.svg", "hero-black.svg", "small.svg", "small-16.svg"]
PNGS = ["hero-1024.png", "hero-white-on-black.png", "small-32.png", "small-16.png", "sheet.png"]
ACCENT = "#D9480F"
# render size per variant for test (b): the hero at its 1024 px deliverable size, the small
# marks at their native pixel grids
SIZES = {"hero": 1024, "small": 32, "small16": 16}
FAILS = []


def report(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        FAILS.append(msg)


# ---------------------------------------------------------------- PNG pixels (stdlib only)


def pixels(path):
    """(width, height, bytes per pixel, raw unfiltered pixel bytes) of an 8-bit RGB/RGBA PNG."""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat = 8, b""
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0 and ctype in (2, 6), (path, depth, ctype, inter)
            bpp = 4 if ctype == 6 else 3
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    out, prev, i = bytearray(), bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if f:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b = prev[x]
                if f == 1:
                    line[x] = (line[x] + a) & 255
                elif f == 2:
                    line[x] = (line[x] + b) & 255
                elif f == 3:
                    line[x] = (line[x] + (a + b) // 2) & 255
                else:
                    c = prev[x - bpp] if x >= bpp else 0
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        out += line
        prev = line
    return w, h, bpp, bytes(out)


def rgb(img):
    """List of (r, g, b) per pixel."""
    w, h, bpp, px = img
    return [px[k:k + 3] for k in range(0, w * h * bpp, bpp)]


# ---------------------------------------------------------------- (a) rebuild


def test_rebuild():
    missing = [f for f in SVGS + PNGS if not os.path.exists(os.path.join(ORIG, f))]
    if missing:
        report(False, f"(a) _work/orig/ lacks {missing}: copy the committed files there before any change")
        return
    t0 = time.time_ns()
    run = subprocess.run([sys.executable, "-I", os.path.join(HERE, "build.py")], capture_output=True, text=True)
    report(run.returncode == 0, f"(a) build.py exit code {run.returncode} {run.stderr.strip()[-300:]}")
    # VectorCraft can report an export it never wrote (vcdriver.fresh_export); a stale file
    # would then pass the comparison below, so every deliverable must be newer than the rebuild
    stale = [f for f in SVGS + PNGS if os.stat(os.path.join(HERE, f)).st_mtime_ns < t0 - 1_000_000_000]
    report(not stale, f"(a) all {len(SVGS + PNGS)} deliverables rewritten by this rebuild {stale or ''}")
    same = 0
    for f in SVGS:
        ok = open(os.path.join(HERE, f), "rb").read() == open(os.path.join(ORIG, f), "rb").read()
        same += ok
        report(ok, f"(a) {f} byte-identical to the committed file")
    same_px = 0
    for f in PNGS:
        a, b = pixels(os.path.join(HERE, f)), pixels(os.path.join(ORIG, f))
        ok = a == b
        same_px += ok
        report(ok, f"(a) {f} {a[0]}x{a[1]} pixel-identical to the committed file")
    print(f"     (a) summary: {same}/{len(SVGS)} SVGs byte-identical, {same_px}/{len(PNGS)} PNGs pixel-identical")


# ---------------------------------------------------------------- (b) accent only on the range


def render(vc, name, size, draw, ground=None):
    vc.cmd("file.new", width=size, height=size, units="Pixels", name="SuperconducTED")
    if ground:
        vc.tool("draw_shape", shape="rectangle", x=0, y=0, width=size, height=size, fill=ground, stroke="none")
    draw()
    out = fresh_export(vc, os.path.join(WORK, name), **({"scale": 1} if name.endswith(".png") else {}))
    vc.cmd("file.close")
    return out


def mutated(art):
    """A copy of `art` in which every layer that carries an accent part also paints its ink
    parts in the accent: the deliberate mistake the stray count must catch."""
    m = mark.Art()
    for it in art.items:
        has_accent = any(r == "accent" for r, _ in it[1])
        parts = [("accent" if has_accent else r, pls) for r, pls in it[1]]
        m.items.append((it[0], parts) + tuple(it[2:]))
    return m


def strays(base, other, mask_alpha):
    diff = [k for k, (p, q) in enumerate(zip(base, other)) if p != q]
    return diff, [k for k in diff if mask_alpha[k] == 0]


def test_accent(vc):
    paper = NEUTRAL["paper"]
    accented = dict(NEUTRAL, accent=ACCENT)
    want = bytes(int(ACCENT[i:i + 2], 16) for i in (1, 3, 5))
    for variant, size in SIZES.items():
        s = size / mark.UNITS[variant]
        tag = "accent-demo" if variant == "hero" else f"accent-{variant}"
        f_base = render(vc, f"neutral-{variant}.png", size, lambda: mark.draw_mark(vc, 0, 0, size, NEUTRAL, variant), paper)
        f_acc = render(vc, f"{tag}.png", size, lambda: mark.draw_mark(vc, 0, 0, size, accented, variant), paper)
        f_mask = render(vc, f"mask-{variant}.png", size,
                        lambda: mark.emit(vc, mark.art(variant), 0, 0, s, {"ink": None, "accent": "#000000"}))
        f_mut = render(vc, f"mutation-{variant}.png", size,
                       lambda: mark.emit(vc, mutated(mark.art(variant)), 0, 0, s, mark.paint_for(accented)), paper)
        base, acc, mut = rgb(pixels(f_base)), rgb(pixels(f_acc)), rgb(pixels(f_mut))
        mw, mh, mbpp, mpx = pixels(f_mask)
        assert mbpp == 4, "the mask must be exported with transparency"
        alpha = mpx[3::4]
        n_mask = sum(1 for a in alpha if a)
        diff, out = strays(base, acc, alpha)
        n_exact = sum(1 for p in acc if p == want)
        mdiff, mout = strays(base, mut, alpha)
        print(f"     (b) {variant} at {size} px: {len(diff)} pixels differ, mask {n_mask} pixels, "
              f"{n_exact} pixels exactly {ACCENT}, strays {len(out)}; mutation: {len(mdiff)} differ, strays {len(mout)}")
        report(n_mask > 0 and len(diff) > 0 and n_exact > 0, f"(b) {variant}: mask, difference and pure-accent pixels are non-empty")
        report(not out, f"(b) {variant}: {len(out)} differing pixels outside the range mask")
        report(len(mout) > 0, f"(b) {variant}: the guard catches a mutation ({len(mout)} strays when the ink parts of the accent layers wear it)")
        if variant == "hero":
            ref = rgb(pixels(os.path.join(HERE, "hero-1024.png")))
            report(ref == base, "(b) the neutral hero render equals hero-1024.png pixel for pixel")


# ---------------------------------------------------------------- (c) mono is one colour

ALLOWED = {"svg", "title", "g", "path"}


def mono_check(svg):
    """(problems, paint colours, stroked path count) of an exported SVG."""
    paints = {v.lower() for v in re.findall(r'\b(?:fill|stroke)="([^"]+)"', svg) if v.lower() != "none"}
    tags = set(re.findall(r"<([a-zA-Z][\w:-]*)", svg)) - {"?xml"}
    problems = []
    if len(paints) != 1:
        problems.append(f"{len(paints)} paint colours {sorted(paints)}")
    if re.search(r"opacity", svg):
        problems.append("an opacity attribute")
    if tags - ALLOWED:
        problems.append(f"elements {sorted(tags - ALLOWED)}")
    stroked = len(re.findall(r'stroke="(?!none)[^"]+"', svg))
    return problems, paints, stroked


def test_mono(vc):
    distinct = {"ink": BLACK, "paper": "#FFFFFF", "accent": ACCENT}
    for variant in mark.VARIANTS:
        size = SIZES[variant]
        f = render(vc, f"mono-{variant}.svg", size, lambda: mark.draw_mark(vc, 0, 0, size, distinct, variant, mono=True))
        svg = open(f, encoding="utf-8").read()
        problems, paints, stroked = mono_check(svg)
        report(not problems, f"(c) {variant} mono: paints {sorted(paints)}, no opacity, only {sorted(ALLOWED)} "
                             f"{'' if not problems else problems}")
        print(f"     (c) {variant} mono: {stroked} stroked paths (in the one colour), "
              f"{len(re.findall('<path', svg)) - stroked} filled paths")
        if variant == "hero":
            ref = open(os.path.join(HERE, "hero-black.svg"), encoding="utf-8").read()
            report(svg == ref, "(c) hero mono with a distinct accent is byte-identical to hero-black.svg")
        g = render(vc, f"mono-guard-{variant}.svg", size, lambda: mark.draw_mark(vc, 0, 0, size, distinct, variant))
        gp, gpaints, _ = mono_check(open(g, encoding="utf-8").read())
        report(bool(gp), f"(c) {variant}: the guard rejects a mono=False render ({sorted(gpaints)})")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(WORK, exist_ok=True)
    test_rebuild()
    with VC(HERE) as vc:
        test_accent(vc)
        test_mono(vc)
    print("     box:", {v: tuple(round(c, 4) for c in mark.box(v)) for v in mark.VARIANTS})
    run = subprocess.run([sys.executable, "-I", os.path.join(HERE, "check_svg.py")], capture_output=True, text=True)
    last = run.stdout.strip().splitlines()[-1] if run.stdout.strip() else run.stderr.strip()
    report(run.returncode == 0, f"check_svg.py: {last}")
    print("FAILURES:", len(FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()

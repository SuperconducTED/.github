"""Acceptance checks for the radial candidate's mark API (../MARK_API.md).

Contract
--------
* Inputs: the committed deliverables in this folder (or the copies in _work/orig/, taken before
  the refactor, when that folder exists) and mark.py / build.py. Requires the VectorCraft CLI.
* Outputs: review renders and SVGs in _work/ (git-ignored): _work/rebuild/ (a full rebuild),
  _work/accent-demo.png and its zooms, _work/check/ (the test renders), and a printed report.
* Side effects: writes only inside _work/; never touches the committed files.
* Exit status: 0 when every check passes, 1 otherwise.

The checks
----------
(a) Rebuild: build.deliverables() into _work/rebuild/ with the neutral colours (accent = ink);
    every SVG must equal the committed one byte for byte, every PNG pixel for pixel (the PNGs
    carry a creation timestamp, so their IDAT is decoded and the RGBA pixels compared).
(b) Accent: each variant is rendered on paper with accent = ink and with accent #D9480F. Every
    pixel that differs must lie on the accent path (rendered alone, any coverage), and the
    differing pixels must cover most of that path (so the guard cannot pass vacuously). A forced
    split with accent = ink is compared with the merged drawing too: the split itself must not
    move any pixel except where an ink shape meets the accent (anti-aliasing seams).
    For the hero, an independent geometric guard: every differing pixel lies within the range's
    annular wedge (radius 228 to 327, bearings B_LO - 3 to B_HI + 3 degrees).
(c) Mono: draw_mark(mono=True) with a distinct accent must export one path, one fill colour, no
    stroke, no opacity and no paper-coloured shape; the same colours without mono must export
    two fills (guard).
(d) box(): the bounding box of the rendered art must match box(variant) to within one pixel.
"""
import math
import os
import re
import shutil
import struct
import sys
import zlib

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "tools")))
from vcdriver import VC, fresh_export  # noqa: E402
import build  # noqa: E402
import mark  # noqa: E402

INK, PAPER, ACCENT = build.INK, build.PAPER, "#D9480F"
WORK = os.path.join(HERE, "_work")
CHECK = os.path.join(WORK, "check")
REBUILD = os.path.join(WORK, "rebuild")
ORIG = os.path.join(WORK, "orig")
SVGS = ("hero.svg", "hero-black.svg", "small.svg")
PNGS = ("hero-1024.png", "hero-white-on-black.png", "small-32.png", "small-16.png", "sheet.png")
FAILS = []


def report(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


# ---------------------------------------------------------------- PNG pixels
def pixels(path):
    """Decode an 8-bit, non-interlaced RGB or RGBA PNG into (w, h, RGBA bytes)."""
    data = open(path, "rb").read()
    pos, idat, w, h, ct = 8, [], None, None, None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, bd, ct, _, _, il = struct.unpack(">IIBBBBB", body)
            assert bd == 8 and ct in (2, 6) and il == 0, (path, bd, ct, il)
        elif typ == b"IDAT":
            idat.append(body)
        pos += 12 + n
    bpp = 4 if ct == 6 else 3
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    out, prev, i = bytearray(), bytearray(stride), 0
    for _ in range(h):
        ft = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ft == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ft == 2:
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif ft == 3:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((a + prev[x]) >> 1)) & 255
        elif ft == 4:
            for x in range(stride):
                a = line[x - bpp] if x >= bpp else 0
                b, c = prev[x], (prev[x - bpp] if x >= bpp else 0)
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else c))) & 255
        prev = line
        if bpp == 4:
            out += line
        else:
            for x in range(w):
                out += line[3 * x:3 * x + 3] + b"\xff"
    return w, h, bytes(out)


def differing(p, q):
    """Indices of the pixels whose RGBA differ."""
    return [k for k in range(len(p) // 4) if p[4 * k:4 * k + 4] != q[4 * k:4 * k + 4]]


def covered(px):
    """Indices of the pixels with any alpha (the art on a transparent ground)."""
    return {k for k in range(len(px) // 4) if px[4 * k + 3]}


def dilate(ix, w, h, n=1):
    out = set(ix)
    for k in ix:
        x, y = k % w, k // w
        for dy in range(-n, n + 1):
            for dx in range(-n, n + 1):
                if 0 <= x + dx < w and 0 <= y + dy < h:
                    out.add((y + dy) * w + x + dx)
    return out


# ---------------------------------------------------------------- engine helpers
def doc(vc, w, h, name, ground=None):
    vc.cmd("file.new", width=w, height=h, units="Pixels", name=name)
    if ground:
        build.rect(vc, 0, 0, w, h, ground)


def export(vc, name, **args):
    path = fresh_export(vc, os.path.join(CHECK, name), **args)
    vc.cmd("file.close")
    return path


def svg_paths(path):
    svg = open(path, encoding="utf-8").read()
    return svg, re.findall(r"<path\b[^>]*>", svg)


# ---------------------------------------------------------------- (a) rebuild
def check_rebuild(vc):
    ref = ORIG if os.path.isdir(ORIG) else HERE
    print(f"\n(a) rebuild with the neutral colours into _work/rebuild, compared with {os.path.relpath(ref, HERE)}/")
    os.makedirs(REBUILD, exist_ok=True)
    for name in SVGS + PNGS:              # no stale file may stand in for a failed export
        if os.path.exists(os.path.join(REBUILD, name)):
            os.remove(os.path.join(REBUILD, name))
    build.deliverables(vc, REBUILD)
    for name in SVGS:
        new, old = open(os.path.join(REBUILD, name), "rb").read(), open(os.path.join(ref, name), "rb").read()
        live = open(os.path.join(HERE, name), "rb").read()
        report(new == old and live == old,
               f"{name}: {len(new)} bytes, byte-identical to the original: {new == old}; "
               f"committed file still the original: {live == old}")
    for name in PNGS:
        w1, h1, p1 = pixels(os.path.join(REBUILD, name))
        w0, h0, p0 = pixels(os.path.join(ref, name))
        same_bytes = open(os.path.join(REBUILD, name), "rb").read() == open(os.path.join(ref, name), "rb").read()
        nd = len(differing(p1, p0)) if (w1, h1) == (w0, h0) else -1
        report(nd == 0, f"{name}: {w1} x {h1}, differing pixels {nd} (file bytes identical: {same_bytes})")


# ---------------------------------------------------------------- (b) accent
SIZES = {"hero": (1000, 1), "small": (32, 8), "small16": (16, 8)}


def check_accent(vc):
    print("\n(b) the accent changes only the range")
    for variant, (size, mag) in SIZES.items():
        S = size * mag
        tag = f"{variant}-{S}"
        # merged (accent = ink), the test accent, a forced split with accent = ink, the accent alone
        doc(vc, S, S, "merged", PAPER)
        mark.draw_mark(vc, 0, 0, S, {"ink": INK, "paper": PAPER, "accent": INK}, variant)
        f_merged = export(vc, f"b-{tag}-merged.png", scale=1)
        doc(vc, S, S, "accent", PAPER)
        ids = mark.draw_mark(vc, 0, 0, S, {"ink": INK, "paper": PAPER, "accent": ACCENT}, variant)
        f_acc = export(vc, f"b-{tag}-accent.png", scale=1)
        doc(vc, S, S, "accent-svg")        # no ground, so the SVG holds only what draw_mark drew
        mark.draw_mark(vc, 0, 0, S, {"ink": INK, "paper": PAPER, "accent": ACCENT}, variant)
        f_svg = export(vc, f"b-{tag}-accent.svg")
        doc(vc, S, S, "split", PAPER)
        mark.draw_parts(vc, 0, 0, S, INK, INK, variant, split=True)
        f_split = export(vc, f"b-{tag}-split-ink.png", scale=1)
        doc(vc, S, S, "mask")
        ink_ids, acc_ids = mark.draw_parts(vc, 0, 0, S, INK, ACCENT, variant, split=True)
        vc.cmd("edit.clear", ids=ink_ids)
        f_mask = export(vc, f"b-{tag}-mask.png", scale=1)

        _, svg_tags = svg_paths(f_svg)
        fills = [re.search(r'fill="([^"]*)"', t).group(1).lower() for t in svg_tags]
        report(len(ids) == 2 and fills == [INK.lower(), ACCENT.lower()],
               f"{variant}: the accented export has {len(svg_tags)} paths, fills bottom to top {fills}")

        w, h, pm = pixels(f_merged)
        _, _, pa = pixels(f_acc)
        _, _, ps = pixels(f_split)
        _, _, pk = pixels(f_mask)
        mask = covered(pk)
        diff = differing(pm, pa)
        outside = [k for k in diff if k not in mask]
        near = dilate(mask, w, h) if outside else mask
        outside1 = [k for k in outside if k not in near]
        report(not outside, f"{variant} at {S} px: {len(diff)} pixels change with the accent; "
                            f"{len(outside)} of them off the accent path ({len(outside1)} beyond one pixel of it)")
        frac = len(set(diff) & mask) / max(1, len(mask))
        report(frac > 0.9, f"{variant}: the changed pixels cover {len(set(diff) & mask)} of the "
                           f"{len(mask)} accent-path pixels ({100 * frac:.1f}%)")
        seam = differing(pm, ps)
        where = ""
        if variant == "hero" and seam:
            rs = [math.hypot((k % w) + 0.5 - 500, (k // w) + 0.5 - 500) for k in seam]
            bs = [math.degrees(math.atan2((k % w) + 0.5 - 500, 500 - (k // w) - 0.5)) for k in seam]
            where = f" at radius {min(rs):.1f} to {max(rs):.1f}, bearing {min(bs):.1f} to {max(bs):.1f}"
            report(all(299 <= r <= 305 and 28 <= b <= 32 for r, b in zip(rs, bs)),
                   f"hero: the forced split (accent = ink) moves {len(seam)} pixels{where} "
                   f"(the rod at bearing 30 meets the arc at radius 302)")
        else:
            report(not seam, f"{variant}: the forced split (accent = ink) moves {len(seam)} pixels")
        if variant == "hero":
            bad = []
            for k in diff:
                x, y = (k % w) + 0.5, (k // w) + 0.5
                r = math.hypot(x - 500, y - 500)
                b = math.degrees(math.atan2(x - 500, 500 - y))
                if not (228 <= r <= 327 and mark.B_LO - 3 <= b <= mark.B_HI + 3):
                    bad.append(k)
            report(not bad, f"hero: {len(bad)} changed pixels outside the range's wedge "
                            f"(radius 228 to 327, bearing {mark.B_LO - 3:.0f} to {mark.B_HI + 3:.0f})")
    # review renders: the hero with the accent, a zoom on the rod junction and the ']', the small marks
    shutil.copyfile(os.path.join(CHECK, "b-hero-1000-accent.png"), os.path.join(WORK, "accent-demo.png"))
    z = 4.0
    doc(vc, 900, 900, "zoom", PAPER)
    mark.draw_mark(vc, 450 - 705 * z, 450 - 295 * z, 1000 * z, {"ink": INK, "paper": PAPER, "accent": ACCENT})
    fresh_export(vc, os.path.join(WORK, "accent-demo-zoom.png"), scale=1)
    vc.cmd("file.close")
    doc(vc, 104, 56, "smalls", PAPER)
    build.rect(vc, 52, 0, 52, 56, INK)
    for k, (ink, ground) in enumerate(((INK, PAPER), (PAPER, INK))):
        col = {"ink": ink, "paper": ground, "accent": ACCENT}
        mark.draw_mark(vc, 52 * k + 4, 4, 32, col, "small")
        mark.draw_mark(vc, 52 * k + 4, 38, 16, col, "small16")
        mark.draw_mark(vc, 52 * k + 26, 38, 16, col, "small")
    fresh_export(vc, os.path.join(CHECK, "smalls.png"), scale=1)
    vc.cmd("file.close")
    build.magnify(os.path.join(CHECK, "smalls.png"), os.path.join(WORK, "accent-demo-small.png"), 8)


# ---------------------------------------------------------------- (c) mono
def check_mono(vc):
    print("\n(c) mono: one colour, no strokes, no opacity, no paper")
    distinct = {"ink": INK, "paper": PAPER, "accent": ACCENT}
    for variant, (size, _) in SIZES.items():
        doc(vc, size, size, "mono")
        mark.draw_mark(vc, 0, 0, size, distinct, variant, mono=True)
        svg, tags = svg_paths(export(vc, f"c-{variant}-mono.svg"))
        body = svg.split("<g", 1)[1]
        fills = {m.lower() for m in re.findall(r'fill="([^"]*)"', body)}
        strokes = [m for m in re.findall(r'stroke="([^"]*)"', body) if m.lower() != "none"]
        shapes = re.findall(r"<(rect|circle|ellipse|line|polyline|polygon|text|image|use)\b", body)
        ok = (len(tags) == 1 and fills == {INK.lower()} and not strokes and "opacity" not in svg
              and "stroke-width" not in body and not shapes and PAPER.lower() not in svg.lower())
        report(ok, f"{variant}: {len(tags)} path, fills {sorted(fills)}, strokes {strokes}, "
                   f"opacity attributes {svg.count('opacity')}, other shapes {shapes}")
        doc(vc, size, size, "guard")
        mark.draw_mark(vc, 0, 0, size, distinct, variant)
        svg, tags = svg_paths(export(vc, f"c-{variant}-guard.svg"))
        fills = sorted({m.lower() for m in re.findall(r'fill="([^"]*)"', svg.split("<g", 1)[1])})
        report(fills == sorted({INK.lower(), ACCENT.lower()}),
               f"{variant}: guard, the same colours without mono export fills {fills}")


# ---------------------------------------------------------------- (d) box
def check_box(vc):
    print("\n(d) box() against the rendered art")
    for variant, (size, mag) in SIZES.items():
        S = size * mag
        doc(vc, S, S, "box")
        mark.draw_mark(vc, 0, 0, S, {"ink": INK, "paper": PAPER, "accent": INK}, variant)
        w, h, px = pixels(export(vc, f"d-{variant}.png", scale=1))
        cov = covered(px)
        xs, ys = [k % w for k in cov], [k // w for k in cov]
        got = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
        want = tuple(v * S for v in mark.box(variant))
        report(all(abs(a - b) <= 1 for a, b in zip(got, want)),
               f"{variant} at {S} px: art spans {got}, box() says {tuple(round(v, 2) for v in want)}")


def main():
    os.makedirs(CHECK, exist_ok=True)
    stages = sys.argv[1:] or ["a", "b", "c", "d"]
    with VC(HERE) as vc:
        if "a" in stages:
            check_rebuild(vc)
        if "b" in stages:
            check_accent(vc)
        if "c" in stages:
            check_mono(vc)
        if "d" in stages:
            check_box(vc)
    print(f"\n{'ALL PASS' if not FAILS else f'{len(FAILS)} FAILED'}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()

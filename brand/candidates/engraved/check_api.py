"""Acceptance checks for the engraved candidate's mark API (../MARK_API.md).

Usage (from the repository root or anywhere; standard library only):
    python -I brand/candidates/engraved/check_api.py [--no-build]

What it proves, with numbers:
  (a) build.py, drawing everything through mark.draw_mark with the neutral palette (accent =
      ink), reproduces the committed hero.svg, hero-black.svg and small.svg byte for byte and
      every committed PNG pixel for pixel. The reference copies live in work/orig/; when that
      folder is missing, the files present before this run are copied there first (delete it
      to re-baseline). PNGs are compared as decoded pixels, because VectorCraft PNGs can embed
      a timestamp; when every PNG is pixel-identical, the committed bytes are copied back.
  (b) With accent #D9480F only the range changes colour: the hero (and the small mark) are
      rendered with accent = ink and with the test accent, and every differing pixel must lie
      inside a mask rendered from the accent elements alone (alpha > 0 on a transparent
      document). A planted accent square outside the range must be caught (the guard is not
      vacuous).
  (c) mono=True output paints in a single colour, the ink, for fills and strokes alike, with
      no opacity and no paper-coloured shapes (MARK_API.md test 3 as amended 2026-10-16: the
      engraving keeps its strokes), checked on exported SVGs of the hero and the small mark
      drawn with a palette whose paper and accent differ from the ink. The same checker must
      reject the committed two-colour hero.svg and small.svg and a non-mono accent export,
      and accept the committed hero-black.svg, which build.py now draws with mono=True.
  plus: box() matches the art's measured extent, the first hero draw_mark inside an open
  document (the lazy lettering path) renders pixel-identical to the committed hero-1024.png,
  and nothing outside this folder is written (acceptance 4). Other agents edit sibling
  folders concurrently, so a before/after snapshot of the repository cannot attribute changes;
  instead an audit hook records every file this process opens for writing, creates, removes,
  renames or copies (the build runs in-process, so its writes are recorded too), and every
  VectorCraft engine it starts must have this folder as its write root (the engine refuses
  writes outside that root).

Side effects: rebuilds this folder's deliverables (unless --no-build) and writes review renders
to work/: accent-demo.png (hero with accent #D9480F), accent-neutral.png, accent-mask.png,
accent-demo-small.png, accent-planted.png, accent-demo.svg, hero-mono.png, mono-hero.svg,
mono-small.svg. Exit status 1 on any failure.
"""
import os
import re
import shutil
import struct
import subprocess
import sys
import zlib

sys.dont_write_bytecode = True        # nothing outside this folder may change
HERE = os.path.dirname(os.path.abspath(__file__))

WRITES, ENGINES = [], []
_W_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
_W_EVENTS = {"os.remove": (0,), "os.rename": (0, 1), "os.replace": (0, 1), "os.mkdir": (0,),
             "os.rmdir": (0,), "os.truncate": (0,), "os.chmod": (0,), "os.utime": (0,),
             "os.symlink": (1,), "os.link": (1,), "shutil.copyfile": (1,), "shutil.copymode": (1,),
             "shutil.copystat": (1,), "shutil.copytree": (1,), "shutil.rmtree": (0,)}


def _audit(event, args):
    """Record every filesystem write of this process and every engine it starts."""
    if event == "open":
        path, _, flags = args
        if isinstance(path, (str, bytes)) and flags & _W_FLAGS:
            WRITES.append(os.path.abspath(os.fsdecode(path)))
    elif event in _W_EVENTS:
        for k in _W_EVENTS[event]:
            if isinstance(args[k], (str, bytes, os.PathLike)):
                WRITES.append(os.path.abspath(os.fsdecode(args[k])))
    elif event == "subprocess.Popen":
        ENGINES.append(list(args[1]) if isinstance(args[1], (list, tuple)) else [args[1]])


sys.addaudithook(_audit)
TOOLS = os.path.abspath(os.path.join(HERE, "..", "..", "tools"))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
from vcdriver import VC, fresh_export  # noqa: E402
import mark  # noqa: E402

WORK = os.path.join(HERE, "work")
ORIG = os.path.join(WORK, "orig")
INK, PAPER = "#1A1D24", "#F2EEE6"
NEUTRAL = {"ink": INK, "paper": PAPER, "accent": INK}
TEST_ACCENT = "#D9480F"
SVGS = ("hero.svg", "hero-black.svg", "small.svg")
PNGS = ("hero-1024.png", "hero-white-on-black.png", "small-32.png", "small-16.png", "sheet.png")

FAILS = []


def report(ok, msg):
    print(("PASS  " if ok else "FAIL  ") + msg)
    if not ok:
        FAILS.append(msg)


# ----------------------------------------------------------------------------------------
# PNG decoding (8-bit, non-interlaced greyscale, RGB, grey+alpha or RGBA), standard library
# ----------------------------------------------------------------------------------------
def read_png(path):
    """Return (width, height, channels, pixel bytes row-major) of an 8-bit PNG."""
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    pos, idat, ihdr = 8, [], None
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        typ, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif typ == b"IDAT":
            idat.append(body)
        elif typ == b"IEND":
            break
        pos += 12 + n
    w, h, depth, ctype, _, _, interlace = ihdr
    if depth != 8 or interlace != 0 or ctype not in (0, 2, 4, 6):
        raise ValueError(f"{path}: unsupported PNG (depth {depth}, colour type {ctype}, interlace {interlace})")
    bpp = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(b"".join(idat))
    stride = w * bpp
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        ft = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if ft == 1:                                    # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:                                  # Up
            line = bytearray((a + b) & 255 for a, b in zip(line, prev))
        elif ft == 3:                                  # Average
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:                                  # Paeth
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        elif ft != 0:
            raise ValueError(f"{path}: bad filter type {ft} in row {y}")
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return w, h, bpp, bytes(out)


def diff_pixels(a, b):
    """Indices of pixels that differ between two decoded PNGs of the same size and layout."""
    (wa, ha, ca, pa), (wb, hb, cb, pb) = a, b
    if (wa, ha, ca) != (wb, hb, cb):
        raise ValueError(f"layouts differ: {(wa, ha, ca)} vs {(wb, hb, cb)}")
    if pa == pb:
        return []
    return [i for i in range(wa * ha) if pa[i * ca:(i + 1) * ca] != pb[i * cb:(i + 1) * cb]]


def alpha_mask(img):
    w, h, c, px = img
    if c not in (2, 4):
        raise ValueError("mask render has no alpha channel")
    return {i for i in range(w * h) if px[i * c + c - 1] > 0}


# ----------------------------------------------------------------------------------------
# (a) rebuild and compare with the committed files
# ----------------------------------------------------------------------------------------
def test_a(build):
    if not os.path.isdir(ORIG):
        os.makedirs(ORIG)
        for f in SVGS + PNGS:
            shutil.copy2(os.path.join(HERE, f), os.path.join(ORIG, f))
        print(f"note  work/orig was missing: copied the {len(SVGS) + len(PNGS)} files present before this run")
    if build:
        # in-process, so the audit hook sees the build's writes too; `python -I build.py all`
        # runs exactly this main()
        import build as build_script
        argv, sys.argv = sys.argv, [os.path.join(HERE, "build.py"), "all"]
        try:
            build_script.main()
        finally:
            sys.argv = argv
        mark._HERO_CACHE.clear()      # so (b) exercises the lazy lettering path again
    same_svg = [f for f in SVGS if open(os.path.join(HERE, f), "rb").read() == open(os.path.join(ORIG, f), "rb").read()]
    report(len(same_svg) == len(SVGS), f"(a) {len(same_svg)}/{len(SVGS)} SVGs byte-identical to work/orig "
                                      f"({', '.join(f for f in SVGS if f not in same_svg) or 'none differ'})")
    same_png, same_bytes, details = 0, 0, []
    for f in PNGS:
        new, old = read_png(os.path.join(HERE, f)), read_png(os.path.join(ORIG, f))
        d = diff_pixels(new, old)
        same_png += not d
        same_bytes += open(os.path.join(HERE, f), "rb").read() == open(os.path.join(ORIG, f), "rb").read()
        details.append(f"{f} {new[0]}x{new[1]}x{new[2]} {len(d)} px differ")
    report(same_png == len(PNGS), f"(a) {same_png}/{len(PNGS)} PNGs pixel-identical ({'; '.join(details)}); "
                                  f"{same_bytes}/{len(PNGS)} also byte-identical")
    if same_png == len(PNGS) and same_bytes < len(PNGS):
        # same pixels, new embedded timestamp: put the committed bytes back so the check leaves
        # no byte-only change in the working tree
        for f in PNGS:
            shutil.copy2(os.path.join(ORIG, f), os.path.join(HERE, f))
        print(f"note  restored the committed bytes of the {len(PNGS)} pixel-identical PNGs from work/orig")


# ----------------------------------------------------------------------------------------
# rendering helpers for (b) and (c)
# ----------------------------------------------------------------------------------------
def render(vc, name, size, ground, draw, svg=False):
    """New document `size` square; optional ground rect; draw(vc); export to work/name."""
    vc.cmd("file.new", width=size, height=size, units="Pixels", name=os.path.splitext(name)[0])
    if ground:
        vc.tool("draw_shape", shape="rectangle", x=0, y=0, width=size, height=size, fill=ground, stroke="none")
    ids = draw(vc)
    path = os.path.join(WORK, name)
    fresh_export(vc, path, **({"format": "svg", "outlineText": True} if svg else {}))
    vc.cmd("file.close")
    return path, ids


def accent_test(vc, variant, size, tag):
    """Render neutral, accent and accent-only mask; return (diff count, mask count, strays)."""
    pal = dict(NEUTRAL, accent=TEST_ACCENT)
    n_path, _ = render(vc, f"accent-neutral{tag}.png", size, PAPER,
                       lambda v: mark.draw_mark(v, 0, 0, size, NEUTRAL, variant))
    a_path, _ = render(vc, f"accent-demo{tag}.png", size, PAPER,
                       lambda v: mark.draw_mark(v, 0, 0, size, pal, variant))
    m_path, _ = render(vc, f"accent-mask{tag}.png", size, None,
                       lambda v: mark._draw(v, 0, 0, size, pal, variant, roles=("accent",)))
    neutral_img, accent_img = read_png(n_path), read_png(a_path)
    diff = diff_pixels(neutral_img, accent_img)
    mask = alpha_mask(read_png(m_path))
    strays = [i for i in diff if i not in mask]
    return neutral_img, diff, mask, strays


def paints(text):
    """The distinct fill and stroke colours of an SVG (lower case, 'none' left out)."""
    return set(v.lower() for v in re.findall(r'\b(?:fill|stroke)="([^"]+)"', text)) - {"none"}


def svg_mono_problems(text, ink=None, paper=None):
    """Every way an SVG breaks the mono rule (MARK_API.md test 3, amended 2026-10-16): more or
    fewer than one paint colour across fills and strokes, a colour other than the ink, any
    paper-coloured shape, any opacity, any gradient, pattern, filter, mask, image or rgba.
    Strokes in the one colour are allowed."""
    probs = []
    cols = paints(text)
    if len(cols) != 1:
        probs.append(f"{len(cols)} paint colours {sorted(cols)}")
    if ink and cols and cols != {ink.lower()}:
        probs.append(f"paints {sorted(cols)}, not only the ink {ink.lower()}")
    if paper and paper.lower() in cols:
        probs.append("paper-coloured shapes")
    if re.search(r'opacity', text, re.I):
        probs.append("opacity")
    if re.search(r'<(linearGradient|radialGradient|pattern|filter|mask|image)\b|rgba\(', text):
        probs.append("gradient, pattern, filter, mask, image or rgba")
    if not re.search(r'<path\b[^>]*\b(?:fill|stroke)="#', text):
        probs.append("no painted path at all")
    return probs


# ----------------------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------------------
def main():
    build = "--no-build" not in sys.argv[1:]
    os.makedirs(WORK, exist_ok=True)
    probe = os.path.join(WORK, "audit-probe.txt")       # proves the audit hook is live
    with open(probe, "w", encoding="utf-8") as f:
        f.write("written by check_api.py to prove the audit hook records writes" + os.linesep)
    hook_live = os.path.abspath(probe) in WRITES
    test_a(build)

    with VC(HERE) as vc:
        # (b) the accent goes only on the range. The first hero draw_mark of this process runs
        # inside an open document, so it also exercises the lazy lettering path.
        neutral_img, diff, mask, strays = accent_test(vc, "hero", 1024, "")
        committed = read_png(os.path.join(ORIG, "hero-1024.png"))
        lazy = diff_pixels(neutral_img, committed)
        report(not lazy, f"lazy path: hero drawn inside an open document matches committed hero-1024.png "
                         f"({len(lazy)} px differ)")
        report(len(diff) > 0 and len(mask) > 0 and not strays,
               f"(b) hero, accent {TEST_ACCENT}: {len(diff)} px changed, mask {len(mask)} px, "
               f"{len(strays)} stray px outside the brackets and dial interval")
        _, sdiff, smask, sstrays = accent_test(vc, "small", 256, "-small")
        report(len(sdiff) > 0 and len(smask) > 0 and not sstrays,
               f"(b) small at 256 px, accent {TEST_ACCENT}: {len(sdiff)} px changed, mask {len(smask)} px, "
               f"{len(sstrays)} stray px outside the brackets")
        # non-vacuity: plant an accent square on the chip die (ink) and expect strays
        pal = dict(NEUTRAL, accent=TEST_ACCENT)

        def planted(v):
            mark.draw_mark(v, 0, 0, 1024, pal)
            c = mark.chip_centre(20.0)
            v.tool("draw_shape", shape="rectangle", x=c[0] * 1.024 - 8, y=c[1] * 1.024 - 8, width=16,
                   height=16, fill=TEST_ACCENT, stroke="none")
        p_path, _ = render(vc, "accent-planted.png", 1024, PAPER, planted)
        pdiff = diff_pixels(neutral_img, read_png(p_path))
        pstrays = [i for i in pdiff if i not in mask]
        report(len(pstrays) > 0, f"(b) guard catches a planted accent square on the chip: {len(pstrays)} stray px")

        # (c) mono: one paint colour for fills and strokes alike, no opacity, no paper shapes.
        # The palette's accent and paper are distinct, so a leak of either would show.
        mono_pal = {"ink": "#123456", "paper": PAPER, "accent": TEST_ACCENT}
        for variant, size in (("hero", 1024), ("small", 32)):
            path, ids = render(vc, f"mono-{variant}.svg", size, None,
                               lambda v, var=variant, sz=size: mark.draw_mark(v, 0, 0, sz, mono_pal, var, mono=True),
                               svg=True)
            text = open(path, encoding="utf-8").read()
            probs = svg_mono_problems(text, mono_pal["ink"], mono_pal["paper"])
            n_fill = len(re.findall(r'<path\b[^>]*\bfill="#', text))
            n_stroke = len(re.findall(r'<path\b[^>]*\bstroke="#', text))
            report(not probs, f"(c) mono {variant}: {n_fill} filled + {n_stroke} stroked paths, paint colours "
                              f"{sorted(paints(text))}, {len(ids)} ids returned, problems: {probs or 'none'}")
        # the checker is not vacuous: it rejects two-colour files and an accent leak
        a_svg, _ = render(vc, "accent-demo.svg", 1024, None,
                          lambda v: mark.draw_mark(v, 0, 0, 1024, mono_pal, "hero"), svg=True)
        for name, path in (("committed hero.svg", os.path.join(HERE, "hero.svg")),
                           ("committed small.svg", os.path.join(HERE, "small.svg")),
                           ("non-mono hero with accent (work/accent-demo.svg)", a_svg)):
            probs = svg_mono_problems(open(path, encoding="utf-8").read())
            report(bool(probs), f"(c) checker rejects the {name}: {probs}")
        probs = svg_mono_problems(open(os.path.join(HERE, "hero-black.svg"), encoding="utf-8").read(), "#000000")
        report(not probs, f"(c) committed hero-black.svg (built with mono=True) passes the checker: {probs or 'no problems'}")
        # for the hero, mono with accent = ink changes nothing (it paints no paper)
        m_path, _ = render(vc, "hero-mono.png", 1024, PAPER,
                           lambda v: mark.draw_mark(v, 0, 0, 1024, NEUTRAL, mono=True))
        mdiff = diff_pixels(neutral_img, read_png(m_path))
        report(not mdiff, f"(c) mono hero with the neutral ink vs the neutral render: {len(mdiff)} px differ")

        # box(): the measured extent of the geometry
        art = mark.hero_art(vc)[0]
        xs = [x - w / 2 for w, pts in art.lines for x, _ in pts] + [x for g in art.fills for c in g for _, ps in c for x, _ in ps]
        xe = [x + w / 2 for w, pts in art.lines for x, _ in pts] + [x for g in art.fills for c in g for _, ps in c for x, _ in ps]
        ys = [y - w / 2 for w, pts in art.lines for _, y in pts] + [y for g in art.fills for c in g for _, ps in c for _, y in ps]
        ye = [y + w / 2 for w, pts in art.lines for _, y in pts] + [y for g in art.fills for c in g for _, ps in c for _, y in ps]
        hero_ext = tuple(v / mark.HERO_UNITS for v in (min(xs), min(ys), max(xe), max(ye)))
        sart = mark.small_art()
        spts = [p for g in sart.fills for c in g for _, ps in c for p in ps]
        small_ext = tuple(v / mark.SMALL_UNITS for v in (min(p[0] for p in spts), min(p[1] for p in spts),
                                                         max(p[0] for p in spts), max(p[1] for p in spts)))
        for variant, ext in (("hero", hero_ext), ("small", small_ext)):
            b = mark.box(variant)
            err = max(abs(u - v) for u, v in zip(b, ext))
            report(err < 1e-6, f"box('{variant}') = {tuple(round(v, 6) for v in b)}, measured "
                               f"{tuple(round(v, 6) for v in ext)} (max error {err:.2g})")

    inside = os.path.normcase(HERE) + os.sep
    outside = sorted(set(p for p in WRITES if not os.path.normcase(p).startswith(inside)))
    roots = []
    for cmd in ENGINES:
        # on Windows the audit event carries the joined command line, quoted only where needed
        line = cmd[0] if len(cmd) == 1 and isinstance(cmd[0], str) else subprocess.list2cmdline(cmd)
        m = re.search(r'--automation-write-root\s+(?:"([^"]*)"|(\S+))', line)
        if m:
            roots.append(m.group(1) or m.group(2))
    bad_roots = [r for r in roots if os.path.normcase(os.path.abspath(r)) != os.path.normcase(HERE)]
    report(hook_live and not outside and not bad_roots and len(roots) == len(ENGINES) > 0,
           f"(4) {len(WRITES)} file writes by this run, {len(outside)} outside "
           f"{os.path.relpath(HERE, REPO)} {outside[:10]}; {len(ENGINES)} VectorCraft engines started, "
           f"{len(roots) - len(bad_roots)} with this folder as write root; audit hook live: {hook_live}")
    print("\nall checks passed" if not FAILS else f"\n{len(FAILS)} check(s) FAILED")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()

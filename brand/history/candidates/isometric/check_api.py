"""Acceptance checks for the isometric candidate's mark API (brand/history/candidates/MARK_API.md).

Usage (from this folder):  python -I check_api.py [--no-build] [reference_folder]

reference_folder (default _work/orig) holds the files as they were before the rebuild:
hero.svg, hero-black.svg, small.svg, hero-1024.png, hero-white-on-black.png, small-32.png,
small-16.png, sheet.png. Copy them there before the first rebuild (or check them out of git).

Checks
------
(a) Rebuild (python -I build.py, unless --no-build), then: every SVG byte-identical to the
    reference, every PNG pixel-identical (IHDR, palette and unfiltered pixel rows compared;
    VectorCraft PNGs embed a timestamp, so their bytes differ).
(b) Accent: the hero drawn twice through draw_mark at the hero-1024 layout, accent = ink and
    accent = #D9480F. Every differing pixel must lie on the footprint of the range: the [ , the ]
    and the zone, each rendered alone in black on white (footprint = any pixel that is not
    pure white). Non-vacuous: thousands of differing pixels, and each of the three pieces must
    hold some of them. Also writes _work/accent-demo.png for review.
(c) Mono: hero-black.svg, small.svg, and draw_mark(mono=True) with white ink for both variants
    (the one path where the knockout sentinel flips to black) each paint in exactly one colour
    (fills and strokes alike), with no opacity and no paper-coloured shapes.
(d) Nothing outside this folder is written: the build runs in this process under an audit hook
    that records every file opened for writing, removed, renamed or created, and every path
    VectorCraft is asked to export or save (the engine itself is also confined to this folder by
    vcdriver's --automation-write-root). Every recorded path must lie inside this folder. A
    before/after listing of brand/ is printed too, for information only: other candidates' agents
    may be editing their own folders at the same time, so it cannot attribute a change.
Exit status 0 when every check passes.
"""
import os
import re
import struct
import sys
import zlib

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "_work")
BRAND = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(BRAND, "tools"))
sys.path.insert(0, HERE)
from vcdriver import VC, fresh_export  # noqa: E402
import mark  # noqa: E402

SVGS = ("hero.svg", "hero-black.svg", "small.svg")
PNGS = ("hero-1024.png", "hero-white-on-black.png", "small-32.png", "small-16.png", "sheet.png")
TEST_ACCENT = "#D9480F"
HERO, SQUARE = 1024, (70, 70, 884)        # the hero-1024 layout of build.py


# ----------------------------------------------------------------------------------------
# PNG decoding (standard library only)
# ----------------------------------------------------------------------------------------
def png_read(path):
    """(IHDR tuple, PLTE bytes or None, filtered image bytes) of a non-interlaced PNG."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    pos, ihdr, plte, idat = 8, None, None, []
    while pos < len(data):
        n = struct.unpack(">I", data[pos:pos + 4])[0]
        kind, body = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = body
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if ihdr[6] != 0:
        raise ValueError(f"{path}: interlaced PNGs are not handled")
    return ihdr, plte, zlib.decompress(b"".join(idat))


def unfilter(ihdr, raw):
    """The image rows with the PNG filters undone, as one bytes object."""
    w, h, depth, ctype = ihdr[:4]
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    bpp = max(1, channels * depth // 8)
    stride = (w * channels * depth + 7) // 8
    out, prev, pos = bytearray(), bytearray(stride), 0
    for _ in range(h):
        ft, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + stride])
        pos += 1 + stride
        if ft == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 255
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ft == 3:
            for i in range(stride):
                left = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        elif ft != 0:
            raise ValueError(f"unknown PNG filter {ft}")
        out += line
        prev = line
    return bytes(out)


def rgba(path):
    """(width, height, RGBA bytes) of an 8-bit RGB or RGBA PNG."""
    ihdr, _, raw = png_read(path)
    w, h, depth, ctype = ihdr[:4]
    px = unfilter(ihdr, raw)
    if depth != 8 or ctype not in (2, 6):
        raise ValueError(f"{path}: only 8-bit RGB or RGBA is handled here")
    if ctype == 2:
        px = b"".join(px[i:i + 3] + b"\xff" for i in range(0, len(px), 3))
    return w, h, px


def same_pixels(a, b):
    """(identical?, how it was decided) for two PNG files."""
    ia, pa, ra = png_read(a)
    ib, pb, rb = png_read(b)
    if ia != ib or pa != pb:
        return False, f"header differs {ia} vs {ib}"
    if ra == rb:
        return True, "filtered rows identical"
    ua, ub = unfilter(ia, ra), unfilter(ib, rb)
    if ua == ub:
        return True, "pixels identical after unfiltering"
    n = sum(1 for x, y in zip(ua, ub) if x != y)
    return False, f"{n} bytes of pixel data differ"


# ----------------------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------------------
def snapshot():
    """(path -> (size, mtime_ns)) for every file under brand/ outside this folder."""
    snap = {}
    for root, dirs, files in os.walk(BRAND):
        if os.path.abspath(root).startswith(HERE):
            dirs[:] = []
            continue
        for f in files:
            p = os.path.join(root, f)
            st = os.stat(p)
            snap[p] = (st.st_size, st.st_mtime_ns)
    return snap


WRITES = []           # every path this process writes, or asks VectorCraft to write


def _audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        flags = args[2] if isinstance(args[2], int) else 0
        mode = args[1] if isinstance(args[1], str) else ""
        wmask = os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
        if flags & wmask or any(ch in mode for ch in "wax+"):
            WRITES.append(os.fsdecode(args[0]))
    elif event in ("os.remove", "os.rmdir", "os.mkdir", "os.truncate", "os.chmod", "os.utime"):
        if isinstance(args[0], (str, bytes, os.PathLike)):
            WRITES.append(os.fsdecode(args[0]))
    elif event in ("os.rename", "shutil.copyfile", "shutil.move", "shutil.rmtree"):
        WRITES.extend(os.fsdecode(a) for a in args[:2] if isinstance(a, (str, bytes, os.PathLike)))


def start_write_audit():
    """Record every write of this process (sys.addaudithook) and every path handed to
    VectorCraft's export and save calls (a wrapper around VC.tool)."""
    sys.addaudithook(_audit)
    plain = VC.tool

    def tool(self, name, **args):
        if name in ("export", "save_file") and "path" in args:
            WRITES.append(args["path"])
        if name == "run_command" and re.search(r"export|save", args.get("command", ""))                 and "path" in args.get("params", {}):
            WRITES.append(args["params"]["path"])
        return plain(self, name, **args)
    VC.tool = tool


def inside(path, folder):
    path, folder = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
    return os.path.commonpath([path, folder]) == folder


def check_rebuild(ref):
    ok = True
    for name in SVGS:
        same = open(os.path.join(HERE, name), "rb").read() == open(os.path.join(ref, name), "rb").read()
        size = os.path.getsize(os.path.join(HERE, name))
        print(f"  {name:26s} {size:8d} bytes  {'byte-identical' if same else 'DIFFERS'}")
        ok &= same
    for name in PNGS:
        same, how = same_pixels(os.path.join(HERE, name), os.path.join(ref, name))
        w, h = png_read(os.path.join(HERE, name))[0][:2]
        print(f"  {name:26s} {w}x{h:<6d}      {'pixel-identical' if same else 'DIFFERS'} ({how})")
        ok &= same
    return ok


def render(vc, path, ground, draw):
    vc.cmd("file.new", width=HERO, height=HERO, units="Pixels", name="check")
    vc.tool("draw_shape", shape="rectangle", x=0, y=0, width=HERO, height=HERO, fill=ground, stroke="none")
    draw()
    fresh_export(vc, path)
    vc.cmd("file.close")


def check_accent(vc):
    neutral = dict(mark.NEUTRAL)
    accent = dict(mark.NEUTRAL, accent=TEST_ACCENT)
    p_neu, p_acc = os.path.join(WORK, "accent-off.png"), os.path.join(WORK, "accent-on.png")
    render(vc, p_neu, mark.PAPER, lambda: mark.draw_mark(vc, *SQUARE, neutral))
    render(vc, p_acc, mark.PAPER, lambda: mark.draw_mark(vc, *SQUARE, accent))
    # visible footprints: the whole hero in painter's order, one range piece black, all else white
    S, ox, oy = mark.transform("hero", *SQUARE)
    hero = mark.art("hero")
    pal = {0: "#FFFFFF", 3: "#000000"}
    masks = {}
    for part in ("[", "]", "zone"):
        probe = [dict(p, tone=3 if p.get("acc") == part else 0, acc=None) for p in hero]
        path = os.path.join(WORK, f"accent-mask-{ {'[': 'left', ']': 'right', 'zone': 'zone'}[part] }.png")
        render(vc, path, "#FFFFFF", lambda: mark.emit(vc, mark.steps_for(probe, S, ox, oy, pal)))
        w, h, px = rgba(path)
        masks[part] = {i for i in range(w * h) if px[4 * i:4 * i + 3] != b"\xff\xff\xff"}
        n = sum(1 for p in hero if p.get("acc") == part)
        print(f"  visible footprint {part:5s} {n:3d} primitives, {len(masks[part]):6d} pixels")
    w, h, a = rgba(p_neu)
    _, _, b = rgba(p_acc)
    diff = [i for i in range(w * h) if a[4 * i:4 * i + 4] != b[4 * i:4 * i + 4]]
    union = set().union(*masks.values())
    outside = [i for i in diff if i not in union]
    per = {k: sum(1 for i in diff if i in m) for k, m in masks.items()}
    acc_px = sum(1 for i in range(w * h) if b[4 * i:4 * i + 3] == bytes.fromhex(TEST_ACCENT[1:]))
    print(f"  differing pixels {len(diff)}; on [ {per['[']}, on ] {per[']']}, on zone {per['zone']}; "
          f"outside the range footprint {len(outside)}")
    print(f"  pixels exactly {TEST_ACCENT} in the accent render: {acc_px}")
    if outside:
        print("  first outside pixels (x, y):", [(i % w, i // w) for i in outside[:10]])
    return not outside and len(diff) > 1000 and all(v > 0 for v in per.values()) and acc_px > 0


def svg_paints(text):
    """The set of colours painted (fill and stroke values other than none), lowercased."""
    vals = re.findall(r'(?:fill|stroke)="([^"]+)"', text) + re.findall(r'(?:fill|stroke)\s*:\s*([^;"]+)', text)
    return {v.strip().lower() for v in vals if v.strip().lower() != "none"}


def mono_ok(label, text, ink, paper):
    paints = svg_paints(text)
    strokes = len(re.findall(r'stroke="(?!none)', text))
    ok = paints == {ink.lower()} and "opacity" not in text and paper.lower() not in paints
    print(f"  {label:34s} paints {sorted(paints)}, strokes {strokes}, opacity {'opacity' in text}, "
          f"paths {text.count('<path')}  {'ok' if ok else 'FAIL'}")
    return ok


def check_mono(vc):
    ok = mono_ok("hero-black.svg", open(os.path.join(HERE, "hero-black.svg"), encoding="utf-8").read(), "#000000", "#FFFFFF")
    ok &= mono_ok("small.svg", open(os.path.join(HERE, "small.svg"), encoding="utf-8").read(), mark.INK, mark.PAPER)
    white = {"ink": "#FFFFFF", "paper": "#000000", "accent": "#FFFFFF"}
    for variant, size in (("hero", HERO), ("small", 64)):
        vc.cmd("file.new", width=size, height=size, units="Pixels", name="check")
        ids = mark.draw_mark(vc, 0, 0, size, white, variant, mono=True)
        out = os.path.join(WORK, f"mono-white-{variant}.svg")
        fresh_export(vc, out)
        vc.cmd("file.close")
        ok &= mono_ok(f"draw_mark white mono {variant} (ids {ids})", open(out, encoding="utf-8").read(), "#FFFFFF", "#000000")
    return ok


def accent_demo(vc):
    """Review sheet: neutral, accent on paper, accent on ink; small marks with the accent."""
    W, H = 2200, 1000
    acc = dict(mark.NEUTRAL, accent=TEST_ACCENT)
    vc.cmd("file.new", width=W, height=H, units="Pixels", name="accent-demo")
    vc.tool("draw_shape", shape="rectangle", x=0, y=0, width=W, height=H, fill="#FFFFFF", stroke="none")
    for i, (cols, ground) in enumerate(((mark.NEUTRAL, mark.PAPER), (acc, mark.PAPER), (mark.on_dark(acc), mark.INK))):
        vc.tool("draw_shape", shape="rectangle", x=20 + i * 560, y=20, width=540, height=960, fill=ground, stroke="none")
        mark.draw_mark(vc, 20 + i * 560 + 270 - 460, 50, 920, cols)   # art centred in the panel
    x = 1720
    for cols, ground in ((acc, mark.PAPER), (mark.on_dark(acc), mark.INK)):
        y = 20
        for size in (128, 32, 16):
            vc.tool("draw_shape", shape="rectangle", x=x, y=y, width=size + 20, height=size + 20, fill=ground, stroke="none")
            mark.draw_mark(vc, x + 10, y + 10, size, cols, "small")
            y += size + 40
        x += 220
    out = os.path.join(WORK, "accent-demo.png")
    fresh_export(vc, out)
    vc.cmd("file.close")
    print("  wrote", os.path.relpath(out, HERE))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ref = os.path.abspath(args[0]) if args else os.path.join(WORK, "orig")
    missing = [n for n in SVGS + PNGS if not os.path.exists(os.path.join(ref, n))]
    if missing:
        sys.exit(f"reference folder {ref} lacks {missing}; copy the files there before rebuilding")
    os.makedirs(WORK, exist_ok=True)
    before = snapshot()
    start_write_audit()
    results = {}
    if "--no-build" not in sys.argv:
        print("rebuilding: build.main() in this process (as python -I build.py)")
        import build
        argv, sys.argv = sys.argv, [build.__file__]
        build.main()
        sys.argv = argv
    print("(a) rebuild with the neutral colours against", os.path.relpath(ref, HERE))
    results["a"] = check_rebuild(ref)
    with VC(HERE) as vc:
        print(f"(b) accent {TEST_ACCENT} against accent = ink")
        results["b"] = check_accent(vc)
        print("(c) one colour")
        results["c"] = check_mono(vc)
        accent_demo(vc)
    outside = sorted({p for p in WRITES if not inside(p, HERE)})
    # non-vacuous: the audit must have seen every file this run is known to write
    known = [os.path.join(WORK, n) for n in ("accent-off.png", "accent-on.png", "accent-demo.png")]
    if "--no-build" not in sys.argv:
        known += [os.path.join(HERE, n) for n in SVGS + PNGS]
    seen = {os.path.normcase(os.path.abspath(p)) for p in WRITES}
    unseen = [p for p in known if os.path.normcase(os.path.abspath(p)) not in seen]
    print(f"(d) writes recorded {len(WRITES)} ({len(set(WRITES))} paths), outside this folder "
          f"{len(outside)}", outside[:5], f"; known writes the audit missed {len(unseen)}", unseen[:3])
    after = snapshot()
    changed = sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))
    where = sorted({os.path.relpath(p, BRAND).split(os.sep)[:2][-1] if os.path.relpath(p, BRAND).startswith(os.path.join("history", "candidates"))
                    else os.path.relpath(p, BRAND).split(os.sep)[0] for p in changed})
    print(f"    for information: {len(changed)} files elsewhere under brand/ changed meanwhile, in {where}")
    results["d"] = not outside and not unseen
    print("result:", ", ".join(f"({k}) {'pass' if v else 'FAIL'}" for k, v in results.items()))
    sys.exit(0 if all(results.values()) else 1)


if __name__ == "__main__":
    main()

"""Check a brand kit written by build_brand.py. Exits non-zero on any failure.

Usage:
    python -I brand/tools/check_brand.py <kit folder>

Reads <kit folder>/manifest.json (written by build_brand.py) and checks:
  * every file the manifest promises exists (SVG, PDF, EPS, PNG, compressed source);
  * every SVG has a <title> and a viewBox, no live text, no embedded or linked images, no
    external references, no gradients, filters or opacity, and only the colours its variant may
    use; one-colour variants (black, white) use exactly one fill colour;
  * every PNG decodes, has the pixel size its name promises (marks, favicons, app icons,
    avatars, cards, banner, @2x/@4x lockups at 2 and 4 times the 1x size); a mark or lockup
    meant to be transparent has at least a quarter of its border fully clear (art may touch an
    edge, a painted background may not), and a file meant to be opaque has opaque corners;
  * the palette options meet their WCAG contrast targets (palettes.check()).
Standard library only.
"""
import json
import os
import re
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palettes  # noqa: E402

FIXED_SIZES = {"favicon-16.png": (16, 16), "favicon-32.png": (32, 32), "favicon-48.png": (48, 48),
               "app-icon-180.png": (180, 180), "app-icon-192.png": (192, 192), "app-icon-512.png": (512, 512),
               "avatar-500.png": (500, 500), "avatar-1024.png": (1024, 1024),
               "profile-header.png": (1280, 340), "profile-header@2x.png": (2560, 680),
               "readme-header-noise-engine.png": (1280, 320), "readme-header-noise-engine@2x.png": (2560, 640)}


def png_read(path):
    """Decode an 8-bit, non-interlaced greyscale, RGB or RGBA PNG. Returns (w, h, channels, rows)."""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if depth != 8 or interlace:
                raise ValueError(f"unsupported PNG: depth {depth}, interlace {interlace}")
            ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    raw, stride, rows, prev = zlib.decompress(idat), w * ch, [], bytearray(w * ch)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - ch] if i >= ch else 0
            b, c = prev[i], prev[i - ch] if i >= ch else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return w, h, ch, rows


def corner_alpha(w, h, ch, rows):
    if ch not in (2, 4):
        return [255] * 4
    return [rows[y][x * ch + ch - 1] for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]


def clear_border_share(w, h, ch, rows):
    """Share of border pixels that are fully transparent. A file meant to be transparent can
    have art touching its edge (a bracket in a corner), but a painted background makes this 0."""
    if ch not in (2, 4):
        return 0.0
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] \
        + [(0, y) for y in range(1, h - 1)] + [(w - 1, y) for y in range(1, h - 1)]
    return sum(rows[y][x * ch + ch - 1] == 0 for x, y in border) / len(border)


def svg_problems(path, allowed, mono):
    t = open(path, encoding="utf-8").read()
    out = []
    if "<title>" not in t:
        out.append("no <title>")
    if "viewBox=" not in t:
        out.append("no viewBox")
    for bad, why in (("<text", "live text"), ("<image", "an image"), ("Gradient", "a gradient"),
                     ("<filter", "a filter"), ("opacity", "opacity")):
        if bad in t:
            out.append(f"contains {why}")
    if re.search(r'(?:xlink:)?href="(?!#)', t):
        out.append("external reference")
    fills = {c.upper() for c in re.findall(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"', t)}
    fills |= {c.upper() for c in re.findall(r'(?:fill|stroke):\s*(#[0-9A-Fa-f]{6})', t)}
    extra = fills - {c.upper() for c in allowed}
    if extra:
        out.append(f"colours outside the variant: {sorted(extra)}")
    if mono and len(fills) != 1:
        out.append(f"one-colour file uses {len(fills)} colours: {sorted(fills)}")
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    kit = os.path.abspath(sys.argv[1])
    man = json.load(open(os.path.join(kit, "manifest.json"), encoding="utf-8"))
    fails, n_files = [], 0
    if man["palette"] != "neutral":
        fails += [f"palette {k}: {w} {r}:1 < {t}:1" for k, w, r, t in palettes.check()]
    for rec in man["files"]:
        stem, folder = rec["stem"], rec["folder"]
        mono = stem.endswith("-black") or stem.endswith("-white")
        if rec.get("vector"):
            p = os.path.join(kit, folder, stem + ".svg")
            n_files += 1
            if not os.path.exists(p):
                fails.append(f"missing {os.path.relpath(p, kit)}")
            elif rec["colours"]:
                fails += [f"{os.path.relpath(p, kit)}: {m}" for m in svg_problems(p, rec["colours"], mono)]
        if rec.get("print"):
            for ext in ("pdf", "eps"):
                n_files += 1
                if not os.path.exists(os.path.join(kit, ext, f"{stem}.{ext}")):
                    fails.append(f"missing {ext}/{stem}.{ext}")
        base = None
        for name, pf in rec["png"].items():
            p = os.path.join(kit, pf, name)
            n_files += 1
            if not os.path.exists(p):
                fails.append(f"missing {pf}/{name}")
                continue
            try:
                w, h, ch, rows = png_read(p)
            except Exception as e:  # noqa: BLE001 - report any decoding failure as a check failure
                fails.append(f"{pf}/{name}: {e}")
                continue
            m = re.search(r"-(\d+)\.png$", name)
            want = FIXED_SIZES.get(name)
            if want is None and m and ("mark" in name or name.startswith("favicon")):
                want = (int(m.group(1)), int(m.group(1)))
            if want and (w, h) != want:
                fails.append(f"{pf}/{name}: {w}x{h}, expected {want[0]}x{want[1]}")
            if name.endswith(".png") and "@" not in name and not m:
                base = (w, h)
            k = re.search(r"@(\d)x\.png$", name)
            if k and base:
                # The 1x size is rounded to whole pixels, so a k-times export may differ from
                # k times the rounded 1x size by up to k / 2 pixels, plus one for its own rounding.
                mult = int(k.group(1))
                tol = mult / 2 + 1
                if abs(w - base[0] * mult) > tol or abs(h - base[1] * mult) > tol:
                    fails.append(f"{pf}/{name}: {w}x{h} is not {mult}x of {base[0]}x{base[1]}")
            alpha = corner_alpha(w, h, ch, rows)
            if rec.get("transparent", True) and pf == "png" and clear_border_share(w, h, ch, rows) < 0.25:
                fails.append(f"{pf}/{name}: background not transparent (under 25 % of the border is clear)")
            if not rec.get("transparent", True) and min(alpha) != 255:
                fails.append(f"{pf}/{name}: corners not opaque")
        if rec.get("source", True) and rec.get("vector") and folder != "guide":
            n_files += 1
            if not os.path.exists(os.path.join(kit, "source", stem + ".vectorcraft")):
                fails.append(f"missing source/{stem}.vectorcraft")
    print(f"{man['mark']} / {man['palette']}: {n_files} files checked, {len(fails)} problems")
    for f in fails:
        print("  FAIL", f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

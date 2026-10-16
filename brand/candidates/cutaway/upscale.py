"""Nearest-neighbour upscale of small PNGs (stdlib only) so real pixels can be inspected by eye.

Usage: python upscale.py out.png factor in1.png [in2.png ...]
The inputs are laid side by side on a paper-coloured strip, 16 px apart (before scaling).
Supports 8-bit RGB / RGBA, non-interlaced (what VectorCraft writes). Transparent pixels are
composited on paper #F2EEE6.
"""
import struct
import sys
import zlib

PAPER = (0xF2, 0xEE, 0xE6)


def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos, idat, w = 8, b"", None
    while pos < len(data):
        n, typ = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if typ == b"IHDR":
            w, h, depth, ctype, _, _, inter = struct.unpack(">IIBBBBB", body)
            assert depth == 8 and inter == 0 and ctype in (2, 6), (depth, ctype, inter)
            bpp = 4 if ctype == 6 else 3
        elif typ == b"IDAT":
            idat += body
        pos += 12 + n
    raw = zlib.decompress(idat)
    stride = w * bpp
    rows, prev, i = [], bytearray(stride), 0
    for _ in range(h):
        f = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0
            b = prev[x]
            c = prev[x - bpp] if x >= bpp else 0
            if f == 1:
                line[x] = (line[x] + a) & 255
            elif f == 2:
                line[x] = (line[x] + b) & 255
            elif f == 3:
                line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[x] = (line[x] + pr) & 255
        rows.append(line)
        prev = line
    px = []
    for line in rows:
        row = []
        for x in range(w):
            r, g, b = line[x * bpp:x * bpp + 3]
            al = line[x * bpp + 3] / 255 if bpp == 4 else 1.0
            row.append(tuple(round(v * al + p * (1 - al)) for v, p in zip((r, g, b), PAPER)))
        px.append(row)
    return w, h, px


def write_png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(v for p in row for v in p) for row in px)
    def chunk(t, b):
        return struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b) & 0xFFFFFFFF)
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def main():
    out, k, ins = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
    imgs = [read_png(p) for p in ins]
    gap = 16
    W = sum(w for w, _, _ in imgs) + gap * (len(imgs) + 1)
    H = max(h for _, h, _ in imgs) + 2 * gap
    canvas = [[PAPER] * W for _ in range(H)]
    x0 = gap
    for w, h, px in imgs:
        for y in range(h):
            canvas[gap + y][x0:x0 + w] = px[y]
        x0 += w + gap
    big = []
    for row in canvas:
        r = [p for p in row for _ in range(k)]
        big += [r] * k
    write_png(out, W * k, H * k, big)


if __name__ == "__main__":
    main()

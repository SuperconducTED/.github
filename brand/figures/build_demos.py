"""Render the demo figures for every palette: ILLUSTRATIVE data, fixed seed, not a measurement.

Usage:
    python -I brand/figures/build_demos.py                 # writes brand/figures/demo/
    python -I brand/figures/build_demos.py --out <folder>  # writes somewhere else (the check)

Writes, per palette key: <key>.png and <key>.svg (light ground), <key>-dark.png and
<key>-dark.svg (dark ground); then all-palettes.png and all-palettes-dark.png, the six side by
side (pasted with Pillow, so every panel is the same file the per-palette PNG is).

Fonts: if the brand TTFs are in VectorCraft's font folder (%APPDATA%/VectorCraft/Fonts, where
brand/tools/install_fonts.py puts them), they are registered for this process only. Without
them the styles fall back to DejaVu Sans / DejaVu Sans Mono and the demos still render.

The data are synthetic. Left panel: a T1-like quantity over 40 calibration cycles that drifts
(a random walk plus a slow sag, plus noise), the crisp line frozen at the first cycle's value
(what a single from_backend snapshot would keep predicting), and an interval band built as a
running envelope of the points with a margin, so every point sits inside it. Right panel: one
series per qubit, each a level plus a random walk. Units are "illustrative units": no number on
these figures is a property of any device.
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.font_manager as fm  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

import superconducted_figures as scf  # noqa: E402

SEED = 20261016
CYCLES = 40
CAPTION = ("Illustrative data: synthetic values from a fixed seed ({seed}), not a measurement "
           "of any device. T1 is in arbitrary illustrative units.")


def register_brand_fonts():
    """Register the brand TTFs from VectorCraft's folder for this process; return the count."""
    folder = os.path.join(os.environ.get("APPDATA", ""), "VectorCraft", "Fonts")
    if not os.path.isdir(folder):
        return 0
    n = 0
    for name in sorted(os.listdir(folder)):
        if name.startswith(("SpaceGrotesk-", "SpaceMono-")) and name.endswith(".ttf"):
            fm.fontManager.addfont(os.path.join(folder, name))
            n += 1
    return n


def illustrative_data(n_series):
    rng = np.random.default_rng(SEED)
    x = np.arange(CYCLES)
    walk = np.cumsum(rng.normal(0.0, 1.5, CYCLES))
    sag = -9.0 * np.sin(np.pi * x / (CYCLES - 1))
    y = 100.0 + walk - walk[0] + sag + rng.normal(0.0, 2.2, CYCLES)
    snapshot = y[0]

    w, margin = 3, 3.0
    pad = np.pad(y, w, mode="edge")
    env_lo = np.array([pad[i:i + 2 * w + 1].min() for i in range(CYCLES)]) - margin
    env_hi = np.array([pad[i:i + 2 * w + 1].max() for i in range(CYCLES)]) + margin
    kernel = np.ones(7) / 7
    lo = np.convolve(np.pad(env_lo, 3, mode="edge"), kernel, mode="valid")
    hi = np.convolve(np.pad(env_hi, 3, mode="edge"), kernel, mode="valid")
    lo = np.minimum(lo, y - margin)
    hi = np.maximum(hi, y + margin)
    assert np.all(lo < y) and np.all(y < hi), "the illustrative band must contain every point"

    # One series per qubit: a mean-reverting walk around a slowly moving level, so the lines
    # stay apart and their end labels never collide.
    levels = np.linspace(120.0, 120.0 - 14.0 * (n_series - 1), n_series)
    slopes = rng.uniform(-0.06, 0.06, n_series)
    qubits = []
    for lvl, slope in zip(levels, slopes):
        q = np.empty(CYCLES)
        q[0] = lvl
        for t in range(1, CYCLES):
            target = lvl + slope * t
            q[t] = q[t - 1] + 0.3 * (target - q[t - 1]) + rng.normal(0.0, 1.1)
        qubits.append(q)
    ends = np.sort([q[-1] for q in qubits])
    assert np.all(np.diff(ends) > 6.0), "per-qubit end labels would collide"
    return x, y, snapshot, lo, hi, qubits


def demo_figure(palette, dark):
    r = scf.use(palette, dark=dark)
    name = scf._DOC["palettes"][palette]["name"]
    x, y, snapshot, lo, hi, qubits = illustrative_data(len(r["series"]))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 4.6), width_ratios=[1.75, 1])
    fig.suptitle(f"SuperconducTED chart style: {name}, {'dark' if dark else 'light'} ground",
                 x=0.012, ha="left")

    scf.band(ax, x, lo, hi, label="Engine interval")
    scf.crisp(ax, x, snapshot, label="Single snapshot (frozen)")
    scf.measured(ax, x, y, label="Measured")
    ax.set_title("The engine's interval brackets the drifting hardware")
    ax.set_xlabel("Calibration cycle")
    ax.set_ylabel("T1 (illustrative units)")
    ax.set_xlim(-1, CYCLES)
    ax.set_ylim(70, 120)
    ax.legend(loc="upper right", ncols=3, handlelength=2.2, columnspacing=1.4)

    for i, (q, c) in enumerate(zip(qubits, r["series"])):
        ax2.plot(x, q, color=c, label=f"Q{i}")
        ax2.annotate(f"Q{i}", (x[-1], q[-1]), xytext=(5, 0), textcoords="offset points",
                     va="center", ha="left", fontsize=8.5, color=r["text_secondary"],
                     family="monospace")
    ax2.set_title("Per-qubit series")
    ax2.set_xlabel("Calibration cycle")
    ax2.set_ylabel("T1 (illustrative units)")
    ax2.set_xlim(-1, CYCLES + 4)
    ax2.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncols=len(qubits),
               handlelength=1.4, columnspacing=1.0)

    scf.mono_ticks(fig)
    fig.text(0.012, 0.012, CAPTION.format(seed=SEED), ha="left", va="bottom", fontsize=8,
             color=r["text_secondary"])
    fig.get_layout_engine().set(rect=(0, 0.035, 1, 1))
    return fig


def grid(paths, out, gutter=24, scale=0.5):
    """Paste PNGs in a 2-column grid at `scale`, separated by a neutral gutter."""
    ims = [Image.open(p).convert("RGB") for p in paths]
    w, h = (round(ims[0].width * scale), round(ims[0].height * scale))
    cols, rows = 2, (len(ims) + 1) // 2
    sheet = Image.new("RGB", (cols * w + (cols + 1) * gutter, rows * h + (rows + 1) * gutter),
                      (128, 128, 128))
    for i, im in enumerate(ims):
        c, rr = i % cols, i // cols
        sheet.paste(im.resize((w, h), Image.LANCZOS),
                    (gutter + c * (w + gutter), gutter + rr * (h + gutter)))
    sheet.save(out, optimize=False)


def build(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for dark in (False, True):
        pngs = []
        for key in scf.PALETTES:
            stem = os.path.join(out_dir, key + ("-dark" if dark else ""))
            fig = demo_figure(key, dark)
            fig.savefig(stem + ".png")
            fig.savefig(stem + ".svg", metadata={"Date": None})
            plt.close(fig)
            pngs.append(stem + ".png")
            written += [stem + ".png", stem + ".svg"]
        sheet = os.path.join(out_dir, "all-palettes" + ("-dark" if dark else "") + ".png")
        grid(pngs, sheet)
        written.append(sheet)
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(HERE, "demo"))
    args = ap.parse_args()
    n = register_brand_fonts()
    print(f"brand fonts registered: {n}" if n else
          "brand fonts not found; rendering with the DejaVu fallbacks")
    files = build(args.out)
    print(f"wrote {len(files)} files to {args.out}")

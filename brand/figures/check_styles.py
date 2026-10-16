"""Validate the SuperconducTED chart styles; exit non-zero on any failure.

Usage:
    python -I brand/figures/check_styles.py
    python -I brand/figures/check_styles.py --skill-validator <path to validate_palette.py>
    python -I brand/figures/check_styles.py --strict-demos   # regenerated demos must be
                                                              # byte-identical to the committed

Every number is recomputed from the hex values in roles.json (and from palettes.py for the
consistency check); nothing stored next to a colour is trusted. What it checks:

 1. Roles agree with brand/tools/palettes.py and with the band tint rule.
 2. Contrast (WCAG 2.x, brand/tools/wcag.py): text and secondary text >= 4.5:1 on the ground;
    text and ink >= 4.5:1 on the band fill; the band edge >= 3:1 on the ground and on its own
    fill; crisp line, measured points, axis line and every series colour >= 3:1 on the ground.
    Gridlines are reported, not gated (decoration; see roles.json gates.grid_note).
 3. The categorical sequence, with the dataviz method's thresholds (OKLab x 100, Machado 2009
    severity 1.0): OKLCH L inside the mode's band, C >= 0.10, adjacent CVD Delta E >= 8,
    adjacent normal-vision Delta E >= 15, every slot >= 15 normal and >= 8 CVD from the accent
    and the ink, no slot within 30 degrees of the accent's hue, and the stored all-pairs slot
    count re-measured. Optionally also through the skill's own validate_palette.py.
 4. Style files: every expected file exists; every key is a real rcParam; loading raises on a
    bad value, and any warning (Python warnings as errors, plus matplotlib's logger, which is
    where it reports unknown keys) fails; the file's colours match roles.json.
 5. Font fallback: in a fresh process that never registers the brand fonts, every style
    renders a figure with no findfont or missing-glyph report.
 6. Self-tests, so no guard passes vacuously: an unknown key, a bad value, a low-contrast
    colour, a colour-blind collision and a missing font family must each be caught.
 7. No en or em dash (U+2013, U+2014) in any text file under brand/figures.
 8. The demos regenerate (into a temporary folder) with warnings as errors, every expected
    file appears, and each PNG has the committed size; byte identity is reported.
"""
import argparse
import json
import logging
import os
import subprocess
import sys
import tempfile
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

from colour_math import (BAND, CHROMA_FLOOR, CVD_TARGET, GRAPHIC_MIN, NORMAL_FLOOR,  # noqa: E402
                         TEXT_MIN, contrast, cvd_delta_e, delta_e, hue_distance, mix, oklch)

MODES = ("light", "dark")
TEXT_EXT = (".py", ".md", ".json", ".mplstyle", ".svg", ".txt")
DASHES = (chr(0x2013), chr(0x2014))  # en dash, em dash


class Report:
    def __init__(self):
        self.rows, self.failed = [], 0

    def add(self, ok, what, detail=""):
        self.rows.append(("PASS" if ok else "FAIL", what, detail))
        self.failed += 0 if ok else 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {what}" + (f": {detail}" if detail else ""))

    def info(self, what, detail):
        print(f"  [INFO] {what}: {detail}")


def style_files(doc):
    for key in doc["palettes"]:
        for mode in MODES:
            yield key, mode, os.path.join(HERE, "styles", f"superconducted-{key}"
                                          f"{'-dark' if mode == 'dark' else ''}.mplstyle")


# ---------------------------------------------------------------------------------------------
# 1 to 3: colours
# ---------------------------------------------------------------------------------------------
def check_consistency(doc, rep):
    from palettes import OPTIONS
    a = doc["band_tint"]["a"]
    bad = []
    if set(doc["palettes"]) != set(OPTIONS):
        bad.append(f"palette keys {sorted(doc['palettes'])} != {sorted(OPTIONS)}")
    for key, p in doc["palettes"].items():
        o = OPTIONS.get(key, {})
        for mode in MODES:
            r = p[mode]
            want = {"ground": o.get(f"ground_{mode}"), "text": o.get(f"text_on_{mode}"),
                    "ink": o.get(f"ink_on_{mode}"), "accent": o.get(f"accent_on_{mode}")}
            for role, v in want.items():
                if (v or "").upper() != r[role].upper():
                    bad.append(f"{key}/{mode} {role} {r[role]} != palettes.py {v}")
            derived = {"band_edge": r["accent"], "crisp": r["ink"], "measured": r["ink"],
                       "measured_ring": r["ground"], "band_fill": mix(r["ground"], r["accent"], a)}
            for role, v in derived.items():
                if v.upper() != r[role].upper():
                    bad.append(f"{key}/{mode} {role} {r[role]} != {v}")
    rep.add(not bad, "roles agree with palettes.py and the band tint rule "
            f"(a = {a}, t = (1 - a) * ground + a * accent)", "; ".join(bad[:5]))


def check_contrast(doc, rep):
    worst = {}

    def need(name, fg, bg, target, where):
        v = contrast(fg, bg)
        if name not in worst or v < worst[name][0]:
            worst[name] = (v, where, target)

    grid = []
    for key, p in doc["palettes"].items():
        for mode in MODES:
            r, w = p[mode], f"{key}/{mode}"
            g, f = r["ground"], r["band_fill"]
            need("text on ground", r["text"], g, TEXT_MIN, w)
            need("secondary text on ground", r["text_secondary"], g, TEXT_MIN, w)
            need("text on band fill", r["text"], f, TEXT_MIN, w)
            need("ink (crisp, measured) on band fill", r["ink"], f, TEXT_MIN, w)
            need("band edge on ground", r["band_edge"], g, GRAPHIC_MIN, w)
            need("band edge on band fill", r["band_edge"], f, GRAPHIC_MIN, w)
            need("crisp line on ground", r["crisp"], g, GRAPHIC_MIN, w)
            need("measured points on ground", r["measured"], g, GRAPHIC_MIN, w)
            need("axis line on ground", r["axis"], g, GRAPHIC_MIN, w)
            for c in r["series"]:
                need("series colours on ground", c, g, GRAPHIC_MIN, w + " " + c)
            grid.append((contrast(r["grid"], g), w))
    for name, (v, where, target) in worst.items():
        rep.add(v >= target, f"{name} >= {target:g}:1", f"worst {v:.2f}:1 ({where})")
    lo, hi = min(grid), max(grid)
    rep.info("gridlines (decoration, exempt from 3:1)",
             f"{lo[0]:.2f}:1 ({lo[1]}) to {hi[0]:.2f}:1 ({hi[1]})")


def series_problems(seq, mode, accent, ink, stored_slots=None):
    """Every failed series gate for one sequence, as strings; plus measured numbers."""
    lo, hi = BAND[mode]
    probs, nums = [], {}
    for c in seq:
        L, C, _ = oklch(c)
        if not lo <= L <= hi:
            probs.append(f"{c} L {L:.3f} outside {lo}..{hi}")
        if C < CHROMA_FLOOR:
            probs.append(f"{c} C {C:.3f} below {CHROMA_FLOOR}")
    pairs = list(zip(seq, seq[1:]))
    nums["adj_cvd"] = min(cvd_delta_e(a, b) for a, b in pairs)
    nums["adj_normal"] = min(delta_e(a, b) for a, b in pairs)
    if nums["adj_cvd"] < CVD_TARGET:
        probs.append(f"adjacent CVD Delta E {nums['adj_cvd']:.1f} < {CVD_TARGET:g}")
    if nums["adj_normal"] < NORMAL_FLOOR:
        probs.append(f"adjacent normal Delta E {nums['adj_normal']:.1f} < {NORMAL_FLOOR:g}")
    nums["reserved_normal"] = min(delta_e(c, r) for c in seq for r in (accent, ink))
    nums["reserved_cvd"] = min(cvd_delta_e(c, r) for c in seq for r in (accent, ink))
    if nums["reserved_normal"] < NORMAL_FLOOR or nums["reserved_cvd"] < CVD_TARGET:
        probs.append(f"a slot too close to accent or ink (normal {nums['reserved_normal']:.1f}, "
                     f"CVD {nums['reserved_cvd']:.1f})")
    _, ac, ah = oklch(accent)
    nums["accent_hue_gap"] = (min(hue_distance(ah, oklch(c)[2]) for c in seq)
                              if ac >= 0.05 else None)
    if nums["accent_hue_gap"] is not None and nums["accent_hue_gap"] < 30:
        probs.append(f"a slot within {nums['accent_hue_gap']:.0f} deg of the accent's hue")
    n = 1
    for k in range(2, len(seq) + 1):
        if all(cvd_delta_e(seq[i], seq[j]) >= CVD_TARGET and delta_e(seq[i], seq[j]) >= NORMAL_FLOOR
               for i in range(k) for j in range(i + 1, k)):
            n = k
        else:
            break
    nums["all_pairs_slots"] = n
    if stored_slots is not None and stored_slots != n:
        probs.append(f"stored all-pairs slot count {stored_slots} != measured {n}")
    return probs, nums


def check_series(doc, rep, skill_validator=None):
    for key, p in doc["palettes"].items():
        for mode in MODES:
            r = p[mode]
            probs, n = series_problems(r["series"], mode, r["accent"], r["ink"],
                                       r.get("series_all_pairs_slots"))
            gap = "achromatic accent" if n["accent_hue_gap"] is None else \
                f"accent hue gap {n['accent_hue_gap']:.0f} deg"
            rep.add(not probs, f"series {key}/{mode} ({len(r['series'])} slots: "
                    f"{', '.join(r['series_families'])})",
                    "; ".join(probs) if probs else
                    f"adjacent CVD {n['adj_cvd']:.1f}, normal {n['adj_normal']:.1f}; vs accent "
                    f"and ink normal {n['reserved_normal']:.1f}, CVD {n['reserved_cvd']:.1f}; "
                    f"{gap}; all-pairs safe for the first {n['all_pairs_slots']}")
            if skill_validator:
                cmd = [sys.executable, "-X", "utf8", "-I", skill_validator, ",".join(r["series"]),
                       "--mode", mode, "--surface", r["ground"]]
                adj = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                first = r["series"][:r["series_all_pairs_slots"]]
                allp = subprocess.run(cmd[:5] + [",".join(first)] + cmd[6:] + ["--pairs", "all"],
                                      capture_output=True, text=True, encoding="utf-8")
                rep.add(adj.returncode == 0 and allp.returncode == 0,
                        f"skill validator {key}/{mode}",
                        f"adjacent exit {adj.returncode}, all-pairs on the first "
                        f"{len(first)} exit {allp.returncode}")


# ---------------------------------------------------------------------------------------------
# 4 to 6: style files, fonts, self-tests
# ---------------------------------------------------------------------------------------------
class _Collect(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.records = []

    def emit(self, record):
        self.records.append(record.getMessage())


def load_style_strict(path):
    """Problems found loading one style file; [] when it is clean."""
    import matplotlib as mpl
    probs = []
    with open(path, encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            s = line.split("#", 1)[0].strip()
            if not s:
                continue
            if ":" not in s:
                probs.append(f"line {i}: no 'key: value'")
                continue
            k = s.split(":", 1)[0].strip()
            if k not in mpl.rcParams:
                probs.append(f"line {i}: unknown rc key {k!r}")
    log = logging.getLogger("matplotlib")
    h = _Collect()
    log.addHandler(h)
    old = log.level
    log.setLevel(logging.WARNING)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            rc = mpl.rc_params_from_file(path, fail_on_error=True, use_default_template=False)
    except Exception as e:  # a bad value raises here
        probs.append(f"load raised {type(e).__name__}: {e}")
        rc = None
    finally:
        log.removeHandler(h)
        log.setLevel(old)
    probs += [f"matplotlib logged: {m.strip().splitlines()[0]}" for m in h.records]
    return probs, rc


def check_style_files(doc, rep):
    from matplotlib.colors import to_hex
    for key, mode, path in style_files(doc):
        name = os.path.basename(path)
        if not os.path.isfile(path):
            rep.add(False, f"style {name}", "missing")
            continue
        probs, rc = load_style_strict(path)
        if rc is not None:
            r = doc["palettes"][key][mode]
            want = {"axes.facecolor": r["ground"], "figure.facecolor": r["ground"],
                    "text.color": r["text"], "axes.labelcolor": r["text"],
                    "xtick.labelcolor": r["text_secondary"], "grid.color": r["grid"],
                    "axes.edgecolor": r["axis"]}
            for k, v in want.items():
                if to_hex(rc[k]).upper() != v.upper():
                    probs.append(f"{k} {to_hex(rc[k])} != roles {v}")
            cyc = [to_hex(c).upper() for c in rc["axes.prop_cycle"].by_key()["color"]]
            if cyc != [c.upper() for c in r["series"]]:
                probs.append(f"prop_cycle {cyc} != roles series {r['series']}")
        rep.add(not probs, f"style {name} loads clean and matches roles.json", "; ".join(probs))


PROBE = r'''
import io, json, logging, sys, warnings
sys.path.insert(0, sys.argv[1])
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import superconducted_figures as scf
family = sys.argv[2]
class C(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING); self.r = []
    def emit(self, rec): self.r.append(rec.getMessage())
h = C(); lg = logging.getLogger("matplotlib"); lg.addHandler(h); lg.setLevel(logging.WARNING)
out = {}
warnings.simplefilter("error")
for key in scf.PALETTES:
    for dark in (False, True):
        h.r.clear()
        try:
            scf.use(key, dark=dark)
            if family != "-":
                plt.rcParams["font.family"] = family
            fig, ax = plt.subplots(figsize=(3, 2))
            ax.set_title("T1 drift 0123456789")
            ax.set_xlabel("Calibration cycle")
            scf.band(ax, [0, 1, 2], [-1.5, -1, -0.5], [1, 1.5, 2], label="band")
            scf.crisp(ax, [0, 1, 2], 0.0, label="crisp")
            scf.measured(ax, [0, 1, 2], [0.2, -0.3, 0.4], label="measured")
            ax.legend()
            scf.mono_ticks(fig)
            fig.savefig(io.BytesIO(), format="png")
            plt.close(fig)
            err = None
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        out[f"{key}{'-dark' if dark else ''}"] = {"records": list(h.r), "error": err}
out["_resolved"] = {f: fm.findfont(fm.FontProperties(family=[f])) for f in ("sans-serif", "monospace")}
print(json.dumps(out))
'''


def run_probe(family="-"):
    p = subprocess.run([sys.executable, "-I", "-c", PROBE, HERE, family],
                       capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        return None, p.stderr.strip().splitlines()[-1:] or ["probe failed"]
    return json.loads(p.stdout.strip().splitlines()[-1]), []


def check_fonts(rep):
    res, err = run_probe()
    if res is None:
        rep.add(False, "font fallback probe", "; ".join(err))
        return
    resolved = res.pop("_resolved")
    bad = {k: (v["error"] or "; ".join(v["records"])) for k, v in res.items()
           if v["error"] or v["records"]}
    rep.add(not bad, f"all {len(res)} styles render in a fresh process with no font, glyph or "
            "other warning", "; ".join(f"{k}: {v}" for k, v in list(bad.items())[:3]))
    rep.info("fonts resolved in that process",
             ", ".join(f"{k} -> {os.path.basename(v)}" for k, v in resolved.items()))


def check_self_tests(rep):
    with tempfile.TemporaryDirectory() as tmp:
        bogus = os.path.join(tmp, "bogus-key.mplstyle")
        with open(bogus, "w", encoding="utf-8") as fh:
            fh.write("axes.facecolour: FFFFFF\n")
        probs, _ = load_style_strict(bogus)
        rep.add(bool(probs), "self-test: an unknown rc key is caught", probs[0] if probs else
                "NOT caught")
        badval = os.path.join(tmp, "bad-value.mplstyle")
        with open(badval, "w", encoding="utf-8") as fh:
            fh.write("lines.linewidth: thick\n")
        probs, _ = load_style_strict(badval)
        rep.add(bool(probs), "self-test: a bad rc value is caught",
                probs[0][:90] if probs else "NOT caught")
    low = contrast("#9AA0A6", "#F7F7F5")
    rep.add(low < GRAPHIC_MIN, "self-test: the contrast gate rejects a known low pair",
            f"#9AA0A6 on #F7F7F5 measures {low:.2f}:1 < 3")
    probs, n = series_problems(["#E6632F", "#BD7F00"], "light", "#5F6368", "#111214")
    rep.add(bool(probs), "self-test: the CVD gate rejects orange next to ochre",
            f"deutan/protan Delta E {n['adj_cvd']:.1f}: {probs[0] if probs else 'NOT caught'}")
    res, err = run_probe("NoSuchFamilyXyz")
    caught = res is not None and all(any("findfont" in m for m in v["records"])
                                     for k, v in res.items() if k != "_resolved")
    rep.add(caught, "self-test: a missing font family is reported by the probe",
            "every style reported findfont" if caught else (err or "NOT caught"))


# ---------------------------------------------------------------------------------------------
# 7, 8: dashes and demos
# ---------------------------------------------------------------------------------------------
def check_dashes(rep, root=HERE):
    hits, n = [], 0
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x != "__pycache__"]
        for f in files:
            if f.endswith(TEXT_EXT):
                n += 1
                with open(os.path.join(d, f), encoding="utf-8", errors="replace") as fh:
                    for i, line in enumerate(fh, 1):
                        if any(ch in line for ch in DASHES):
                            hits.append(f"{os.path.relpath(os.path.join(d, f), root)}:{i}")
    rep.add(not hits, f"no en or em dash in {n} text files under brand/figures", ", ".join(hits[:8]))


def check_demos(doc, rep, strict=False):
    from PIL import Image
    committed = os.path.join(HERE, "demo")
    names = []
    for key in doc["palettes"]:
        for suffix in ("", "-dark"):
            names += [f"{key}{suffix}.png", f"{key}{suffix}.svg"]
    names += ["all-palettes.png", "all-palettes-dark.png"]
    missing = [n for n in names if not os.path.isfile(os.path.join(committed, n))]
    rep.add(not missing, f"all {len(names)} committed demo files present", ", ".join(missing))
    with tempfile.TemporaryDirectory() as tmp:
        p = subprocess.run([sys.executable, "-I", "-W", "error",
                            os.path.join(HERE, "build_demos.py"), "--out", tmp],
                           capture_output=True, text=True, encoding="utf-8")
        rep.add(p.returncode == 0, "demos regenerate with warnings as errors",
                (p.stdout.strip().splitlines() or [""])[0] if p.returncode == 0
                else p.stderr.strip()[-300:])
        if p.returncode != 0:
            return
        gone = [n for n in names if not os.path.isfile(os.path.join(tmp, n))
                or os.path.getsize(os.path.join(tmp, n)) == 0]
        rep.add(not gone, "every demo file regenerated and non-empty", ", ".join(gone))
        size_bad, same = [], 0
        for n in names:
            a, b = os.path.join(tmp, n), os.path.join(committed, n)
            if not (os.path.isfile(a) and os.path.isfile(b)):
                continue
            if n.endswith(".png"):
                with Image.open(a) as ia, Image.open(b) as ib:
                    if ia.size != ib.size:
                        size_bad.append(f"{n} {ia.size} != {ib.size}")
            with open(a, "rb") as fa, open(b, "rb") as fb:
                same += fa.read() == fb.read()
        rep.add(not size_bad, "regenerated PNGs have the committed pixel sizes", "; ".join(size_bad))
        detail = f"{same} of {len(names)} files byte-identical to the committed demos"
        if strict:
            rep.add(same == len(names), "demos byte-identical (--strict-demos)", detail)
        else:
            rep.info("byte identity (needs the brand fonts and the same matplotlib)", detail)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--skill-validator", help="path to the dataviz skill's validate_palette.py")
    ap.add_argument("--strict-demos", action="store_true")
    args = ap.parse_args()
    import matplotlib
    import numpy
    print(f"matplotlib {matplotlib.__version__}, numpy {numpy.__version__}, Python "
          f"{sys.version.split()[0]}")
    with open(os.path.join(HERE, "roles.json"), encoding="utf-8") as fh:
        doc = json.load(fh)
    rep = Report()
    print("1-3. colours")
    check_consistency(doc, rep)
    check_contrast(doc, rep)
    check_series(doc, rep, args.skill_validator)
    print("4-6. style files, fonts, self-tests")
    check_style_files(doc, rep)
    check_fonts(rep)
    check_self_tests(rep)
    print("7-8. dashes, demos")
    check_dashes(rep)
    check_demos(doc, rep, args.strict_demos)
    total = len(rep.rows)
    print(f"\n{total - rep.failed} of {total} checks passed"
          + ("" if not rep.failed else f"; {rep.failed} FAILED"))
    sys.exit(1 if rep.failed else 0)


if __name__ == "__main__":
    main()

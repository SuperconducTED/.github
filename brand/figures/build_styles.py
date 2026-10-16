"""Generate the SuperconducTED chart styles: one matplotlib style per palette option and mode.

Usage:
    python -I brand/figures/build_styles.py            # writes styles/*.mplstyle and roles.json
    python -I brand/figures/build_styles.py --print    # also prints the derivation table

Inputs:  brand/tools/palettes.py (the six palette options; read only).
Outputs: brand/figures/styles/superconducted-<key>.mplstyle        light ground
         brand/figures/styles/superconducted-<key>-dark.mplstyle   dark ground
         brand/figures/roles.json                                  every named chart colour,
                                                                   with the reasons and numbers
Deterministic: the same palettes.py always gives byte-identical files.

The chart roles, per palette and mode (light uses *_on_light and ground_light, dark the same):

    ground          figure and axes background                       = ground
    text            titles, axis labels, legend                      = text
    text_secondary  tick labels, captions                            = text mixed toward ground,
                                                                       the lightest mix at >= 7:1
    axis            the baseline spine and tick marks                = text mixed toward ground,
                                                                       the lightest mix at >= 3:1
    grid            hairline gridlines (decoration, see below)       = text mixed toward ground
                                                                       at GRID_A
    band_fill       the interval band (the engine's answer)          = mix(ground, accent, BAND_A)
    band_edge       the band's lower and upper bounds                = accent
    crisp           the single-snapshot line (frozen prediction)     = ink
    measured        the hardware's measured points                   = ink
    series          per-qubit categorical sequence                   = derived below

Band tint. The fill is a solid colour, t = (1 - a) * ground + a * accent per sRGB channel, not
an alpha, so it prints and overlaps the same everywhere. `a` is measured, not picked:
    floor   = the smallest a (step 0.01) at which, in every palette and both modes, the fill
              differs from the ground by Delta E >= 8 (OKLab x 100, the dataviz CVD target)
              under normal vision AND under protanopia AND deuteranopia;
    ceiling = the largest a at which ink and text on the fill keep >= 4.5:1 and the accent
              edge keeps >= 3:1 against its own fill;
    BAND_A  = the floor rounded up to the next 0.05, asserted to be <= the ceiling.

Series. The dataviz skill's reference hues (eight families, references/palette.md) are the
documented source. For each palette:
  1. Exclude the accent's hue: every family within HUE_WINDOW (30) degrees of the accent's
     OKLCH hue in either mode (an achromatic accent, C < 0.05, excludes none).
  2. Snap each remaining family to the palette's ground (the skill's snap-to-passing): hold
     the reference hue, move OKLCH L away from the reference step in 0.005 steps (chroma
     capped by the sRGB gamut) until the colour sits in the mode's L band, keeps C >= 0.10,
     clears 3:1 on the ground (stricter than the skill, which allows a labelled relief band),
     and stays apart from the reserved colours, accent and ink, as if they were neighbouring
     slots: normal-vision Delta E >= 15 and CVD Delta E >= 8 (the band edge is a thin line,
     like a series line). A family with no passing step drops out. The reference hex itself
     is used when it already passes. Step 2 is the discriminating test; step 1 only names the
     hue the accent owns.
  3. Enumerate every ordering of up to six families (the theme derivation of color-formula.md)
     and keep those whose adjacent pairs clear CVD Delta E >= 8 and normal Delta E >= 15 in
     BOTH modes; pick by: the first three slots validating all-pairs (CVD >= 8 and normal
     >= 15 for every pair among them, as the skill's own default does), then the largest
     worst adjacent CVD Delta E (to 0.1), then the longest all-pairs prefix, then the largest
     worst adjacent normal Delta E, then the order closest to the reference order. Six slots
     unless no six-slot order passes, then five, and so on.
"""
import argparse
import itertools
import json
import math
import os
import sys
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
from colour_math import (BAND, CHROMA_FLOOR, CVD_TARGET, GRAPHIC_MIN,  # noqa: E402
                         NORMAL_FLOOR, TEXT_MIN, contrast, cvd_delta_e, delta_e, hue_distance,
                         max_chroma, mix, oklch, oklch_hex)
from palettes import OPTIONS  # noqa: E402

STYLES = os.path.join(HERE, "styles")
ROLES = os.path.join(HERE, "roles.json")
MODES = ("light", "dark")

# The dataviz skill's reference categorical palette (references/palette.md), light and dark
# steps per hue family, in the skill's default order.
REFERENCE = {
    "blue": ("#2A78D6", "#3987E5"),
    "orange": ("#EB6834", "#D95926"),
    "aqua": ("#1BAF7A", "#199E70"),
    "yellow": ("#EDA100", "#C98500"),
    "magenta": ("#E87BA4", "#D55181"),
    "green": ("#008300", "#008300"),
    "violet": ("#4A3AA7", "#9085E9"),
    "red": ("#E34948", "#E66767"),
}
FAMILIES = list(REFERENCE)
MAX_SLOTS = 6
ALL_PAIRS_GOAL = 3         # the skill's default validates its first three slots all-pairs
HUE_WINDOW = 30.0          # degrees of OKLCH hue that count as "the accent's hue"
ACHROMATIC_C = 0.05        # an accent below this chroma has no hue to protect
RESERVED_CVD = CVD_TARGET  # series vs accent or ink: the band edge is a thin line, like a
                           # series line, so it is held to the series target, not the floor
L_STEP = 0.005             # OKLCH lightness step for snapping
BAND_VISIBLE = CVD_TARGET  # fill vs ground, Delta E under normal, protan and deutan vision
SECONDARY_TARGET = 7.0     # tick labels are small: WCAG AAA for normal text
AXIS_TARGET = GRAPHIC_MIN  # the baseline is a graphical object: 3:1
GRID_A = 0.12              # gridlines: a recessive hairline, decoration only

_dE = lru_cache(maxsize=None)(delta_e)
_cvd = lru_cache(maxsize=None)(cvd_delta_e)


def _role(o, role, mode):
    return o[f"{role}_{mode}"] if role == "ground" else o[f"{role}_on_{mode}"]


# ---------------------------------------------------------------------------------------------
# Band tint
# ---------------------------------------------------------------------------------------------
def _band_visibility(o, mode, a):
    g = _role(o, "ground", mode)
    f = mix(g, _role(o, "accent", mode), a)
    return min(delta_e(f, g), delta_e(f, g, "protan"), delta_e(f, g, "deutan"))


def _band_limits(o, mode, a):
    """Worst of the ceiling constraints, as (ink_or_text_on_fill, accent_on_fill)."""
    g = _role(o, "ground", mode)
    f = mix(g, _role(o, "accent", mode), a)
    on_fill = min(contrast(_role(o, "ink", mode), f), contrast(_role(o, "text", mode), f))
    return on_fill, contrast(_role(o, "accent", mode), f)


def derive_band_tint():
    steps = [i / 100 for i in range(1, 61)]
    floor = {}
    for mode in MODES:
        floor[mode] = next(a for a in steps if all(_band_visibility(o, mode, a) >= BAND_VISIBLE
                                                   for o in OPTIONS.values()))
    ceiling = {}
    for mode in MODES:
        ok = [a for a in steps if all(_band_limits(o, mode, a)[0] >= TEXT_MIN
                                      and _band_limits(o, mode, a)[1] >= GRAPHIC_MIN
                                      for o in OPTIONS.values())]
        ceiling[mode] = max(a for a in ok if all(b in ok for b in steps if b <= a))
    a = math.ceil(max(floor.values()) * 20 - 1e-9) / 20
    if a > min(ceiling.values()):
        raise SystemExit(f"band tint {a} exceeds the ceiling {ceiling}")

    def binding(mode, value, fn):
        return min(OPTIONS, key=lambda k: fn(OPTIONS[k], mode, value))

    return {
        "a": a,
        "rule": "t = (1 - a) * ground + a * accent, per sRGB channel, rounded to 8 bits",
        "floor": floor,
        "floor_binding_palette": {m: binding(m, floor[m], _band_visibility) for m in MODES},
        "ceiling": ceiling,
        "ceiling_binding_palette": {m: binding(m, ceiling[m], lambda o, mm, v: _band_limits(o, mm, v)[0])
                                    for m in MODES},
        "why": ("The smallest coverage at which the band reads as a region for every reader "
                "(Delta E >= 8 against the ground under normal, protan and deutan vision, in all "
                "six palettes and both modes), rounded up to a memorable 0.05 step. It stays a "
                "quiet wash (the dataviz method: never a saturated block) and keeps ink and "
                "text on the band at >= 4.5:1 and the accent edge at >= 3:1 on its own fill."),
    }


# ---------------------------------------------------------------------------------------------
# Neutral roles
# ---------------------------------------------------------------------------------------------
def lightest_mix(ground, colour, target):
    """The smallest coverage s (step 0.01) whose mix(ground, colour, s) clears target:1."""
    for i in range(1, 101):
        hx = mix(ground, colour, i / 100)
        if contrast(hx, ground) >= target:
            return i / 100, hx
    raise ValueError(f"{colour} never reaches {target}:1 on {ground}")


# ---------------------------------------------------------------------------------------------
# Series
# ---------------------------------------------------------------------------------------------
def excluded_families(o):
    """Families that share the accent's hue (within HUE_WINDOW in either mode), with reasons."""
    out = {}
    for mode in MODES:
        _, c, h = oklch(_role(o, "accent", mode))
        if c < ACHROMATIC_C:
            continue
        for f in FAMILIES:
            d = hue_distance(h, oklch(REFERENCE[f][MODES.index(mode)])[2])
            if d < HUE_WINDOW:
                out.setdefault(f, f"within {HUE_WINDOW:.0f} deg of the {mode} accent's hue "
                                  f"({d:.0f} deg)")
    return out


def snap(family, mode, ground, reserved):
    """The passing step of a family nearest its reference lightness, or None."""
    ref = REFERENCE[family][MODES.index(mode)]
    L0, C0, h = oklch(ref)
    lo, hi = BAND[mode]
    ks = sorted(range(-200, 201), key=lambda k: (abs(k), k))
    for k in ks:
        L = L0 + k * L_STEP
        if not lo <= L <= hi:
            continue
        hx = ref if k == 0 else oklch_hex(L, min(C0, max_chroma(L, h)), h)
        if hx is None:
            continue
        Lr, Cr, _ = oklch(hx)
        if not (lo <= Lr <= hi) or Cr < CHROMA_FLOOR or contrast(hx, ground) < GRAPHIC_MIN:
            continue
        if any(_dE(hx, r) < NORMAL_FLOOR or _cvd(hx, r) < RESERVED_CVD for r in reserved):
            continue
        return hx
    return None


def all_pairs_prefix(seq):
    """How many leading slots validate all-pairs (CVD >= 8 and normal >= 15 for every pair)."""
    n = 1
    for k in range(2, len(seq) + 1):
        if all(_cvd(seq[i], seq[j]) >= CVD_TARGET and _dE(seq[i], seq[j]) >= NORMAL_FLOOR
               for i in range(k) for j in range(i + 1, k)):
            n = k
        else:
            break
    return n


def derive_series(o):
    excl = excluded_families(o)
    steps = {m: {} for m in MODES}
    for mode in MODES:
        reserved = (_role(o, "accent", mode), _role(o, "ink", mode))
        for f in FAMILIES:
            if f not in excl:
                steps[mode][f] = snap(f, mode, _role(o, "ground", mode), reserved)
    usable = [f for f in FAMILIES if f not in excl and steps["light"][f] and steps["dark"][f]]
    for k in range(min(MAX_SLOTS, len(usable)), 1, -1):
        best = None
        for order in itertools.permutations(usable, k):
            score = []
            for mode in MODES:
                seq = [steps[mode][f] for f in order]
                pairs = list(zip(seq, seq[1:]))
                score.append((min(_cvd(a, b) for a, b in pairs), min(_dE(a, b) for a, b in pairs),
                              all_pairs_prefix(seq)))
            worst_cvd = min(s[0] for s in score)
            worst_nv = min(s[1] for s in score)
            if worst_cvd < CVD_TARGET or worst_nv < NORMAL_FLOOR:
                continue
            prefix = min(s[2] for s in score)
            key = (min(prefix, ALL_PAIRS_GOAL), round(worst_cvd, 1), prefix, round(worst_nv, 1),
                   tuple(-FAMILIES.index(f) for f in order))
            if best is None or key > best[0]:
                best = (key, order)
        if best:
            order = list(best[1])
            return {
                "families": order,
                "light": [steps["light"][f] for f in order],
                "dark": [steps["dark"][f] for f in order],
                "excluded": excl,
                "unused": [f for f in usable if f not in order],
            }
    raise SystemExit(f"no passing series order for {o['name']}")


# ---------------------------------------------------------------------------------------------
# Roles and style files
# ---------------------------------------------------------------------------------------------
def derive_roles(o, band, series, mode):
    g, text = _role(o, "ground", mode), _role(o, "text", mode)
    ink, accent = _role(o, "ink", mode), _role(o, "accent", mode)
    sec_a, secondary = lightest_mix(g, text, SECONDARY_TARGET)
    axis_a, axis = lightest_mix(g, text, AXIS_TARGET)
    return {
        "ground": g,
        "text": text,
        "text_secondary": secondary,
        "axis": axis,
        "grid": mix(g, text, GRID_A),
        "ink": ink,
        "accent": accent,
        "band_fill": mix(g, accent, band["a"]),
        "band_edge": accent,
        "crisp": ink,
        "measured": ink,
        "measured_ring": g,
        "series": series[mode],
        "series_families": series["families"],
        "series_all_pairs_slots": all_pairs_prefix(series[mode]),
        "mix":{"text_secondary": sec_a, "axis": axis_a, "grid": GRID_A, "band_fill": band["a"]},
    }


def _h(c):
    return c.lstrip("#").upper()


def style_text(key, o, r, mode):
    cyc = ", ".join(f"'{_h(c)}'" for c in r["series"])
    head = [
        f"# SuperconducTED chart style: {o['name']}, {mode} ground.",
        "# Generated by brand/figures/build_styles.py from brand/tools/palettes.py.",
        "# Do not edit by hand: change palettes.py or the generator and run it again.",
        "#",
        "# Chart roles (roles.json holds them too; superconducted_figures.py draws with them):",
        f"#   band fill  #{_h(r['band_fill'])}  the interval band, a solid {round(r['mix']['band_fill'] * 100)} percent tint of the accent",
        f"#   band edge  #{_h(r['band_edge'])}  the band's bounds (the accent: the range, nothing else)",
        f"#   crisp      #{_h(r['crisp'])}  the single-snapshot line, dashed (ink: the machine)",
        f"#   measured   #{_h(r['measured'])}  the hardware's points, ringed in the ground colour",
        f"#   series     {' '.join('#' + _h(c) for c in r['series'])}",
        f"#              ({', '.join(r['series_families'])}; per-qubit identity, fixed order)",
        "#",
        "# Fonts: Space Grotesk for text, Space Mono as the monospace face (tick labels through",
        "# superconducted_figures.mono_ticks); DejaVu Sans and DejaVu Sans Mono, which ship with",
        "# matplotlib, stand in silently where the brand fonts are not installed.",
        "",
    ]
    rc = [
        ("font.family", "sans-serif"),
        ("font.sans-serif", "Space Grotesk, DejaVu Sans"),
        ("font.monospace", "Space Mono, DejaVu Sans Mono"),
        ("font.size", "10"),
        ("text.color", _h(r["text"])),
        ("", ""),
        ("figure.facecolor", _h(r["ground"])),
        ("figure.edgecolor", _h(r["ground"])),
        ("figure.constrained_layout.use", "True"),
        ("figure.constrained_layout.h_pad", "0.1"),
        ("figure.constrained_layout.w_pad", "0.08"),
        ("figure.titlesize", "13"),
        ("figure.titleweight", "bold"),
        ("savefig.facecolor", _h(r["ground"])),
        ("savefig.edgecolor", _h(r["ground"])),
        ("savefig.dpi", "200"),
        ("svg.hashsalt", "superconducted"),
        ("pdf.fonttype", "42"),
        ("ps.fonttype", "42"),
        ("", ""),
        ("axes.facecolor", _h(r["ground"])),
        ("axes.edgecolor", _h(r["axis"])),
        ("axes.linewidth", "0.8"),
        ("axes.spines.left", "False"),
        ("axes.spines.right", "False"),
        ("axes.spines.top", "False"),
        ("axes.spines.bottom", "True"),
        ("axes.grid", "True"),
        ("axes.grid.axis", "y"),
        ("axes.axisbelow", "True"),
        ("axes.labelcolor", _h(r["text"])),
        ("axes.labelsize", "10"),
        ("axes.labelpad", "6"),
        ("axes.titlecolor", _h(r["text"])),
        ("axes.titlesize", "11"),
        ("axes.titleweight", "normal"),
        ("axes.titlelocation", "left"),
        ("axes.titlepad", "10"),
        ("axes.prop_cycle", f"cycler('color', [{cyc}])"),
        ("", ""),
        ("grid.color", _h(r["grid"])),
        ("grid.linestyle", "-"),
        ("grid.linewidth", "0.6"),
        ("grid.alpha", "1.0"),
        ("", ""),
        ("xtick.color", _h(r["axis"])),
        ("xtick.labelcolor", _h(r["text_secondary"])),
        ("xtick.labelsize", "8.5"),
        ("xtick.direction", "out"),
        ("xtick.major.size", "3.5"),
        ("xtick.major.width", "0.8"),
        ("xtick.minor.visible", "False"),
        ("ytick.color", _h(r["axis"])),
        ("ytick.labelcolor", _h(r["text_secondary"])),
        ("ytick.labelsize", "8.5"),
        ("ytick.major.size", "0"),
        ("ytick.major.pad", "5"),
        ("ytick.minor.visible", "False"),
        ("", ""),
        ("legend.frameon", "False"),
        ("legend.fontsize", "9"),
        ("legend.labelcolor", _h(r["text"])),
        ("legend.handlelength", "1.8"),
        ("legend.borderaxespad", "0.4"),
        ("", ""),
        ("lines.linewidth", "1.5"),
        ("lines.solid_capstyle", "round"),
        ("lines.solid_joinstyle", "round"),
        ("lines.dash_capstyle", "butt"),
        ("lines.dashed_pattern", "3.2, 2.0"),
        ("lines.markersize", "6"),
        ("lines.markeredgewidth", "1.2"),
        ("patch.linewidth", "1.0"),
    ]
    body = [f"{k}: {v}" if k else "" for k, v in rc]
    return "\n".join(head + body) + "\n"


def build(verbose=False):
    os.makedirs(STYLES, exist_ok=True)
    band = derive_band_tint()
    doc = {
        "schema": 1,
        "generated_by": "brand/figures/build_styles.py",
        "source": "brand/tools/palettes.py",
        "band_tint": band,
        "gates": {
            "text_on_ground": TEXT_MIN, "marks_on_ground": GRAPHIC_MIN,
            "ink_and_text_on_band": TEXT_MIN, "edge_on_band": GRAPHIC_MIN,
            "series_lightness_band": BAND, "series_chroma_floor": CHROMA_FLOOR,
            "series_adjacent_cvd_target": CVD_TARGET, "series_normal_floor": NORMAL_FLOOR,
            "series_all_pairs_goal": ALL_PAIRS_GOAL,
            "series_vs_reserved": {"normal": NORMAL_FLOOR, "cvd": RESERVED_CVD},
            "hue_window_deg": HUE_WINDOW, "secondary_text_target": SECONDARY_TARGET,
            "axis_target": AXIS_TARGET, "grid_mix": GRID_A,
            "grid_note": ("Gridlines are decoration (WCAG 1.4.11 covers graphics needed to "
                          "understand the content; tick labels carry the values), so they "
                          "are kept recessive and exempt from 3:1."),
        },
        "reference_hues": {f: {"light": l, "dark": d} for f, (l, d) in REFERENCE.items()},
        "palettes": {},
    }
    for key, o in OPTIONS.items():
        series = derive_series(o)
        entry = {"name": o["name"], "why": o["why"],
                 "series_excluded_families": series["excluded"],
                 "series_unused_families": series["unused"]}
        for mode in MODES:
            r = derive_roles(o, band, series, mode)
            entry[mode] = r
            name = f"superconducted-{key}" + ("-dark" if mode == "dark" else "") + ".mplstyle"
            with open(os.path.join(STYLES, name), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(style_text(key, o, r, mode))
        doc["palettes"][key] = entry
        if verbose:
            print(f"{o['name']:13s} excluded {sorted(series['excluded'])} order {series['families']}")
            for mode in MODES:
                print(f"   {mode:5s} {' '.join(entry[mode]['series'])}  band {entry[mode]['band_fill']}"
                      f"  all-pairs slots {entry[mode]['series_all_pairs_slots']}")
    with open(ROLES, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    if verbose:
        print(f"band tint a = {band['a']} (floor {band['floor']}, ceiling {band['ceiling']})")
    return doc


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--print", action="store_true", help="print the derivation table")
    build(verbose=ap.parse_args().print)
    print(f"wrote {len(OPTIONS) * 2} styles to {STYLES} and {ROLES}")

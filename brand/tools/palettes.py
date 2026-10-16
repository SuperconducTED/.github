"""The palette options for the SuperconducTED identity: the single source of truth.

The owner picks one after the team picks the mark (decision of 2026-10-16). Until then every
generator renders all of them. Each option assigns colours to roles, not to shapes:

    ground_light, ground_dark     the two backgrounds
    text_on_light, text_on_dark   type (the wordmark, running text)
    ink_on_light, ink_on_dark     the mark's machine and line work (the "ink" role of the mark
                                  API); usually the same as the text colour
    accent_on_light, accent_on_dark
                                  the range: brackets, intervals, chart bands (the "accent"
                                  role); the identity's one colour rule

Contract: OPTIONS maps a key to such a dict plus "name" and "why" (one line tied to the story).
check() returns every failed contrast target; run this file to print the table.

Contrast targets (WCAG 2.x, computed by wcag.py):
    text on its ground                      >= 4.5:1  (normal-size text)
    ink and accent on their ground          >= 3:1    (graphical objects)
Accent colours are never used for small text unless they also clear 4.5:1; the table says
which ones do.

Kept clear of IBM blue #0F62FE, Qiskit purple #6929C4 and the CASSANDRA Collective's night,
bronze and gold (#121C2E, #8A672B, #D2A65A); Copper is close in feel to CASSANDRA's
terracotta #B2462A and says so.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wcag import contrast  # noqa: E402


def _opt(name, why, ink, paper, accent_l, accent_d, ink_l=None, ink_d=None):
    return dict(name=name, why=why, ground_light=paper, ground_dark=ink,
                text_on_light=ink, text_on_dark=paper,
                ink_on_light=ink_l or ink, ink_on_dark=ink_d or paper,
                accent_on_light=accent_l, accent_on_dark=accent_d)


OPTIONS = {
    "cryostat": _opt("Cryostat", "The cold of the dilution refrigerator: ice on blue-black.",
                     "#0A1B24", "#EEF3F5", "#0A6C7C", "#4FD6E6"),
    "heatleak": _opt("Heat leak", "Cold machine, warm noise: the machine in ice blue, the range "
                     "it drifts through in ember.",
                     "#0B1622", "#F1F4F7", "#B8461B", "#FF8A4C", ink_l="#1F5F86", ink_d="#8FD3F4"),
    "copper": _opt("Copper stage", "The refrigerator's plates are copper: copper on graphite. "
                   "Close in feel to CASSANDRA's terracotta.",
                   "#15171A", "#F5F3EF", "#9C4E1C", "#E39256"),
    "phosphor": _opt("Phosphor", "The oscilloscope trace, the instrument that shows a signal "
                     "drifting.",
                     "#0B1410", "#EEF3EF", "#0B7446", "#5BF0A0"),
    "figure": _opt("Figure", "Matplotlib's default blue (#1F77B4), the colour of nearly every "
                   "Python plot, error bands included.",
                   "#16191D", "#FFFFFF", "#1F77B4", "#6FB1E3"),
    "mono": _opt("Monochrome", "No colour to lean on: ink, paper and one grey for the range.",
                 "#111214", "#F7F7F5", "#5F6368", "#9AA0A6"),
}

TEXT_MIN, GRAPHIC_MIN = 4.5, 3.0


def ratios(o):
    """Contrast ratios for one option, keyed by what they measure."""
    return {
        "text on light": contrast(o["text_on_light"], o["ground_light"]),
        "text on dark": contrast(o["text_on_dark"], o["ground_dark"]),
        "ink on light": contrast(o["ink_on_light"], o["ground_light"]),
        "ink on dark": contrast(o["ink_on_dark"], o["ground_dark"]),
        "accent on light": contrast(o["accent_on_light"], o["ground_light"]),
        "accent on dark": contrast(o["accent_on_dark"], o["ground_dark"]),
    }


def check():
    """Every (option, measure, ratio, target) that misses its target; empty when all pass."""
    fails = []
    for key, o in OPTIONS.items():
        for what, r in ratios(o).items():
            target = TEXT_MIN if what.startswith("text") else GRAPHIC_MIN
            if r < target:
                fails.append((key, what, round(r, 2), target))
    return fails


if __name__ == "__main__":
    for key, o in OPTIONS.items():
        rs = ratios(o)
        text_ok = [w for w in ("accent on light", "accent on dark") if rs[w] >= TEXT_MIN]
        print(f"{o['name']:13s} " + "  ".join(f"{w} {r:5.2f}" for w, r in rs.items())
              + f"   accent fit for text: {', '.join(text_ok) or 'none'}")
    bad = check()
    print("all targets met" if not bad else f"FAILED: {bad}")
    sys.exit(1 if bad else 0)

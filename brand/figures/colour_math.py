"""Colour arithmetic for the chart style: OKLab, OKLCH, colour-vision simulation, tints.

Used by build_styles.py (to derive the chart roles) and check_styles.py (to re-measure them).
The team helper superconducted_figures.py does not import this file; it only reads roles.json.

Contract (every colour is an sRGB hex string "#RRGGBB"):
    mix(ground, colour, a) -> hex      per-channel sRGB tint, t = (1 - a) * ground + a * colour
    oklch(hex) -> (L, C, h)            OKLCH lightness [0, 1], chroma, hue angle in degrees
    oklch_hex(L, C, h) -> hex | None   None when (L, C, h) is outside the sRGB gamut
    max_chroma(L, h) -> float          the largest in-gamut chroma at that lightness and hue
    delta_e(a, b, kind=None) -> float  Euclidean OKLab distance x 100; kind is None (normal
                                       vision), "protan", "deutan" or "tritan"
    cvd_delta_e(a, b) -> float         min(protan, deutan) distance, the dataviz CVD measure
    contrast(a, b) -> float            WCAG 2.x ratio, from brand/tools/wcag.py

Method and thresholds follow the dataviz skill's validator (validate_palette.py): OKLab after
Ottosson (2020); colour-vision deficiency simulated with Machado, Oliveira and Fernandes (2009)
at severity 1.0 in linear RGB, clamped to [0, 1]; Delta E is OKLab distance x 100. The CVD
thresholds below are calibrated to that simulation model, so the model is part of the standard.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
from wcag import contrast  # noqa: E402,F401  (re-exported for the build and check scripts)

# Gates of the dataviz method (validate_palette.py, color-formula.md, check 2 to 5).
BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}   # OKLCH L for a categorical slot
CHROMA_FLOOR = 0.10                                     # OKLCH C; below it a hue reads as grey
CVD_TARGET, CVD_FLOOR = 8.0, 6.0                        # min(protan, deutan) Delta E x 100
NORMAL_FLOOR = 15.0                                     # unsimulated Delta E x 100, hard gate
TEXT_MIN, GRAPHIC_MIN = 4.5, 3.0                        # WCAG 2.x targets

MACHADO = {
    "protan": [[0.152286, 1.052583, -0.204868],
               [0.114503, 0.786281, 0.099216],
               [-0.003882, -0.048116, 1.051998]],
    "deutan": [[0.367322, 0.860646, -0.227968],
               [0.280085, 0.672501, 0.047413],
               [-0.011820, 0.042940, 0.968881]],
    "tritan": [[1.255528, -0.076749, -0.178779],
               [-0.078411, 0.930809, 0.147602],
               [0.004733, 0.691367, 0.303900]],
}


def hex_to_srgb(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def srgb_to_hex(rgb):
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02X}" for c in rgb)


def _s2lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _lin2s(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def _lin(h):
    return tuple(_s2lin(c) for c in hex_to_srgb(h))


def _lin_to_oklab(r, g, b):
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b  # noqa: E741
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _oklab_to_lin(L, a, b):
    l = L + 0.3963377774 * a + 0.2158037573 * b  # noqa: E741
    m = L - 0.1055613458 * a - 0.0638541728 * b
    s = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l ** 3, m ** 3, s ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklab(h):
    return _lin_to_oklab(*_lin(h))


def oklch(h):
    L, a, b = oklab(h)
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def _in_gamut(lin, eps=1e-6):
    return all(-eps <= c <= 1 + eps for c in lin)


def oklch_hex(L, C, h):
    """Hex for an OKLCH colour, or None when it lies outside sRGB."""
    a, b = C * math.cos(math.radians(h)), C * math.sin(math.radians(h))
    lin = _oklab_to_lin(L, a, b)
    if not _in_gamut(lin):
        return None
    return srgb_to_hex(_lin2s(max(0.0, min(1.0, c))) for c in lin)


def max_chroma(L, h, hi=0.4):
    """Largest chroma in sRGB at OKLCH lightness L and hue h (bisection, 1e-4 resolution)."""
    lo = 0.0
    while hi - lo > 1e-4:
        mid = (lo + hi) / 2
        if oklch_hex(L, mid, h) is None:
            hi = mid
        else:
            lo = mid
    return lo


def mix(ground, colour, a):
    """Per-channel sRGB tint: (1 - a) * ground + a * colour, rounded to 8 bits per channel."""
    g, c = hex_to_srgb(ground), hex_to_srgb(colour)
    return srgb_to_hex((1 - a) * gi + a * ci for gi, ci in zip(g, c))


def _simulate(h, kind):
    r, g, b = _lin(h)
    M = MACHADO[kind]
    return tuple(max(0.0, min(1.0, M[i][0] * r + M[i][1] * g + M[i][2] * b)) for i in range(3))


def delta_e(h1, h2, kind=None):
    """OKLab Euclidean distance x 100; kind None is unsimulated (normal) vision."""
    a = _lin_to_oklab(*(_simulate(h1, kind) if kind else _lin(h1)))
    b = _lin_to_oklab(*(_simulate(h2, kind) if kind else _lin(h2)))
    return 100 * math.dist(a, b)


def cvd_delta_e(h1, h2):
    """The dataviz CVD separation of a pair: the worse of protanopia and deuteranopia."""
    return min(delta_e(h1, h2, "protan"), delta_e(h1, h2, "deutan"))


def hue_distance(h1, h2):
    """Smallest angle between two hue angles in degrees, in [0, 180]."""
    d = abs(h1 - h2) % 360
    return 360 - d if d > 180 else d

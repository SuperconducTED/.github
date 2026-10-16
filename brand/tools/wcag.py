"""WCAG 2.x relative luminance and contrast ratio for sRGB hex colours.

relative_luminance("#RRGGBB") -> float in [0, 1]
contrast("#RRGGBB", "#RRGGBB") -> float in [1, 21], symmetric in its arguments

Formulae (WCAG 2.2, "relative luminance" and "contrast ratio" definitions):
    c = v / 255;  c_lin = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    L = 0.2126 R_lin + 0.7152 G_lin + 0.0722 B_lin
    ratio = (L_lighter + 0.05) / (L_darker + 0.05)
"""


def relative_luminance(hex_colour):
    h = hex_colour.lstrip("#")
    channels = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((relative_luminance(a), relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)

"""Build the SuperconducTED brand kit in VectorCraft from one mark and one palette.

Usage, from the repository root (keep the checkout path short: VectorCraft 0.10 writes no file
at 260 or more path characters):

    python -I brand/tools/build_brand.py --mark engraved --palette cryostat --out <folder>
    python -I brand/tools/build_brand.py --decision --scratch <folder>

The first form writes the whole kit for one mark and one palette into <folder>: lockups, colour
variants, web icons, the organisation avatar, the profile banner, social cards, a README header,
guide images and a manifest that check_brand.py verifies. The second renders the team's decision
aids into brand/decision/ (each candidate in use, and every palette on every candidate), building
each candidate's kit in <folder>/<mark>/ on the way, which also tests the generator end to end.

Inputs: brand/candidates/<mark>/mark.py (the mark API in brand/candidates/MARK_API.md),
brand/tools/palettes.py (the palette options), Space Grotesk and Space Mono installed in
VectorCraft (brand/tools/install_fonts.py). Standard library only.
Side effects: writes only inside --out, --scratch and brand/decision/.
Every number of the layouts lives in the constants below; edit them here, never the outputs.
"""
import argparse
import importlib.util
import inspect
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.dirname(HERE)
# SC_CANDIDATES points the generator at another candidates folder; it exists for testing the
# layouts with a stand-in mark and is not needed for normal use.
CANDIDATES = os.environ.get("SC_CANDIDATES") or os.path.join(BRAND, "candidates")
sys.path.insert(0, HERE)
from vcdriver import VC  # noqa: E402
from wcag import contrast  # noqa: E402
import palettes  # noqa: E402

MARKS = ("engraved", "cutaway", "radial", "isometric")
FONT, MONO = "Space Grotesk", "Space Mono"
WORDMARK = dict(text="SuperconducTED", style="Medium", tracking=0)
ORG_LINE = "Student research at TED University on honest noise models for superconducting quantum computers."
TAGLINE = "Noise as a range, not a number."   # owner's pick, 2026-10-16 (brand/FOUNDATION.md)
PLACE_LINE = "Ankara · Türkiye"
REPO_CARDS = {
    "noise-engine": dict(title="Noise engine", line="Fuzzy-logic noise engine for Qiskit Aer-based quantum computer emulators."),
    "codesign": dict(title="Co-design", line="Requirements and design record for the SuperconducTED co-design tool."),
}
# The neutral colours the candidates were drawn in; used for the decision aids, where the
# palette is deliberately not yet chosen (owner decision 2026-10-16).
NEUTRAL = dict(name="Neutral", why="The candidates' drawing colours; no palette chosen yet.",
               ground_light="#F2EEE6", ground_dark="#1A1D24", text_on_light="#1A1D24",
               text_on_dark="#F2EEE6", ink_on_light="#1A1D24", ink_on_dark="#F2EEE6",
               accent_on_light="#1A1D24", accent_on_dark="#F2EEE6")

# Lockups. S is the side of the mark's unit square (powers of two keep fine engraving free of
# moire); the visible art is what box() reports inside it. Text sizes are cap heights as
# fractions of the visible mark height H (Hs for the small mark).
LOCKUP_S = 256
HORIZONTAL = dict(gap=0.20, cap=0.22)
STACKED = dict(gap=0.16, cap=0.15)
COMPACT = dict(S=64, gap=0.30, cap=0.42)
CLEAR_SPACE = 0.25          # of H (or Hs), on every side
TINTS = (0.20, 0.55)        # coverage of ink over paper for tint-light and tint-shade (MARK_API.md)
CARD = dict(w=1280, h=640, mark_S=512, mark_cx=330, text_x=640, text_w=580, kicker_cap=15,
            title_cap=46, line_size=30, line_lead=1.35, gap_kicker=34, gap_title=40)
BANNER = dict(w=1280, h=340, mark_S=256, mark_cx=230, text_x=420, word_cap=58, line_size=26,
              place_size=20, gap=30)
README_HEADER = dict(w=1280, h=320, mark_S=256, mark_cx=210, text_x=390, word_cap=52,
                     title_size=30, line_size=22, gap=24)


# ---------------------------------------------------------------- colour
def mix(a, b, t):
    """Per-channel sRGB mix: (1 - t) * a + t * b, as #RRGGBB."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round((1 - t) * x + t * y):02X}" for x, y in zip(ca, cb))


def mark_colours(ink, paper, accent):
    return {"ink": ink, "paper": paper, "accent": accent,
            "tint-light": mix(paper, ink, TINTS[0]), "tint-shade": mix(paper, ink, TINTS[1])}


def variants(p):
    """The four colour variants of a palette: ground, text and mark colours, mono flag."""
    return {
        "on-light": dict(ground=p["ground_light"], text=p["text_on_light"], mono=False,
                         mark=mark_colours(p["ink_on_light"], p["ground_light"], p["accent_on_light"])),
        "on-dark": dict(ground=p["ground_dark"], text=p["text_on_dark"], mono=False,
                        mark=mark_colours(p["ink_on_dark"], p["ground_dark"], p["accent_on_dark"])),
        "black": dict(ground="#FFFFFF", text="#000000", mono=True,
                      mark=mark_colours("#000000", "#FFFFFF", "#000000")),
        "white": dict(ground="#000000", text="#FFFFFF", mono=True,
                      mark=mark_colours("#FFFFFF", "#000000", "#FFFFFF")),
    }


# ---------------------------------------------------------------- the mark
def load_mark(name):
    """Import brand/candidates/<name>/mark.py under a unique module name. Modules it imports
    from its own folder (for example its build.py) are dropped from sys.modules afterwards, so
    four candidates with same-named helpers can be loaded in one process."""
    folder = os.path.join(CANDIDATES, name)
    modname = f"sc_mark_{name}"
    before = set(sys.modules)
    sys.path.insert(0, folder)
    try:
        spec = importlib.util.spec_from_file_location(modname, os.path.join(folder, "mark.py"))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[modname] = mod
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(folder)
        for k in list(set(sys.modules) - before):
            f = getattr(sys.modules.get(k), "__file__", None) or ""
            if k != modname and os.path.abspath(f).startswith(folder + os.sep):
                del sys.modules[k]
    return mod


def warm_up(vc, mod):
    """Let a mark do its one-time setup while no document is open. The engraved mark outlines
    its lettering in a temporary document (its hero_art(vc)); doing that first keeps it from
    interleaving with the generator's own documents. Only a setup function that takes the
    engine is called: other candidates' hero_art() is plain geometry and needs no warm-up."""
    for name in ("prepare", "hero_art"):
        fn = getattr(mod, name, None)
        if callable(fn) and len(inspect.signature(fn).parameters) >= 1:
            fn(vc)
            return


def has_variant(mod, variant):
    return variant in getattr(mod, "VARIANTS", ("hero", "small"))


def place_mark(vc, mod, left, top, S, colours, variant="hero", mono=False):
    """Draw the mark so its VISIBLE art starts at (left, top); S is the unit square's side.
    Returns (ids, visible width, visible height)."""
    x0, y0, x1, y1 = mod.box(variant)
    ids = mod.draw_mark(vc, left - x0 * S, top - y0 * S, S, colours, variant=variant, mono=mono)
    return list(ids or []), (x1 - x0) * S, (y1 - y0) * S


def centre_mark(vc, mod, cx, cy, S, colours, variant="hero", mono=False):
    x0, y0, x1, y1 = mod.box(variant)
    w, h = (x1 - x0) * S, (y1 - y0) * S
    return place_mark(vc, mod, cx - w / 2, cy - h / 2, S, colours, variant, mono)


# ---------------------------------------------------------------- drawing helpers
def rect(vc, x, y, w, h, fill, radius=None):
    args = dict(shape="rectangle", x=x, y=y, width=w, height=h, fill=fill, stroke="none")
    if radius:
        args["radius"] = radius
    return vc.tool("draw_shape", **args)["id"]


def bounds(vc, oid):
    n = vc.cmd("document.node", id=oid, summary=True)
    return n.get("bounds") or n["summary"]["bounds"]


def move_to(vc, oid, x, y):
    b = bounds(vc, oid)
    vc.cmd("select.set", ids=[oid])
    vc.cmd("object.setBounds", x=x, y=y, width=b["width"], height=b["height"], reference=0)
    return dict(x=x, y=y, width=b["width"], height=b["height"])


def delete(vc, ids):
    vc.cmd("select.set", ids=ids)
    vc.cmd("edit.clear")


_CAP = {}


def cap_height(vc, font, style):
    """Cap height of `font` at 100 pt, measured once on an outlined H."""
    key = (font, style)
    if key not in _CAP:
        t = vc.tool("add_text", x=0, y=200, text="H", font=font, size=100, color="#000000")["id"]
        vc.cmd("text.setStyle", id=t, style=style)
        vc.cmd("select.set", ids=[t])
        g = vc.cmd("type.createOutlines")["ids"][0]
        _CAP[key] = bounds(vc, g)["height"]
        delete(vc, [g])
    return _CAP[key]


def words(vc, s, x, cap_top, cap, colour, font=FONT, style="Regular", tracking=0):
    """Outlined text whose capitals are `cap` tall with their top at cap_top and whose ink
    starts at x. Returns (group id, bounds)."""
    size = 100 * cap / cap_height(vc, font, style)
    t = vc.tool("add_text", x=x, y=cap_top + cap, text=s, font=font, size=size, color=colour)["id"]
    vc.cmd("text.setStyle", id=t, style=style, tracking=tracking)
    vc.cmd("select.set", ids=[t])
    g = vc.cmd("type.createOutlines")["ids"][0]
    b = bounds(vc, g)
    b = move_to(vc, g, x, b["y"])
    return g, b


def sized(vc, s, x, baseline, size, colour, font=FONT, style="Regular", tracking=0):
    """Outlined text at a point size with its baseline at `baseline`. Returns (id, bounds)."""
    t = vc.tool("add_text", x=x, y=baseline, text=s, font=font, size=size, color=colour)["id"]
    vc.cmd("text.setStyle", id=t, style=style, tracking=tracking)
    vc.cmd("select.set", ids=[t])
    g = vc.cmd("type.createOutlines")["ids"][0]
    return g, bounds(vc, g)


def wrap(vc, text, width, size, font=FONT, style="Regular"):
    """Greedy line breaks so no line is wider than `width` at `size`. Measures real outlines."""
    out, line = [], ""
    for w in text.split():
        trial = (line + " " + w).strip()
        g, b = sized(vc, trial, 0, 0, size, "#000000", font, style)
        delete(vc, [g])
        if b["width"] > width and line:
            out.append(line)
            line = w
        else:
            line = trial
    return out + [line]


# ---------------------------------------------------------------- lockups
def horizontal(vc, mod, x, y, S, v):
    """Mark, then the wordmark centred on the mark's visible centre. Returns (ids, w, h)."""
    p = HORIZONTAL
    ids, w, H = place_mark(vc, mod, x, y, S, v["mark"], mono=v["mono"])
    cap = p["cap"] * H
    g, b = words(vc, WORDMARK["text"], x + w + p["gap"] * H, y + H / 2 - cap / 2, cap, v["text"],
                 style=WORDMARK["style"], tracking=WORDMARK["tracking"])
    return ids + [g], b["x"] + b["width"] - x, H


def stacked(vc, mod, x, y, S, v):
    p = STACKED
    x0, y0, x1, y1 = mod.box("hero")
    w, H = (x1 - x0) * S, (y1 - y0) * S
    cap = p["cap"] * H
    g, b = words(vc, WORDMARK["text"], 0, 0, cap, v["text"], style=WORDMARK["style"])
    W = max(w, b["width"])
    ids, _, _ = place_mark(vc, mod, x + (W - w) / 2, y, S, v["mark"], mono=v["mono"])
    b2 = move_to(vc, g, x + (W - b["width"]) / 2, y + H + p["gap"] * H)
    return ids + [g], W, b2["y"] + b2["height"] - y


def compact(vc, mod, x, y, v):
    """Small mark plus wordmark, for 24 to 64 px tall uses."""
    p = COMPACT
    ids, w, Hs = place_mark(vc, mod, x, y, p["S"], v["mark"], variant="small", mono=v["mono"])
    cap = p["cap"] * Hs
    g, b = words(vc, WORDMARK["text"], x + w + p["gap"] * Hs, y + Hs / 2 - cap / 2, cap, v["text"],
                 style=WORDMARK["style"])
    return ids + [g], b["x"] + b["width"] - x, Hs


# ---------------------------------------------------------------- documents and export
class Kit:
    def __init__(self, vc, out, mark, palette_key, palette):
        self.vc, self.out, self.mark_name, self.key, self.p = vc, out, mark, palette_key, palette
        self.mod = load_mark(mark)
        warm_up(vc, self.mod)
        self.v = variants(palette)
        self.files = []
        for d in ("svg", "png", "pdf", "eps", "web", "guide", "source"):
            os.makedirs(os.path.join(out, d), exist_ok=True)

    def new(self, name, w, h, title, description):
        self.vc.cmd("file.new", width=w, height=h, units="Pixels", name=name)
        self.vc.cmd("file.info", title=title, author="SuperconducTED", description=description,
                    keywords=["SuperconducTED", "logo", self.mark_name, self.p["name"]])

    def fit(self, w, h):
        self.vc.cmd("artboard.setProps", index=0, x=0, y=0, width=round(w, 3), height=round(h, 3))

    def export(self, stem, folder="svg", vector=True, print_files=True, png=(), source=True,
               colours=None, transparent=True):
        vc, out = self.vc, self.out
        rec = dict(stem=stem, folder=folder, colours=sorted(set(colours or [])), transparent=transparent,
                   png={})
        if vector:
            vc.tool("export", path=os.path.join(out, folder, stem + ".svg"))
        if print_files:
            vc.cmd("document.export", path=os.path.join(out, "pdf", stem + ".pdf"), preserveEditing=False)
            vc.cmd("document.export", path=os.path.join(out, "eps", stem + ".eps"))
        for suffix, scale in png:
            pf = "web" if folder == "web" else ("guide" if folder == "guide" else "png")
            path = os.path.join(out, pf, f"{stem}{suffix}.png")
            vc.tool("export", path=path, scale=scale)
            rec["png"][f"{stem}{suffix}.png"] = pf
        if source:
            vc.cmd("document.save", path=os.path.join(out, "source", stem + ".vectorcraft"), compress=True)
        vc.cmd("file.close")
        rec["vector"] = vector
        rec["print"] = print_files
        rec["source"] = source
        self.files.append(rec)

    def allowed(self, v, extra=()):
        """Colours a file of this variant may contain. A mark that shades with mixes of its
        role colours (the isometric brackets) lists what it paints through colours_used()."""
        m = v["mark"]
        out = [m["ink"], m["paper"], m["accent"], m["tint-light"], m["tint-shade"], v["text"], *extra]
        used = getattr(self.mod, "colours_used", None)
        if callable(used):
            for variant in ("hero", "small"):
                out += list(used(m, variant, v["mono"]))
        return out

    # -------------------------------------------------------- marks and lockups
    def marks(self):
        for vname, v in self.v.items():
            self.new(f"mark-{vname}", 1024, 1024, "SuperconducTED mark", f"The hero mark, {vname}.")
            self.mod.draw_mark(self.vc, 0, 0, 1024, v["mark"], variant="hero", mono=v["mono"])
            self.export(f"superconducted-mark-{vname}", png=[(f"-{px}", px / 1024) for px in (128, 256, 512, 1024)],
                        colours=self.allowed(v))
            # A design with a hand-hinted 16 px drawing (variant "small16") gets its 16 px file
            # from that drawing; scaling the 32-grid small mark down lands edges on half pixels.
            hinted = has_variant(self.mod, "small16")
            sizes = (24, 32, 48, 64) if hinted else (16, 24, 32, 48, 64)
            self.new(f"mark-small-{vname}", 64, 64, "SuperconducTED mark, small", f"The small mark, {vname}.")
            self.mod.draw_mark(self.vc, 0, 0, 64, v["mark"], variant="small", mono=v["mono"])
            self.export(f"superconducted-mark-small-{vname}", print_files=False,
                        png=[(f"-{px}", px / 64) for px in sizes], colours=self.allowed(v))
            if hinted:
                self.new(f"mark-small16-{vname}", 16, 16, "SuperconducTED mark, 16 px", f"Hinted 16 px mark, {vname}.")
                self.mod.draw_mark(self.vc, 0, 0, 16, v["mark"], variant="small16", mono=v["mono"])
                self.export(f"superconducted-mark-small-{vname}", vector=False, print_files=False,
                            png=[("-16", 1)], source=False, colours=self.allowed(v))

    def lockups(self):
        for vname, v in self.v.items():
            for kind, fn in (("horizontal", horizontal), ("stacked", stacked)):
                self.new(f"{kind}-{vname}", 3000, 1600, f"SuperconducTED, {kind} lockup", f"{kind} lockup, {vname}.")
                _, w, h = fn(self.vc, self.mod, 0, 0, LOCKUP_S, v)
                self.fit(w, h)
                self.export(f"superconducted-{kind}-{vname}", png=[("", 1), ("@2x", 2), ("@4x", 4)],
                            colours=self.allowed(v))
            self.new(f"compact-{vname}", 1600, 200, "SuperconducTED, compact lockup", f"Compact lockup, {vname}.")
            _, w, h = compact(self.vc, self.mod, 0, 0, v)
            self.fit(w, h)
            self.export(f"superconducted-compact-{vname}", png=[("", 1), ("@2x", 2), ("@4x", 4)],
                        colours=self.allowed(v))

    # -------------------------------------------------------- web
    def web(self):
        v, vc = self.v["on-dark"], self.vc
        ground = v["ground"]
        # Favicon: the small mark on a ground tile at every size, so the tab icon keeps one shape.
        # The small marks are drawn on a 32-unit grid with their own margins, so they fill the
        # tile's full square: scaled to 32 px every edge lands on a whole pixel. Shrinking them
        # to leave a margin would put edges on fractions of a pixel and blur them.
        self.new("favicon", 64, 64, "SuperconducTED favicon", "Small mark on a tile, for 16 to 48 px.")
        rect(vc, 0, 0, 64, 64, ground, radius=12)
        self.mod.draw_mark(vc, 0, 0, 64, v["mark"], variant="small")
        # The tile's rounded corners are transparent on purpose, so the corner check does not apply.
        self.export("favicon", folder="web", print_files=False, png=[("-32", 0.5), ("-48", 0.75)],
                    colours=self.allowed(v, [ground]), transparent=True)
        small16 = "small16" if has_variant(self.mod, "small16") else "small"
        self.new("favicon-16", 16, 16, "SuperconducTED favicon, 16 px", "Hinted 16 px favicon.")
        rect(vc, 0, 0, 16, 16, ground, radius=3)
        # A hand-hinted drawing is one unit square per pixel: draw it at exactly 16 px from (0, 0).
        self.mod.draw_mark(vc, 0, 0, 16, v["mark"], variant=small16)
        self.export("favicon-16", folder="web", vector=False, print_files=False, png=[("", 1)], source=False,
                    transparent=True)
        # App icon: the hero on a square tile; platforms round the corners themselves.
        self.new("app-icon", 512, 512, "SuperconducTED app icon", "Hero mark on a tile, 180 px and up.")
        rect(vc, 0, 0, 512, 512, ground)
        centre_mark(vc, self.mod, 256, 256, 448, v["mark"])
        self.export("app-icon", folder="web", print_files=False,
                    png=[("-180", 180 / 512), ("-192", 192 / 512), ("-512", 1)],
                    colours=self.allowed(v, [ground]), transparent=False)
        # Organisation avatar.
        self.new("avatar", 1024, 1024, "SuperconducTED avatar", "Organisation avatar: the hero on its ground.")
        rect(vc, 0, 0, 1024, 1024, ground)
        centre_mark(vc, self.mod, 512, 512, 896, v["mark"])
        self.export("avatar", folder="web", print_files=False, png=[("-500", 500 / 1024), ("-1024", 1)],
                    colours=self.allowed(v, [ground]), transparent=False)

    def banner(self):
        """The organisation profile banner, 1280 x 340 (the size of today's header.svg)."""
        b, v, vc = BANNER, self.v["on-dark"], self.vc
        self.new("profile-header", b["w"], b["h"], "SuperconducTED", "SuperconducTED, TED University, Ankara.")
        rect(vc, 0, 0, b["w"], b["h"], v["ground"])
        centre_mark(vc, self.mod, b["mark_cx"], b["h"] / 2, b["mark_S"], v["mark"])
        lines = wrap(vc, ORG_LINE, b["w"] - b["text_x"] - 60, b["line_size"])
        block = b["word_cap"] + b["gap"] + len(lines) * b["line_size"] * 1.35 + b["gap"] * 0.6 + b["place_size"]
        top = b["h"] / 2 - block / 2
        words(vc, WORDMARK["text"], b["text_x"], top, b["word_cap"], v["text"], style=WORDMARK["style"])
        y = top + b["word_cap"] + b["gap"] + b["line_size"]
        for ln in lines:
            sized(vc, ln, b["text_x"], y, b["line_size"], v["text"])
            y += b["line_size"] * 1.35
        sized(vc, PLACE_LINE, b["text_x"], y + b["gap"] * 0.6 - b["line_size"] * 0.35 + b["place_size"] * 0.4,
              b["place_size"], v["text"], font=MONO)
        self.export("profile-header", folder="web", print_files=False, png=[("", 1), ("@2x", 2)],
                    colours=self.allowed(v, [v["ground"]]), transparent=False)

    def readme_header(self):
        r, v, vc = README_HEADER, self.v["on-dark"], self.vc
        self.new("readme-header-noise-engine", r["w"], r["h"], "SuperconducTED noise engine",
                 REPO_CARDS["noise-engine"]["line"])
        rect(vc, 0, 0, r["w"], r["h"], v["ground"])
        centre_mark(vc, self.mod, r["mark_cx"], r["h"] / 2, r["mark_S"], v["mark"])
        lines = wrap(vc, REPO_CARDS["noise-engine"]["line"], r["w"] - r["text_x"] - 60, r["line_size"])
        block = r["word_cap"] + r["gap"] + r["title_size"] + r["gap"] * 0.6 + len(lines) * r["line_size"] * 1.35
        top = r["h"] / 2 - block / 2
        words(vc, WORDMARK["text"], r["text_x"], top, r["word_cap"], v["text"], style=WORDMARK["style"])
        y = top + r["word_cap"] + r["gap"] + r["title_size"]
        sized(vc, "noise engine", r["text_x"], y, r["title_size"], v["text"], font=MONO)
        y += r["gap"] * 0.6 + r["line_size"] * 1.35
        for ln in lines:
            sized(vc, ln, r["text_x"], y, r["line_size"], v["text"])
            y += r["line_size"] * 1.35
        self.export("readme-header-noise-engine", folder="web", print_files=False, png=[("", 1), ("@2x", 2)],
                    colours=self.allowed(v, [v["ground"]]), transparent=False)

    def cards(self):
        """Social preview cards, 1280 x 640 (GitHub's recommended size)."""
        c, v, vc = CARD, self.v["on-dark"], self.vc
        # The organisation's card carries the tagline; the repository cards their descriptions.
        specs = [("social-card", None, "SuperconducTED", TAGLINE)]
        # The kicker keeps the name's own casing: capitals only belong to lettering drawn into a mark.
        specs += [(f"social-card-{k}", "SuperconducTED", s["title"], s["line"]) for k, s in REPO_CARDS.items()]
        for stem, kicker, title, line in specs:
            self.new(stem, c["w"], c["h"], f"{title} social card", line)
            rect(vc, 0, 0, c["w"], c["h"], v["ground"])
            centre_mark(vc, self.mod, c["mark_cx"], c["h"] / 2, c["mark_S"], v["mark"])
            lines = wrap(vc, line, c["text_w"], c["line_size"])
            step = c["line_size"] * c["line_lead"]
            block = ((c["kicker_cap"] + c["gap_kicker"]) if kicker else 0) + c["title_cap"] + c["gap_title"] \
                + c["line_size"] + step * (len(lines) - 1)
            y = c["h"] / 2 - block / 2
            widths = []
            if kicker:
                _, kb = words(vc, kicker, c["text_x"], y, c["kicker_cap"], v["text"], font=MONO, tracking=60)
                widths.append(kb["width"])
                y += c["kicker_cap"] + c["gap_kicker"]
            _, tb = words(vc, title, c["text_x"], y, c["title_cap"], v["text"], style=WORDMARK["style"])
            widths.append(tb["width"])
            y += c["title_cap"] + c["gap_title"] + c["line_size"]
            for ln in lines:
                _, lb = sized(vc, ln, c["text_x"], y, c["line_size"], v["text"])
                widths.append(lb["width"])
                y += step
            if max(widths) > c["text_w"] + 1:
                raise ValueError(f"{stem}: a line is {max(widths):.0f} px wide, the column is {c['text_w']} px")
            self.export(stem, folder="web", print_files=False, png=[("", 1)],
                        colours=self.allowed(v, [v["ground"]]), transparent=False)

    # -------------------------------------------------------- guide
    def guide(self):
        vc, p = self.vc, self.p
        rows = [("Ground, light", p["ground_light"]), ("Ground, dark", p["ground_dark"]),
                ("Ink on light", p["ink_on_light"]), ("Ink on dark", p["ink_on_dark"]),
                ("Accent on light (the range)", p["accent_on_light"]), ("Accent on dark (the range)", p["accent_on_dark"])]
        seen, uniq = set(), []
        for name, hx in rows:
            if hx not in seen:
                seen.add(hx)
                uniq.append((name, hx))
        rs = palettes.ratios(p)
        W, ROW = 1400, 120
        H = 110 + ROW * len(uniq) + 150
        self.new("palette", W, H, f"SuperconducTED palette: {p['name']}", p["why"])
        rect(vc, 0, 0, W, H, "#FFFFFF")
        sized(vc, f"{p['name']}: {p['why']}", 40, 60, 24, "#111111", style="Medium")
        # color.convert answers with CMYK as fractions 0..1 through VectorCraft's "Generic CMYK
        # (SWOP-like)" profile; shown here as percentages. Colours outside that gamut are
        # flagged with their colour difference, so they are proofed before a print run.
        cmyk, gamut = {}, {}
        for i, (name, hx) in enumerate(uniq):
            y = 100 + i * ROW
            vc.tool("draw_shape", shape="rectangle", x=40, y=y, width=90, height=90, fill=hx,
                    stroke="#BBBBBB", strokeWidth=1)
            c = vc.cmd("color.convert", color=hx, to="cmyk")
            cmyk[hx] = [round(100 * x) for x in c["values"]]
            gamut[hx] = dict(out_of_gamut=bool(c.get("outOfGamut")), delta_e=round(c.get("deltaE") or 0.0, 1))
            rgb = " ".join(str(int(hx[k:k + 2], 16)) for k in (1, 3, 5))
            note = f"   out of CMYK gamut (dE {gamut[hx]['delta_e']}): proof before printing" \
                if gamut[hx]["out_of_gamut"] else ""
            sized(vc, f"{name}   {hx}", 160, y + 34, 22, "#111111", font=MONO)
            sized(vc, f"RGB {rgb}    CMYK {' '.join(map(str, cmyk[hx]))} (approx.){note}", 160, y + 70, 18,
                  "#444444", font=MONO)
        y = 100 + ROW * len(uniq) + 30
        for k, (what, r) in enumerate(rs.items()):
            target = palettes.TEXT_MIN if what.startswith("text") else palettes.GRAPHIC_MIN
            sized(vc, f"{what}: {r:.2f}:1 (target {target}:1)", 40 + (k % 2) * 650, y + (k // 2) * 34, 18,
                  "#222222", font=MONO)
        self.export("palette", folder="guide", print_files=False, png=[("", 1)], source=False, transparent=False)
        with open(os.path.join(self.out, "guide", "palette.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(key=self.key, palette=p, cmyk_percent=cmyk, cmyk_gamut=gamut,
                           cmyk_profile="VectorCraft Generic CMYK (SWOP-like)",
                           ratios={k: round(v, 2) for k, v in rs.items()}), f, indent=2)
        # Clear space around the primary lockup.
        v = self.v["on-light"]
        self.new("clear-space", 1700, 700, "SuperconducTED clear space", "Keep X = 0.25 H free on every side.")
        rect(vc, 0, 0, 1700, 700, "#FFFFFF")
        ids, w, h = horizontal(vc, self.mod, 0, 0, LOCKUP_S, v)
        X = CLEAR_SPACE * h
        ox, oy = (1700 - w) / 2, 160
        vc.cmd("select.set", ids=ids)
        g = vc.cmd("object.group")["id"]
        move_to(vc, g, ox, oy)
        vc.tool("draw_shape", shape="rectangle", x=ox - X, y=oy - X, width=w + 2 * X, height=h + 2 * X,
                fill="none", stroke="#B04A2E", strokeWidth=1.5)
        for qx, qy in ((ox - X, oy - X), (ox + w, oy + h)):
            rect(vc, qx, qy, X, X, "#F3D9CF")
        sized(vc, "X = 0.25 H, where H is the height of the mark", ox - X, oy + h + X + 50, 22, "#111111")
        self.export("clear-space", folder="guide", print_files=False, png=[("", 1)], source=False, transparent=False)

    def board(self):
        """One overview image: lockups on both grounds, the mark small, the card."""
        vc = self.vc
        W, H = 2400, 1400
        self.new("brand-board", W, H, "SuperconducTED brand board", f"{self.mark_name}, {self.p['name']}.")
        for i, vname in enumerate(("on-light", "on-dark")):
            v = self.v[vname]
            rect(vc, i * W / 2, 0, W / 2, 900, v["ground"])
            ids, w, h = horizontal(vc, self.mod, 0, 0, LOCKUP_S, v)
            vc.cmd("select.set", ids=ids)
            g = vc.cmd("object.group")["id"]
            scale = min(1.0, (W / 2 - 160) / w)
            vc.cmd("object.setBounds", x=i * W / 2 + (W / 2 - w * scale) / 2, y=80, width=w * scale,
                   height=h * scale, reference=0)
            centre_mark(vc, self.mod, i * W / 2 + W / 4, 620, 384, v["mark"])
        for i, vname in enumerate(("black", "white")):
            v = self.v[vname]
            rect(vc, i * W / 2, 900, W / 2, 500, v["ground"])
            for k, px in enumerate((256, 128, 64)):
                centre_mark(vc, self.mod, i * W / 2 + 200 + k * 300, 1150, px, v["mark"], mono=True)
            for k, px in enumerate((32, 16)):
                centre_mark(vc, self.mod, i * W / 2 + 1000 + k * 80, 1150, px, v["mark"], variant="small", mono=True)
        self.export("brand-board", folder="guide", vector=False, print_files=False, png=[("", 1)], source=False,
                    transparent=False)

    def manifest(self):
        with open(os.path.join(self.out, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(dict(mark=self.mark_name, palette=self.key, files=self.files), f, indent=2)

    def build_all(self):
        for step in (self.marks, self.lockups, self.web, self.banner, self.readme_header, self.cards,
                     self.guide, self.board):
            print(f"  {self.mark_name}/{self.key}: {step.__name__}", flush=True)
            step()
        self.manifest()


# ---------------------------------------------------------------- decision aids
def place_png(vc, path, x, y, w, h):
    oid = vc.cmd("file.place", path=path, link=False)["ids"][0]
    vc.cmd("select.set", ids=[oid])
    vc.cmd("object.setBounds", x=x, y=y, width=w, height=h, reference=0)
    return oid


def in_use_sheet(vc, kit_dir, mark, out_png):
    """One candidate in use: avatar at GitHub's sizes, favicon in a tab, banner, social card."""
    W, H = 2000, 1500
    vc.cmd("file.new", width=W, height=H, units="Pixels", name=f"in-use-{mark}")
    rect(vc, 0, 0, W, H, "#FFFFFF")
    web = os.path.join(kit_dir, "web")
    sized(vc, f"{mark}: in use (neutral colours; palette not chosen yet)", 40, 60, 30, "#111111", style="Medium")
    # Banner, full width.
    place_png(vc, os.path.join(web, "profile-header.png"), 40, 100, 1280, 340)
    sized(vc, "Organisation profile banner, 1280 x 340", 40, 470, 18, "#555555")
    # Avatar at the sizes GitHub shows an organisation avatar.
    x = 1360
    for px in (200, 48, 20):
        rect(vc, x - 2, 100 - 2, px + 4, px + 4, "#E6E6E6", radius=px * 0.12)
        place_png(vc, os.path.join(web, "avatar-1024.png"), x, 100, px, px)
        x += px + 30
    sized(vc, "Avatar at 200, 48 and 20 px", 1360, 340, 18, "#555555")
    # A browser tab with the favicon.
    rect(vc, 1360, 380, 560, 60, "#DEE1E6", radius=10)
    rect(vc, 1372, 390, 300, 50, "#FFFFFF", radius=8)
    place_png(vc, os.path.join(web, "favicon-16.png"), 1386, 407, 16, 16)
    sized(vc, "SuperconducTED", 1412, 421, 16, "#222222")
    sized(vc, "Favicon at 16 px in a tab", 1360, 470, 18, "#555555")
    # Social card and README header.
    place_png(vc, os.path.join(web, "social-card-noise-engine.png"), 40, 520, 960, 480)
    sized(vc, "Repository social card, 1280 x 640, shown at 75 %", 40, 1030, 18, "#555555")
    place_png(vc, os.path.join(web, "readme-header-noise-engine.png"), 1040, 520, 920, 230)
    sized(vc, "README header for the noise engine, shown at 72 %", 1040, 780, 18, "#555555")
    comp =os.path.join(kit_dir, "png", "superconducted-compact-on-light@2x.png")
    oid = vc.cmd("file.place", path=comp, link=False)["ids"][0]
    b = bounds(vc, oid)
    s = 64 / b["height"]
    vc.cmd("select.set", ids=[oid])
    vc.cmd("object.setBounds", x=1040, y=830, width=b["width"] * s, height=64, reference=0)
    sized(vc, "Compact lockup at 32 px tall (small mark), for navigation bars", 1040, 930, 18, "#555555")
    hz = os.path.join(kit_dir, "png", "superconducted-horizontal-on-light.png")
    oid = vc.cmd("file.place", path=hz, link=False)["ids"][0]
    b = bounds(vc, oid)
    s = min(1.0, 1880 / b["width"], 330 / b["height"])
    vc.cmd("select.set", ids=[oid])
    vc.cmd("object.setBounds", x=40, y=1080, width=b["width"] * s, height=b["height"] * s, reference=0)
    sized(vc, "Primary horizontal lockup", 40, 1450, 18, "#555555")
    vc.tool("export", path=out_png)
    vc.cmd("file.close")


def palette_sheet(vc, scratch, out_png, figures_demo=None):
    """Every palette option on every candidate: hero on the dark and the light ground."""
    keys = list(palettes.OPTIONS)
    cell, pad = 190, 14
    W = 360 + len(MARKS) * 2 * (cell + pad) + (cell * 2 + pad if figures_demo else 0) + 40
    H = 120 + len(keys) * (cell + 50)
    tiles = os.path.join(scratch, "_tiles")
    os.makedirs(tiles, exist_ok=True)
    mods = {m: load_mark(m) for m in MARKS}
    for mod in mods.values():
        warm_up(vc, mod)
    for key in keys:
        p = palettes.OPTIONS[key]
        for m in MARKS:
            for vname in ("on-dark", "on-light"):
                v = variants(p)[vname]
                vc.cmd("file.new", width=512, height=512, units="Pixels", name=f"t-{key}-{m}-{vname}")
                rect(vc, 0, 0, 512, 512, v["ground"])
                centre_mark(vc, mods[m], 256, 256, 448, v["mark"])
                vc.tool("export", path=os.path.join(tiles, f"{key}-{m}-{vname}.png"))
                vc.cmd("file.close")
    vc.cmd("file.new", width=W, height=H, units="Pixels", name="palettes")
    rect(vc, 0, 0, W, H, "#FFFFFF")
    sized(vc, "Palette options on every candidate (hero on the dark ground, then the light ground). "
              "The accent marks only the range.", 40, 60, 24, "#111111", style="Medium")
    for i, key in enumerate(keys):
        p = palettes.OPTIONS[key]
        y = 110 + i * (cell + 50)
        sized(vc, p["name"], 40, y + 30, 24, "#111111", style="Medium")
        for k, hx in enumerate((p["ground_dark"], p["ground_light"], p["ink_on_light"], p["accent_on_light"],
                                p["accent_on_dark"])):
            rect(vc, 40 + k * 56, y + 50, 48, 48, hx)
        rs = palettes.ratios(p)
        sized(vc, f"accent {rs['accent on light']:.2f}:1 light, {rs['accent on dark']:.2f}:1 dark", 40, y + 130, 15,
              "#444444", font=MONO)
        x = 360
        for m in MARKS:
            for vname in ("on-dark", "on-light"):
                place_png(vc, os.path.join(tiles, f"{key}-{m}-{vname}.png"), x, y, cell, cell)
                x += cell + pad
        if figures_demo and os.path.exists(os.path.join(figures_demo, f"{key}.png")):
            oid = vc.cmd("file.place", path=os.path.join(figures_demo, f"{key}.png"), link=False)["ids"][0]
            b = bounds(vc, oid)
            s = min((2 * cell + pad) / b["width"], cell / b["height"])
            vc.cmd("select.set", ids=[oid])
            vc.cmd("object.setBounds", x=x, y=y, width=b["width"] * s, height=b["height"] * s, reference=0)
    for j, m in enumerate(MARKS):
        sized(vc, m, 360 + j * 2 * (cell + pad), 100, 16, "#555555", font=MONO)
    vc.tool("export", path=out_png)
    vc.cmd("file.close")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    # Defaults are the identity's own choices (palettes.MARK and palettes.CHOSEN, 2026-10-16), so
    # `build_brand.py --out brand/kit` rebuilds the official kit.
    ap.add_argument("--mark", choices=MARKS, default=palettes.MARK)
    ap.add_argument("--palette", choices=list(palettes.OPTIONS) + ["neutral"], default=palettes.CHOSEN)
    ap.add_argument("--out")
    ap.add_argument("--decision", action="store_true")
    ap.add_argument("--scratch")
    a = ap.parse_args()
    if palettes.check():
        raise SystemExit(f"palette contrast failures: {palettes.check()}")
    if a.decision:
        # The engine is confined to the scratch folder: the chart demos are copied in first and
        # the finished sheets copied out to brand/decision/ at the end.
        if not a.scratch:
            raise SystemExit("--decision needs --scratch <short folder>")
        scratch = os.path.abspath(a.scratch)
        os.makedirs(scratch, exist_ok=True)
        demo_src, demo = os.path.join(BRAND, "figures", "demo"), os.path.join(scratch, "_figures")
        if os.path.isdir(demo_src):
            shutil.copytree(demo_src, demo, dirs_exist_ok=True)
        sheets = []
        with VC(scratch) as vc:
            for m in MARKS:
                kit_dir = os.path.join(scratch, m)
                Kit(vc, kit_dir, m, "neutral", NEUTRAL).build_all()
                sheets.append(os.path.join(scratch, f"in-use-{m}.png"))
                in_use_sheet(vc, kit_dir, m, sheets[-1])
            sheets.append(os.path.join(scratch, "palettes.png"))
            palette_sheet(vc, scratch, sheets[-1], figures_demo=demo if os.path.isdir(demo) else None)
        decision = os.path.join(BRAND, "decision")
        os.makedirs(decision, exist_ok=True)
        for s in sheets:
            shutil.copyfile(s, os.path.join(decision, os.path.basename(s)))
        print("decision aids written to", decision)
        return
    if not a.out:
        raise SystemExit("give --out (and optionally --mark, --palette), or --decision --scratch")
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    p = NEUTRAL if a.palette == "neutral" else palettes.OPTIONS[a.palette]
    with VC(out) as vc:
        Kit(vc, out, a.mark, a.palette, p).build_all()
    print("kit written to", out)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Show or change the app's accent, one of the house palette's colors.

    python3 scripts/accent.py           # list the palettes, the current one marked
    python3 scripts/accent.py teal      # switch: the tokens and the favicon, in place

The scaffold picked one from the project's name. Switching rewrites
the accent family (--accent, --on-accent, --accent-deep, --on-deep,
--accent-tint, --bg-glow) in the stylesheet's :root and both dark
blocks, the favicon in index.html and the placeholder page's colors.
The chart series mix from --accent, so they follow. A user's brand
replaces these values by hand instead. Standard library only; runs on
the system python3 (3.9 and up). The palettes are the plugin's
skills/build/templates/palettes.json.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PALETTES = {
    "teal": {
        "light": {"accent": "#076c6a", "on-accent": "#ffffff", "accent-deep": "#023534", "on-deep": "#f4f4f7", "accent-tint": "#d5f0ee", "bg-glow": "#e4efee"},
        "dark": {"accent": "#4bc2be", "on-accent": "#012221", "accent-deep": "#011514", "on-deep": "#e4efee", "accent-tint": "#003231", "bg-glow": "#101f1e"},
    },
    "cyan": {
        "light": {"accent": "#026983", "on-accent": "#ffffff", "accent-deep": "#00435a", "on-deep": "#f4f4f7", "accent-tint": "#d6eef8", "bg-glow": "#e4eef2"},
        "dark": {"accent": "#48bee2", "on-accent": "#00212a", "accent-deep": "#00141b", "on-deep": "#e4eef2", "accent-tint": "#00303d", "bg-glow": "#111e23"},
    },
    "blue": {
        "light": {"accent": "#0163ac", "on-accent": "#ffffff", "accent-deep": "#012f55", "on-deep": "#f4f4f7", "accent-tint": "#dcecfd", "bg-glow": "#e6edf4"},
        "dark": {"accent": "#6eb6fe", "on-accent": "#001d39", "accent-deep": "#001126", "on-deep": "#e6edf4", "accent-tint": "#0d2c49", "bg-glow": "#151d26"},
    },
    "indigo": {
        "light": {"accent": "#3351df", "on-accent": "#ffffff", "accent-deep": "#13226e", "on-deep": "#f4f4f7", "accent-tint": "#e1e9fe", "bg-glow": "#e9ecf5"},
        "dark": {"accent": "#9cacfe", "on-accent": "#131642", "accent-deep": "#060e2b", "on-deep": "#e9ecf5", "accent-tint": "#1c284a", "bg-glow": "#181c26"},
    },
    "violet": {
        "light": {"accent": "#5b3fd6", "on-accent": "#ffffff", "accent-deep": "#2b1a6b", "on-deep": "#f4f4f7", "accent-tint": "#ebe6fb", "bg-glow": "#ecebf4"},
        "dark": {"accent": "#b4a1ff", "on-accent": "#1b1340", "accent-deep": "#0f0b2a", "on-deep": "#ecebf4", "accent-tint": "#2a2448", "bg-glow": "#1a1b26"},
    },
    "purple": {
        "light": {"accent": "#8734c9", "on-accent": "#ffffff", "accent-deep": "#3e1061", "on-deep": "#f4f4f7", "accent-tint": "#eee5fa", "bg-glow": "#eeeaf3"},
        "dark": {"accent": "#c99ef9", "on-accent": "#260e3a", "accent-deep": "#170826", "on-deep": "#eeeaf3", "accent-tint": "#322144", "bg-glow": "#1e1a24"},
    },
    "plum": {
        "light": {"accent": "#a0309a", "on-accent": "#ffffff", "accent-deep": "#4e034c", "on-deep": "#f4f4f7", "accent-tint": "#f5e3f3", "bg-glow": "#f1e9f0"},
        "dark": {"accent": "#e099da", "on-accent": "#30092e", "accent-deep": "#1f051d", "on-deep": "#f1e9f0", "accent-tint": "#3c1d39", "bg-glow": "#221821"},
    },
    "rose": {
        "light": {"accent": "#b7186e", "on-accent": "#ffffff", "accent-deep": "#570131", "on-deep": "#f4f4f7", "accent-tint": "#fbe2ea", "bg-glow": "#f3e9ec"},
        "dark": {"accent": "#f295ba", "on-accent": "#37051e", "accent-deep": "#240312", "on-deep": "#f3e9ec", "accent-tint": "#421b2c", "bg-glow": "#24181c"},
    },
}

# The files that carry the accent, when the project has them.
STYLESHEETS = ("web/src/styles.css", "frontend/styles.css", "frontend/mcp/styles.css")
FAVICONS = ("web/index.html", "frontend/web/index.html")
OTHERS = ("scripts/placeholder.py",)

# An innermost `selector { body }` block.
BLOCK = re.compile(r"([^{}]*)\{([^{}]*)\}")
RECT_FILL = re.compile(r"(%3Crect(?:(?!%3E).)*?fill='%23)[0-9a-fA-F]{6}")
TEXT_FILL = re.compile(r"(%3Ctext(?:(?!%3E).)*?fill='%23)[0-9a-fA-F]{6}")


def scheme_of(selector: str, body: str) -> str | None:
    """'light' or 'dark' for a :root block that sets color-scheme."""
    lines = selector.strip().splitlines()
    if not lines or not lines[-1].strip().startswith(":root"):
        return None
    if "color-scheme: dark" in body:
        return "dark"
    if "color-scheme: light" in body:
        return "light"
    return None


def apply_tokens(text: str, palette: dict) -> str:
    """`text` with each :root block's accent tokens set from `palette`."""
    def block(match: re.Match) -> str:
        selector, body = match.group(1), match.group(2)
        scheme = scheme_of(selector, body)
        if scheme is None:
            return match.group(0)
        for token, value in palette[scheme].items():
            body = re.sub(r"(--%s:\s*)#[0-9a-fA-F]{3,8}\b" % re.escape(token),
                          lambda m: m.group(1) + value, body)
        return selector + "{" + body + "}"
    return BLOCK.sub(block, text)


def apply_favicon(text: str, palette: dict) -> str:
    light = palette["light"]
    text = RECT_FILL.sub(lambda m: m.group(1) + light["accent"].lstrip("#"), text)
    return TEXT_FILL.sub(lambda m: m.group(1) + light["on-accent"].lstrip("#"), text)


def current(root: Path = ROOT) -> str | None:
    """The palette the project's stylesheet uses, or None (a brand's own)."""
    for rel in STYLESHEETS:
        path = root / rel
        if not path.is_file():
            continue
        for match in BLOCK.finditer(path.read_text(encoding="utf-8")):
            if scheme_of(match.group(1), match.group(2)) != "light":
                continue
            found = re.search(r"--accent:\s*(#[0-9a-fA-F]{3,8})\b", match.group(2))
            if found:
                value = found.group(1).lower()
                return next((n for n, p in PALETTES.items()
                             if p["light"]["accent"] == value), None)
    return None


def switch(name: str, root: Path = ROOT) -> list[str]:
    """Rewrite every file that carries the accent; returns the changed ones."""
    palette = PALETTES[name]
    changed = []
    for rel in STYLESHEETS + OTHERS + FAVICONS:
        path = root / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        new = apply_favicon(text, palette) if rel in FAVICONS else apply_tokens(text, palette)
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(rel)
    return changed


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (argv and argv[0].startswith("-")):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    now = current()
    if not argv:
        for name, palette in PALETTES.items():
            mark = "*" if name == now else " "
            print(f"{mark} {name:<7} {palette['light']['accent']} light, "
                  f"{palette['dark']['accent']} dark")
        if now is None:
            print("  (the stylesheet's accent is none of these: a brand's own)")
        return 0
    name = argv[0]
    if name not in PALETTES:
        print(f"accent: no palette '{name}'; one of: {', '.join(PALETTES)}", file=sys.stderr)
        return 2
    changed = switch(name)
    print(f"Accent: {name}" + (f" ({', '.join(changed)})" if changed else " (already)"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Tests for the house palette (skills/build/templates/palettes.json):
every accent passes WCAG contrast against the template stylesheet's own
page, panel and ink in light and dark, none reads as green, amber or
red (--good, --warn and --bad own those), violet is the templates'
values exactly, and each template's scripts/accent.py carries the same
palettes.

    python3 tests/templates/palettes_test.py
"""

import colorsys
import importlib.util
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES = ROOT / "skills" / "build" / "templates"
PALETTES = json.loads((TEMPLATES / "palettes.json").read_text())["palettes"]
STYLES = (TEMPLATES / "web-app" / "web" / "src" / "styles.css").read_text()
TOKENS = ("accent", "on-accent", "accent-deep", "on-deep", "accent-tint", "bg-glow")

# HSL hue bands the accent stays out of.
BANDS = {"red": [(0, 20), (345, 360)], "amber": [(20, 70)], "green": [(70, 165)]}


def rgb(value: str) -> tuple:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))


def luminance(value: str) -> float:
    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (linear(c) for c in rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + 0.05) / (lo + 0.05)


def hue(value: str) -> float:
    return colorsys.rgb_to_hls(*rgb(value))[0] * 360


def scheme_block(scheme: str) -> str:
    """The body of the stylesheet's light :root block or first dark block."""
    if scheme == "light":
        return STYLES[STYLES.index(":root {"):].split("}", 1)[0]
    start = STYLES.index(':root:not([data-theme="light"]) {')
    return STYLES[start:].split("}", 1)[0]


def token(block: str, name: str) -> str:
    return re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{6}})", block).group(1).lower()


class PalettesTest(unittest.TestCase):
    def test_eight_named_palettes_with_every_token(self) -> None:
        names = [p["name"] for p in PALETTES]
        self.assertEqual(len(names), 8)
        self.assertEqual(len(set(names)), 8, "names are unique")
        for p in PALETTES:
            for scheme in ("light", "dark"):
                self.assertEqual(sorted(p[scheme]), sorted(TOKENS), f"{p['name']} {scheme}")
                for value in p[scheme].values():
                    self.assertRegex(value, r"^#[0-9a-f]{6}$", p["name"])

    def test_violet_is_the_templates_own(self) -> None:
        violet = next(p for p in PALETTES if p["name"] == "violet")
        for scheme in ("light", "dark"):
            block = scheme_block(scheme)
            for name in TOKENS:
                self.assertEqual(violet[scheme][name], token(block, name), f"{scheme} --{name}")

    def test_contrast(self) -> None:
        for scheme in ("light", "dark"):
            block = scheme_block(scheme)
            bg, panel, ink = token(block, "bg"), token(block, "panel"), token(block, "ink")
            for p in PALETTES:
                t = p[scheme]
                pairs = [
                    ("--on-accent on --accent", t["on-accent"], t["accent"], 4.5),
                    ("white on --accent-deep", "#ffffff", t["accent-deep"], 7),
                    ("--on-deep on --accent-deep", t["on-deep"], t["accent-deep"], 7),
                    ("--ink on --accent-tint", ink, t["accent-tint"], 7),
                    ("--accent on --bg", t["accent"], bg, 4.5),
                    ("--accent on --panel", t["accent"], panel, 4.5),
                ]
                if scheme == "light":
                    pairs.append(("--on-accent on --accent-deep", t["on-accent"], t["accent-deep"], 7))
                for what, fg, back, least in pairs:
                    with self.subTest(palette=p["name"], scheme=scheme, pair=what):
                        self.assertGreaterEqual(round(contrast(fg, back), 2), least)

    def test_no_accent_reads_as_green_amber_or_red(self) -> None:
        for p in PALETTES:
            for scheme in ("light", "dark"):
                h = hue(p[scheme]["accent"])
                for band, ranges in BANDS.items():
                    with self.subTest(palette=p["name"], scheme=scheme):
                        self.assertFalse(any(lo <= h < hi for lo, hi in ranges),
                                         f"{p['name']} {scheme} accent hue {h:.0f} is {band}")

    def test_each_templates_accent_script_carries_the_palettes(self) -> None:
        want = {p["name"]: {"light": p["light"], "dark": p["dark"]} for p in PALETTES}
        texts = set()
        for template in ("web-app", "mcp-ui", "both"):
            path = TEMPLATES / template / "scripts" / "accent.py"
            spec = importlib.util.spec_from_file_location(f"accent_{template.replace('-', '_')}", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(module.PALETTES, want, path)
            self.assertEqual(list(module.PALETTES), list(want), "same order")
            texts.add(path.read_text())
        self.assertEqual(len(texts), 1, "the three copies are identical")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Checks the template stylesheets.

    python3 tools/style-check.py                  # the copies agree (no browser)
    python3 tools/style-check.py --write          # rewrite the copies from the source
    python3 tools/style-check.py --browser        # also render tools/style-check.html
    python3 tools/style-check.py --browser --screenshots DIR

The web-app stylesheet is the source. `both/frontend/styles.css` is an
exact copy, which both of that template's front doors `@import`; the
`mcp-ui` stylesheet shares its body from `:root {` on, with `.ui` rules
added.
`--browser` renders the class page with Playwright at 320, 375 and 1280 px
in light and dark, and fails on horizontal page overflow or a cut-off
short label (the template look steps' rule). It needs Playwright; run it
through the plugin's uv:

    bin/uv run --no-project --with playwright python tools/style-check.py --browser
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "skills/build/templates"
WEB = T / "web-app/web/src/styles.css"
SHARED = T / "both/frontend/styles.css"
MCP = T / "mcp-ui/frontend/mcp/styles.css"
# The `both` front doors import the shared sheet rather than copy it.
IMPORTS = {
    T / "both/frontend/web/src/styles.css": '@import "../../styles.css";',
    T / "both/frontend/mcp/styles.css": '@import "../styles.css";',
}
PAGE = ROOT / "tools/style-check.html"

# The MCP-only lines, added after the web body's `main > *` rule.
MCP_ONLY = (".ui {", ".ui > *")
UI_RULES = (
    ".ui { --topbar-h: 0px; "
    '--font-display: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; '
    '--font-text: ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; '
    "--font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; "
    "font-family: var(--font-text); "
    "padding: var(--space-4); display: grid; "
    "gap: var(--space-3); align-content: start; }  "
    "/* an MCP UI's root, inside the host's frame; system fonts, since a host may block web fonts */\n"
    ".ui > * { min-width: 0; }\n"
)

# Same selector as the template's "sees no clipped labels" step.
LABELS = (
    ".stat .label, .stat .value, .group-band, th, .pill, .tab, "
    "button, .page-head h1, .field > label"
)
CLIPPED = """(selector) => [...document.querySelectorAll(selector)]
    .filter(e => {
        const text = e.innerText.trim();
        return text.length > 0 && text.length < 24 &&
            e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1;
    })
    .map(e => e.innerText.trim())"""


def body(text: str) -> str:
    return text[text.index(":root {"):]


def mcp_from(web: str, mcp: str) -> str:
    """The MCP stylesheet for `web`: its own header, the web body, `.ui`."""
    header = mcp[: mcp.index(":root {")]
    web_body = body(web)
    anchor = web_body.index("main > * { min-width: 0; }")
    cut = web_body.index("\n", anchor) + 1
    return header + web_body[:cut] + UI_RULES + web_body[cut:]


def check_copies(write: bool) -> list[str]:
    problems = []
    web = WEB.read_text()
    if write:
        SHARED.write_text(web)
        MCP.write_text(mcp_from(web, MCP.read_text()))
    if SHARED.read_text() != web:
        problems.append(
            f"{SHARED.relative_to(ROOT)} differs from {WEB.relative_to(ROOT)} "
            "(run with --write)"
        )
    lines = [
        line for line in body(MCP.read_text()).splitlines()
        if not line.startswith(MCP_ONLY)
    ]
    if lines != body(web).splitlines():
        problems.append(
            f"{MCP.relative_to(ROOT)}: body differs from the web stylesheet "
            "(run with --write)"
        )
    for path, line in IMPORTS.items():
        if line not in path.read_text():
            problems.append(f"{path.relative_to(ROOT)}: missing `{line}`")
    return problems


def check_browser(screenshots: Path | None) -> list[str]:
    from playwright.sync_api import sync_playwright

    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(PAGE, Path(tmp) / "index.html")
        shutil.copy(WEB, Path(tmp) / "styles.css")
        url = (Path(tmp) / "index.html").as_uri()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for width, height in ((320, 700), (375, 812), (1280, 900)):
                for theme in ("light", "dark"):
                    page.set_viewport_size({"width": width, "height": height})
                    page.goto(f"{url}?theme={theme}&drawer=")
                    where = f"{width}px {theme}"
                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth - window.innerWidth"
                    )
                    if overflow > 1:
                        problems.append(f"{where}: page is {overflow}px wider than the screen")
                    clipped = page.evaluate(CLIPPED, LABELS)
                    if clipped:
                        problems.append(f"{where}: labels cut off: {clipped!r}")
                    if screenshots is not None:
                        screenshots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(
                            path=str(screenshots / f"{width}-{theme}.png"), full_page=True
                        )
            if screenshots is not None:
                page.set_viewport_size({"width": 1280, "height": 900})
                page.goto(f"{url}?drawer=1")
                page.screenshot(path=str(screenshots / "1280-drawer.png"))
            browser.close()
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write", action="store_true", help="rewrite the copies from the source")
    parser.add_argument("--browser", action="store_true", help="render the class page")
    parser.add_argument("--screenshots", type=Path, help="save PNGs here (with --browser)")
    args = parser.parse_args()

    problems = check_copies(args.write)
    if args.browser:
        problems += check_browser(args.screenshots)
    for problem in problems:
        print(f"style-check: {problem}", file=sys.stderr)
    if not problems:
        checked = "copies agree" + ("; class page fits and clips nothing" if args.browser else "")
        print(f"style-check: {checked}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

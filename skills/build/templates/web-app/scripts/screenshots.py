"""Screenshot every route of the running web app, for the design review
(`web-app/references/ui-design.md`, principle 12).

    uv run --with playwright python scripts/screenshots.py / /settings
    uv run --with playwright python scripts/screenshots.py --user Ben /

Signs in through the Development picker (`rbt dev`), then saves each
route at desktop (1440x900) and phone (375x812) width, light and dark,
full page, to `screenshots/`. Open every image and look at it. The first
run needs a browser: `uv run --with playwright playwright install
chromium`."""

import argparse
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

# Where `rbt dev run` serves this app's frontend.
DEFAULT_BASE = "http://localhost:5273"

SIZES = {"desktop": (1440, 900), "phone": (375, 812)}
THEMES = ("light", "dark")


def slug(route: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", route.lower()).strip("-") or "home"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("routes", nargs="*", default=["/"])
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--user", default="Alice", help="a Development picker identity")
    parser.add_argument("--out", type=Path, default=Path("screenshots"))
    args = parser.parse_args()
    base = args.base.rstrip("/")
    args.out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # Sign in once and reuse the session for every shot.
        context = browser.new_context()
        page = context.new_page()
        page.goto(base + "/")
        page.wait_for_load_state("networkidle")  # the session probe answers first
        sign_in = page.get_by_role("button", name="Sign in")
        if sign_in.count() > 0:
            sign_in.first.click()
            page.get_by_role("link", name=args.user).click()
            # Back on the app, signed in: its "Sign in" button is gone.
            page.get_by_role("button", name="Sign in").first.wait_for(
                state="detached", timeout=15_000
            )
        state = context.storage_state()
        context.close()

        for name, (width, height) in SIZES.items():
            for theme in THEMES:
                context = browser.new_context(
                    storage_state=state,
                    viewport={"width": width, "height": height},
                    color_scheme=theme,
                )
                # The choice ThemeToggle saves (`web/src/theme.tsx`).
                context.add_init_script(f"localStorage.setItem('theme', '{theme}')")
                page = context.new_page()
                for route in args.routes:
                    page.goto(base + route)
                    page.wait_for_load_state("networkidle")
                    page.wait_for_timeout(500)  # let skeletons resolve
                    path = args.out / f"{slug(route)}-{name}-{theme}.png"
                    page.screenshot(path=str(path), full_page=True)
                    print(path)
                context.close()
        browser.close()


if __name__ == "__main__":
    main()

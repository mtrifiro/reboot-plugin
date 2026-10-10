"""Look checks: steps a browser scenario uses to fail a page that breaks
the visual standard (`web-app/references/ui-design.md`, "Never"), e.g.

    Then "alice" sees the web app fit a phone screen
    And "alice" sees no loading text in the web app
    And "alice" sees the web app use its own fonts
    And "alice" sees the web app work in light and dark
    And "alice" sees no clipped labels in the web app

They are a floor; the screenshot review (build Step 5) judges the design.

They drive the browser the web app steps open, so they need Playwright
(`python/references/testing-web-app.md`, "Install"); without it this
module defines nothing and the backend scenarios run as before."""

import re

# The last run's results, for the pull request and the release record
# (last_run.py).
from last_run import (  # noqa: F401
    pytest_sessionstart,
    pytest_terminal_summary,
    pytest_unconfigure,
)

# How far a run is, for the Reboot band (run_progress.py).
from run_progress import (  # noqa: F401
    pytest_collection_finish,
    pytest_runtest_logreport,
    pytest_runtest_logstart,
    pytest_sessionfinish,
)

try:
    from reboot.bdd import parsers, then
    from reboot.bdd.web import WebApp
    HAVE_BROWSER = True
except ImportError:  # Playwright not installed: no browser scenarios.
    HAVE_BROWSER = False

if HAVE_BROWSER:
    # Font names a page may lead with without loading anything: generic
    # families and the system stack. Any other name must be a face the
    # page actually loaded.
    SYSTEM_FONTS = {
        "ui-sans-serif", "ui-serif", "ui-monospace", "system-ui",
        "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto",
        "helvetica neue", "helvetica", "arial", "sans-serif", "monospace",
        "sfmono-regular", "menlo", "consolas",
    }
    # The browser's default text: what an unstyled page renders in.
    DEFAULT_SERIF = {"serif", "times", "times new roman"}

    # Elements whose short text is a label, never meant to truncate: a
    # cut-off one ("P0" shown as "PO") fails. Titles may truncate.
    LABELS = (
        ".stat .label, .stat .value, .group-band, th, .pill, .tab, "
        "button, .page-head h1, .field > label"
    )

    @then(parsers.parse('"{user}" sees the web app fit a phone screen'))
    def _fits_a_phone_screen(web_app: WebApp, user: str) -> None:
        page = web_app.page(user=user)
        size = page.viewport_size
        page.set_viewport_size({"width": 375, "height": 812})
        try:
            page.wait_for_timeout(300)  # let the layout settle
            overflow = page.evaluate(
                "document.documentElement.scrollWidth - window.innerWidth"
            )
            assert overflow <= 1, (
                f"the page is {overflow}px wider than a 375px phone screen; "
                "look for a row that doesn't wrap or scroll inside itself"
            )
        finally:
            if size is not None:
                page.set_viewport_size(size)

    @then(parsers.parse('"{user}" sees no loading text in the web app'))
    def _no_loading_text(web_app: WebApp, user: str) -> None:
        text = web_app.page(user=user).inner_text("body")
        found = re.search(r"\bloading\s*(\.\.\.|…)", text, re.IGNORECASE)
        assert found is None, (
            f"the page shows {found.group(0)!r}; use a skeleton instead"
            if found else ""
        )

    @then(parsers.parse('"{user}" sees the web app use its own fonts'))
    def _own_fonts(web_app: WebApp, user: str) -> None:
        page = web_app.page(user=user)
        page.evaluate("document.fonts.ready.then(() => true)")
        family = page.evaluate("getComputedStyle(document.body).fontFamily")
        first = family.split(",")[0].strip().strip("'\"").lower()
        assert first not in DEFAULT_SERIF, (
            f"the page's text font is {family!r}, the browser default; "
            "set a font stack in styles.css"
        )
        if first in SYSTEM_FONTS:
            return  # a deliberate system stack
        # `document.fonts.check()` is true for a name with no face at all,
        # so look for a loaded face of that family instead.
        loaded = page.evaluate(
            """(name) => [...document.fonts].some(f =>
                f.status === "loaded" &&
                f.family.replace(/["']/g, "").toLowerCase() === name)""",
            first,
        )
        assert loaded, (
            f"the page names {first!r} first but never loaded it; add its "
            "@font-face or link, or lead with a system stack"
        )

    @then(parsers.parse('"{user}" sees the web app work in light and dark'))
    def _light_and_dark(web_app: WebApp, user: str) -> None:
        page = web_app.page(user=user)
        # The template's ThemeToggle (`web/src/theme.tsx`).
        toggle = page.locator('button[aria-label^="Switch to"]')
        assert toggle.count() == 1, (
            "no light/dark toggle (a button named \"Switch to … mode\")"
        )
        background = (
            "getComputedStyle(document.body).backgroundColor === "
            "'rgba(0, 0, 0, 0)' ? getComputedStyle(document.documentElement)"
            ".backgroundColor : getComputedStyle(document.body).backgroundColor"
        )
        before = page.evaluate(background)
        toggle.click()
        page.wait_for_timeout(200)
        after = page.evaluate(background)
        theme = page.evaluate("document.documentElement.dataset.theme")
        toggle.click()  # leave the page as it was
        assert theme in ("light", "dark"), "the toggle didn't set data-theme"
        assert after != before, (
            "switching the theme didn't change the page's background"
        )

    @then(parsers.parse('"{user}" sees no clipped labels in the web app'))
    def _no_clipped_labels(web_app: WebApp, user: str) -> None:
        clipped = web_app.page(user=user).evaluate(
            """(selector) => [...document.querySelectorAll(selector)]
                .filter(e => {
                    const text = e.innerText.trim();
                    return text.length > 0 && text.length < 24 &&
                        e.clientWidth > 0 && e.scrollWidth > e.clientWidth + 1;
                })
                .map(e => e.innerText.trim())""",
            LABELS,
        )
        assert not clipped, (
            f"labels cut off or overlapping: {clipped!r}; give them room "
            "or move them out of the bar"
        )

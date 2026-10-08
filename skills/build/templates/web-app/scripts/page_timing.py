"""Time every route's load against Google's Core Web Vitals "good"
thresholds (build skill, Step 5).

    uv run --with playwright python scripts/page_timing.py / /settings

For each route: content, from the navigation to the first frame with no
`.skeleton` or `[aria-busy="true"]` left (the data on screen, held to
LCP's 2.5 s, since a skeleton can be the page's largest paint); LCP
itself; and CLS, how far the layout jumps as the data arrives. Signs in
through the Development picker (`rbt dev`), loads each route cold (a
fresh browser cache) and warm (reloads), and prints the worst of each.
Exits 1 when any is over. Time the production build (the build skill,
Step 5, says how), not Vite's dev server. The first run needs a browser:
`uv run --with playwright playwright install chromium`."""

import argparse
import sys

from playwright.sync_api import Page, sync_playwright

# Where `vite preview` serves the timing build (the build skill, Step 5),
# not Vite's dev server, which compiles each module on request.
DEFAULT_BASE = "http://localhost:4273"

# Google's "good" thresholds (web.dev/articles/vitals).
LCP_MS = 2500
CLS = 0.1

# Records, on the page, when its content first shows (the first frame
# after the document parses with no skeleton or busy region left), its
# largest contentful paint and its cumulative layout shift.
OBSERVE = """
(() => {
  window.__lcp = 0;
  window.__cls = 0;
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) window.__lcp = e.startTime;
  }).observe({ type: "largest-contentful-paint", buffered: true });
  new PerformanceObserver(list => {
    for (const e of list.getEntries()) if (!e.hadRecentInput) window.__cls += e.value;
  }).observe({ type: "layout-shift", buffered: true });
  const busy = () =>
    document.querySelector('.skeleton, [aria-busy="true"]') !== null ||
    !document.body || document.body.innerText.trim() === "";
  const check = () => {
    if (window.__contentAt !== undefined) return;
    if (document.readyState !== "loading" && !busy()) {
      window.__contentAt = performance.now();
      return;
    }
    requestAnimationFrame(check);
  };
  requestAnimationFrame(check);
})();
"""


def load(page: Page, url: str) -> tuple[float, float, float]:
    """One load of `url`: content and LCP in milliseconds, and CLS."""
    page.goto(url)
    page.wait_for_function("window.__contentAt !== undefined", timeout=30_000)
    page.wait_for_timeout(500)  # late shifts and paints still count
    content, lcp, cls = page.evaluate("[window.__contentAt, window.__lcp, window.__cls]")
    return float(content), float(lcp), float(cls)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("routes", nargs="*", default=["/"])
    parser.add_argument("--base", default=DEFAULT_BASE)
    parser.add_argument("--user", default="Alice", help="a Development picker identity")
    parser.add_argument("--runs", type=int, default=5, help="warm loads per route")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # Sign in once and reuse the session for every load.
        context = browser.new_context()
        page = context.new_page()
        page.goto(base + "/")
        page.wait_for_load_state("networkidle")  # the session probe answers first
        sign_in = page.get_by_role("button", name="Sign in")
        if sign_in.count() > 0:
            sign_in.first.click()
            page.get_by_role("link", name=args.user).click()
            page.get_by_role("button", name="Sign in").first.wait_for(
                state="detached", timeout=15_000
            )
        state = context.storage_state()
        context.close()

        missed = []
        print(f"{'route':<24} {'content':>9} {'LCP':>7} {'CLS':>6}")
        print(f"{'(good)':<24} {'≤ 2.5 s':>9} {'≤ 2.5 s':>7} {'≤ 0.1':>6}")
        for route in args.routes:
            url = base + route
            # Cold: a fresh context, so nothing is cached; then reloads.
            context = browser.new_context(storage_state=state)
            context.add_init_script(OBSERVE)
            page = context.new_page()
            loads = [load(page, url) for _ in range(1 + args.runs)]
            context.close()
            content = max(c for c, _, _ in loads)
            lcp = max(l for _, l, _ in loads)
            cls = max(s for _, _, s in loads)
            over = [
                name
                for name, value, limit in (("content", content, LCP_MS), ("LCP", lcp, LCP_MS), ("CLS", cls, CLS))
                if value > limit
            ]
            mark = f"  ✗ {', '.join(over)}" if over else ""
            print(f"{route:<24} {content / 1000:8.2f}s {lcp / 1000:6.2f}s {cls:6.3f}{mark}")
            if over:
                missed.append(route)
        browser.close()

    if missed:
        print(f"\nOver a threshold: {', '.join(missed)}")
        return 1
    print("\nEvery route within the thresholds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

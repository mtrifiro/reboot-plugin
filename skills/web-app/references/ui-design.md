---
title: Design the UI
impact: HIGH
impactDescription: Without it the SPA ships unstyled controls, no visual hierarchy, or a view that doesn't fit its task
tags: web-app, ui, design, css, dark-mode, skeleton, layout, review
summary: "Brief, the house default look (a user's brand replaces it), primary view by task, page anatomy, labeled controls, light/dark toggle, restyle by token values, screenshot review."
step: frontend
applies: [mcp-ui, web-app]
always: false
verified: 1.6.0
docs: ""
---

# Design the UI

## When you are here

Designing or writing the SPA's pages. The goal is a UI a person can
scan and operate: a clear hierarchy, legible rows, and the right view
for the task. Precedence: the user's words, then an existing design
system (their brand site, a tokens file), then this file, then the
template's defaults, which are Reboot's brand ("The default look"
below). A user who names a brand, a site or a look gets that instead. Wiring and
accessible markup: [`react-client.md`](react-client.md).

## Do this

**01 Brief.** Five lines in the design: who uses it and on what screen;
the task; the one question the primary view answers; the accent and its
source; the type choice. Look for a brand before settling the look: the
user's words, a tokens file, the product's site, then the brand of the
organization the app serves. With none, keep the house default and say
so; never name a source nobody gave. For example:

```
Who: support leads, on a laptop, between calls
Task: triage incoming bug reports by severity and status
Question: what needs someone today?
Accent: violet #5b3fd6 on paper — house default, no brand supplied
        (or: teal #0f8a8a — from the team's logo)
Type: house default — Bricolage Grotesque, Instrument Sans, JetBrains Mono (or the brand's)
```

**Read a brand from its site, don't guess.** Open it in the browser and
read computed styles: the body's background and color; the font family
and weight of `h1`, `h2`, body text, buttons and `code`; and the most
frequent colors on the page. A brand usually gives more than an accent:
a page color, an ink, a highlight, and up to three typefaces (display,
text, mono). Record each in the brief, with the site as the source. A
product the user names ("model Resy") is a source the same way: open
it, read, show the table, then apply, never from memory; on a running
app, [`ui-restyle.md`](ui-restyle.md).

### The default look: the house default

The template's `styles.css` ships it: the skills' own look, no one's
brand. Its `:root` and dark blocks name every token: paper page,
near-black ink, a violet accent with a deep shade for the top bar and
a pale tint for selection, `--good`/`--warn`/`--bad`. Type is Bricolage
Grotesque 500 for headings and big numbers, Instrument Sans for text,
JetBrains Mono for code and ids, bundled from `@fontsource` in
`main.tsx`, no CDN; headings weight 500, slightly tight, never bold.
The tint is the accent's own pale shade, never a second hue. Keep the
look when the user names no brand; replace it whole when they do. MCP
UIs keep the colors and use the system fonts
(`mcp-ui/references/ui-design.md`).

**02 Primary view by task.**

| Task | Primary view | Template classes |
| --- | --- | --- |
| Triage, lookup, review of many items | Grouped list or table with filters | `filter-panel`, `list-card`, `group-band`, `row` (`row-grid` for many columns), `dot`; `table-wrap` |
| A few items moving through stages | Board | `board`, `board-col`, `card` |
| Amounts over time | Chart | `chart` (an `<svg>`, `--series-1..4`) |
| Events over time | Timeline | `feed` |
| Places, dates | A floor plan, a map, a calendar | none; build on the tokens. A spatial hero takes the width, lists beside it `density-compact`; geometry from data (footprints in the seed, non-overlap checked in code); status per 05, with a legend; solid strokes, no glow or gradient, legible across a room; a seed geometry change needs the expunge cycle (restaurant-app-2, 1.6.0) |

One record's detail is a `kv` list in a `drawer` (`drawer-body` scrolls,
`drawer-foot` holds the main action) or on its own route.
Confirm a destructive action with a `confirm-bar` in place; report a
finished one with a `notice`.

A well-designed list is a full primary view; don't add a chart to make
it look visual. Add a second view over the same reader when it answers
a question the first can't.

**03 Anatomy.** `topbar` (product name, account, theme toggle) →
`page-head` in a `brand-band` (a headline saying what the page is for, a
`lede` on what to do here, the main action or view switch on its right)
→ summary, its tiles overlapping the band's edge → controls → content.
Data never starts above the title block. With two or more pages, the
template's `SiteNav` (`web/src/nav.tsx`) goes after the product name:
the links sit beside it, then on a second line of their own, then that
line tighter, then behind a ☰ menu left of the name, each step taken
only when the last would cut a link off. Anything placed below the bar
uses `--topbar-h`, which `useBarHeight` keeps at the bar's real height.

A page that scrolls past about two screens, with three or more
sections, wraps them in the template's `WithContents`
(`web/src/contents.tsx`): a sidebar of the page's own `h2` and `h3`
headings, the one being read marked, sticky under the bar from 640 px
up and folded into a Contents panel below.

**04 Summary first, simplest form.** Counts: `stats` tiles (label, big
number, optional `meter`); a tile that filters is a `button.stat`, marked
`selected` when active. Proportions: a bar only when every segment
holds its label; otherwise a `tally` (a dot, count and label each) or
tiles.

**05 Brand from its colors; saturation on one dimension.** The accent
marks primary actions, selection and a highlighted tile; its deep shade
(`--accent-deep`) carries one structural band, the top bar and page
head; the page, tint and glow (`--bg`, `--accent-tint`, `--bg-glow`)
carry surfaces. A brand replaces the whole family: accent, deep, tint,
page, ink, muted and line, in light and both dark blocks. A brand of one
color can derive the rest with `color-mix()` from `--accent`. The
accent may differ by scheme (the violet needs a lighter lilac on a dark
page); it keeps its role, and stays off green, amber and red in
both. A brand's green becomes `--accent-tint`, never an accent. Keep
contrast high: body text 7:1 or better, secondary text 4.5:1,
panels set apart from a tinted page. Saturated color (`--good`, `--warn`,
`--bad`) encodes exactly one data dimension (severity, health), as a
`dot` or `pill`; every other status is a neutral `pill` with text. Don't
use green, amber or red as the accent.

**06 Controls on one surface, labeled.** A `filter-panel`: search full
width; filters in a grid with a small label above each; view, group
and sort together; keyboard hints behind a "?", not in the toolbar.

**07 Readable by default.** Rows of about 44–56 px; the main text wraps
and is never cut off while secondary columns have room (mark them
`secondary`, hidden first as the width shrinks); `density-compact` as
an option; numbers labeled ("also seen ×2"); identifiers ("A.14b")
shown as written, never uppercased.

**08 Detail doesn't reflow the list.** A `drawer` over the list or its
own route; a side panel leaves the list its title column.

**09 Containment by role.** Border, fill and shadow mark a separate
object (the filter panel, the list, a tile), not every block. One type
scale of about five sizes, one radius, one shadow.

**10 Live data.** Skeletons shaped like the content; an empty state
with the next action; a running workflow as a pill on its object.

**11 Light and dark, with a toggle.** Design both schemes. The first
build keeps `ThemeToggle` (`web/src/theme.tsx`) in the top bar:
remembered per browser, the OS setting until chosen. The user may ask
to remove it later.

**12 Review the screenshots.** With the app running,
`uv run --with playwright python scripts/screenshots.py / /other-route`
signs in through the dev login and saves every route at desktop
(1440×900) and phone (375×812, full page) width, light and dark, to
`screenshots/`. Open every image. Compute the contrast of every text
and background pair in both schemes with a short script, not by eye.
After a hand toggle wait about 300 ms: cards fade over 160 ms and a
mid-fade capture looks like a contrast bug. Check 03–09 and Never, fix
in one pass, then pin a look scenario per page (`testing-web-app.md`,
"Look steps"). A plan's exact numbers are starting points; when a
screenshot shows one hurts legibility, deviate and say so at handoff.

**Build on the template's `styles.css`.** Change token values to the
brief's, keep the names, use its classes (the table in 02, plus
`topbar`, `brand-band`, `page-head`, `stats`, `tally`) and extend the
file.

**13 Restyle by changing values, not adding layers.** Asked to restyle
a running app, edit the token values in place in `:root` and both dark
blocks; never append a block that redefines them, since a later block
silently beats the edit. The steps, the layers to fold first and the
depth to offer are in [`ui-restyle.md`](ui-restyle.md).

## Never

- Browser default styling: an unstyled `<button>`, `<select>` or
  `<input>`, or the default serif.
- "Loading…" or a bare spinner; use `skeleton`.
- An empty list without a next action; use `empty`.
- `alert()`, `confirm()`, `prompt()`: they block the scenarios too.
- Raw hex in components; use a token.
- A page broken at phone width (16 px gutters, wide tables in
  `table-wrap`, tabs scrolling in their own row) or in either color
  scheme.
- Form fields in a `1fr 1fr` grid: a date or number input won't shrink
  and overflows its card. Use `field-row` and `field`.
- A first build without the light/dark toggle, or a palette with only
  one scheme.
- A placeholder as a control's only label, or labels removed to
  restyle (use `visually-hidden`).
- Saturated color on two data dimensions at once.
- A summary label that is cut off or overlaps.
- Keeping a plan's number after the screenshots show it hurts.
- A brand source nobody gave, or the house default kept while the
  user named another brand. With no brand, the brief says "house
  default, no brand supplied".
- A restyle that appends an override layer instead of changing the
  token values.
- A logo or favicon with a hard-coded color; use `var(--accent)` and
  `var(--on-accent)` (the favicon: the accent's current hex).
- A green, amber or red accent in either scheme, including a brand's
  green highlight promoted to the dark accent.
- Font-specific `font-feature-settings` left after the font changes.
- Truncating the main text of a row or card.
- Page links in a row that scrolls with its scrollbar hidden: past the
  edge they are gone with no sign. Wrap, then a menu (`SiteNav`).
- A layout chosen from a measurement that the layout itself changes.
  The bar's `min-height` read from the `--topbar-h` it writes only grew;
  a "tight" style that reached the measured copy flipped the nav
  between two layouts at one width. Measure what no layout touches, and
  check by sweeping the window width both ways, 4 px at a time, then
  holding still at each switch point: the layout changes once per
  point and never while still.
- Uppercase on identifiers or data (`text-transform` turns "A.14b" into
  "A.14B").

## Limits

Principles, not pixels: an existing design system or the user's own
direction overrides any of them, the house default included.

## Scales as

Not measured.

## Errors you will see

None known.

## See also

- [`react-client.md`](react-client.md) — wiring and accessible markup
- [`build/templates/README.md`](../../build/templates/README.md) — template files and classes
- [`testing-web-app.md`](../../python/references/testing-web-app.md) — look steps

---
title: Changing the Look of a Running App
impact: MEDIUM
impactDescription: Four palettes in nine minutes, each a guess from a taste word, applied as an appended layer while the backend restarted; the user rejected every one and asked what was going on
tags: restyle, look, palette, brand, tokens, candidates, screenshots, iteration
summary: "One change per turn, no restart, a screenshot opened; after two rejections, rendered candidates or a site read."
step: frontend
applies: [web-app, mcp-ui]
always: false
when: "the user asks to change the look of an app that already runs"
verified: 1.6.0
docs: ""
---

# Changing the Look of a Running App

## When you are here

The app runs and the user wants it to look different: "I hate the
colors", "make it friendlier", "model X". The mechanics of a restyle
(token values in place, folded layers, favicon, logo, fonts) are
[`ui-design.md`](ui-design.md) principle 13; reading a brand or a named
product from its site is principle 01. This file is the loop around
them, so each turn shows the user one change they can judge.

## Do this

1. **Find the source before the edit.** A brand, a tokens file, or a
   product the user names ("Resy", "linear.app's colors") is read from
   its site and shown as a table (page, ink, highlight, fonts, each with
   its source) before anything changes. A taste word ("cleaner",
   "friendly", "cool") is not a source; it narrows the next step, it does
   not pick colors.
2. **One change per turn.** Edit the token values in `:root` and both
   dark blocks (principle 13), nothing else in that turn. No backend
   restart, expunge or reseed in the same turn: a page captured mid-boot
   comes back signed out or half-loaded, and the user cannot tell the
   look from the outage.
3. **Look before they do.** Run `scripts/screenshots.py` for the page
   in question, open the image, and check it against principles 03 to
   09. Then tell the user what changed and where to look, in one or two
   lines ("the accent is now the logo's teal; the page is warmer; look at
   the list and the drawer").
4. **After a second rejection with no source, stop guessing.** Offer two
   or three rendered candidates: the plugin's class page
   (`tools/style-check.html`) or the app's own page, each in one token
   set, screenshotted side by side; or ask for a site to read. Candidates
   are token sets, never layers appended to `styles.css`. Fold the chosen
   one into `:root`, delete the rest, and run the screenshots again.
5. **Plan, then do, for a whole brand.** Asked to restyle to a brand,
   show the source table against the app's current values and offer the
   depth (colors and type, or the whole visual language) before editing;
   restaurant-app-2's Reboot restyle was accepted on the first try that
   way, after four guesses had failed in the morning.

## Never

- A new palette from a taste word alone, or a named product's colors
  from memory (restaurant-app-2, 1.6.0: four guesses, four rejections).
- A look change in the same turn as a backend restart, expunge or
  reseed.
- A screenshot taken without opening it, or a change reported without
  saying where to look.
- Candidates kept as stacked blocks in `styles.css`; a later block beats
  the tokens and its raw hex outlives the look (principle 13).

## Limits

- `scripts/screenshots.py` signs in through the Development picker and
  waits for the live readers; a page behind a production provider needs
  a signed-in session of its own.
- The class page shows the template's anatomy in a token set, not the
  app's own pages; for a page the template does not cover, screenshot
  the app.

## Scales as

- Not measured.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| A screenshot shows the sign-in picker or loading skeletons | The backend was restarting, or the readers had not delivered | No restart in a look turn; `screenshots.py` waits for skeletons, so rerun it once the app is up |

## See also

- [`ui-design.md`](ui-design.md) — principles 01 (a source), 12 (the screenshot review), 13 (restyle mechanics)
- [`../../build/templates/README.md`](../../build/templates/README.md) — `scripts/screenshots.py`

---
title: The UI Is the Product
impact: HIGH
impactDescription: Without it the SPA ships default fonts, unstyled controls and a table per page
tags: web-app, ui, design, css, dark-mode, skeleton
summary: "Unless asked for plain: brief, hero view beyond tables, template `styles.css`, skeletons, empty states with next actions."
step: frontend
applies: [web-app]
always: false
verified: 1.6.0
docs: ""
---

# The UI Is the Product

## When you are here

Designing or writing the SPA's pages. Every app is highly visual
unless the user asks otherwise: information-dense, branded, the data's
shape on screen; "it works" is the floor. Wiring and accessible markup:
[`react-client.md`](react-client.md).

## Do this

**The visual brief**, in the design: who uses it and on what screen
(density follows); the hero view; the palette and its source (the
user's brand site, else the domain), light and dark; a display, text
and mono face from Google Fonts; how live data shows.

**Build on the template's `web/src/styles.css`** (tokens, light and
dark, base elements, standard classes listed at its top). Change token
values to the brief's, keep the names, extend the file. Keep
`ThemeToggle` (`web/src/theme.tsx`) in the top bar: every app offers
light and dark, remembered per browser, the OS setting until chosen.

**One hero view**, the landing screen, showing the data's shape: a
board by stage (pipelines, tickets), a labeled scatter (two scores), a
timeline (history), a map, a calendar, a chart (amounts over time). The
table is a second tab over the same reader.

**Live data:** skeletons sized like the real rows until the reader
answers; an empty state with the next action; a running workflow as a
pill on its object, with its start time.

## Never

- Browser default fonts; an unstyled `<button>`, `<select>` or `<input>`.
- A table as the only view of the domain.
- "Loading…" or a bare spinner; use `skeleton`.
- An empty list without a next action; use `empty`.
- `alert()`, `confirm()`, `prompt()`: they block the scenarios too.
- Raw hex in components; use a token.
- A page broken at phone width (16 px gutters, wide tables in
  `table-wrap`, tabs scrolling in their own row) or in either color
  scheme.
- Form fields in a `1fr 1fr` grid: a date or number input won't shrink
  and overflows its card. Use `field-row` and `field`.
- An app without the light/dark toggle, or a palette with only one
  scheme.
- Removing labels to restyle; use `visually-hidden`.

## Limits

None known.

## Scales as

Not measured.

## Errors you will see

None known.

## See also

- [`react-client.md`](react-client.md) — wiring and accessible markup
- [`build/templates/README.md`](../../build/templates/README.md) — template files

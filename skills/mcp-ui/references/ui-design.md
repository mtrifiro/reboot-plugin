---
title: The Look of an MCP UI
impact: HIGH
impactDescription: Without it an MCP UI ships unstyled, ignores the host's light or dark theme, and shows "loading..."
tags: mcp-ui, ui, design, css, dark-mode, host-theme, skeleton
summary: "The web app's principles inside a host: shared `frontend/mcp/styles.css`, `useHostTheme()` (the host owns light/dark), one focused view, skeletons."
step: frontend
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# The Look of an MCP UI

## When you are here

Writing a `UI()` bundle under `frontend/mcp/<name>/`. It renders inside
the host's frame (Claude, ChatGPT, …), next to the conversation. Follow
the principles in `web-app/references/ui-design.md` (04, 05, 07 and 09
apply inside a host); this file covers what differs in a host's frame.
Wiring:
[`react-app-tsx.md`](react-app-tsx.md).

## Do this

**One stylesheet for both front doors.** Each UI's `index.css` imports
`frontend/mcp/styles.css`: the web app's tokens and classes (`stats`,
`list-card`, `row`, `pill`, `skeleton`, `field-row`, …), in Reboot's
brand by default (`web-app/references/ui-design.md`, "The default
look"), with system fonts: the `.ui` rule sets `--font-*` back to the
system stack. A user's brand replaces the token values (accent, page and
ink family, light and dark), so the UI and the web app look like one
product; the deep band is the web app's alone. In the `both` template
the two front doors import one shared `frontend/styles.css`, so there is
one place to change. A restyle of the web app is a restyle of the MCP
UIs too: change the values there, never append an override layer.

**The host owns light and dark.** Call `useHostTheme()` once in the UI's
top component; it applies the host's theme now and on every change, by
setting `data-theme` on `<html>`. No toggle in an MCP UI.

```tsx
import { useHostTheme } from "../host-theme";

export const BoardApp: FC = () => {
  useHostTheme();
  const { board } = useBoard();
  if (board === undefined) return <Skeleton />;
  return <BoardView board={board} />;
};
```

**One focused view per UI**: the result of what the AI just did, as a
short list, one record, or a summary. Root it in `<main
className="ui">`; let it fill the frame's width and grow in height.

**Widget anatomy:** a title line with the count and what it shows; the
content, at most about 20 rows, each a single line at frame width; then
one row of actions, ending with "Open in web app" when there is more.
Lists and editing beyond that belong in the web app.

**Live data:** a skeleton shaped like the view until the reader answers,
never a "loading..." string; an empty state that says what to ask the
AI next.

## Never

- Web fonts in an MCP UI, the Reboot default's included: a host may
  block loading them in its frame; keep the `.ui` rule's system stack.
- A light/dark toggle, or a theme that ignores the host's.
- "loading..." or a bare spinner; use `skeleton`.
- A whole app in one UI (tabs of tables): one view per `UI()`.
- Raw hex in components; use a token.

## Limits

- `useHostTheme()` needs the MCP host connection: outside a host (a
  plain browser tab) `useMcpApp()` is `null` and the page follows the
  OS setting (`prefers-color-scheme`).

## Scales as

Not measured.

## Errors you will see

None known.

## See also

- [`react-app-tsx.md`](react-app-tsx.md) — the UI's component and hooks
- [`../../web-app/references/ui-design.md`](../../web-app/references/ui-design.md) — the brief and design principles

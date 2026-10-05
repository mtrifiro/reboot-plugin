---
title: Pop-out button — deep-linking an MCP UI widget to your web app
impact: MEDIUM
impactDescription: An MCP UI widget runs in a sandboxed iframe that blocks `window.open`, so a naive "open in browser" button silently does nothing in most hosts. Use the bound entity's `state_id` to build a deep link and ask the host to open it via the MCP Apps `openLink` request, with a `window.open` fallback.
tags: react, app-tsx, pop-out, deep-link, openLink, state_id, useMcpApp, dual-frontend, web-app
summary: "The iframe blocks `window.open`: deep-link from `state_id` via `useMcpApp().openLink({ url })`, with fallback; `rbt_session` keeps sign-in."
step: frontend
applies: [mcp-ui]
always: false
when: "a widget needs a \"pop out into the web app\" button"
verified: 1.6.0
docs: ""
---

# Pop-out button — deep-linking an MCP UI widget to your web app

## When you are here

The backend also serves a standalone web app (`web-app` skill) and a
widget needs a "pop out into the web app" button opening the **same
entity** in a browser tab. Building the web app and sharing one `User`
via `oauth=...` are not covered here.

## Do this

```tsx
import { useMcpApp } from "@reboot-dev/reboot-react";
import { useCounter } from "@api/<pkg>/v1/<name>_rbt_react";

export const ClickerApp = () => {
  // Both hooks before any early return.
  const { counter } = useCounter(); // from the tool-call target; `undefined` until then
  const mcpApp = useMcpApp(); // `null` outside a host and on early renders

  if (counter === undefined) {
    return null;
  }

  // The resolved entity ID, though no `{ id }` was passed.
  const counterId = counter.state_id;

  const handlePopOut = async () => {
    // The web app reads this param on load and renders that entity.
    const url =
      "https://your-web-app.example/?counter=" + encodeURIComponent(counterId);

    // `window.open` is blocked in the sandboxed iframe: ask the host first,
    // fall back when not under a host or the host declines.
    if (mcpApp?.openLink) {
      try {
        const { isError } = await mcpApp.openLink({ url });
        if (!isError) {
          return;
        }
      } catch {
        // Fall through to `window.open`.
      }
    }
    window.open(url, "_blank", "noopener");
  };

  return <button onClick={handlePopOut}>Open in web app ↗</button>;
};
```

- The handle exposes the resolved entity ID as `state_id`; the host opens
  external URLs for the widget via the MCP Apps `openLink` request.
- The web app renders `?counter=<id>` as a single-counter view via
  `useCounter({ id })`.
- Both frontends share the `oauth=...` session (the `rbt_session`
  cookie), so a user signed in through the MCP host is signed in when the
  tab opens.

## Never

- `window.open(url)` alone — the iframe is sandboxed without
  `allow-popups`, so it silently no-ops in most hosts. Try `openLink`
  first.
- `mcpApp.openLink(...)` without `?.` — `useMcpApp()` is `null` outside a
  host and on early renders.
- Calling `useMcpApp()` after the `counter === undefined` early return —
  hooks must run on every render.
- A hardcoded `localhost` origin in a deployed app — take the web app's
  origin from config.

## Limits

- `useMcpApp()` (re-exported from `@reboot-dev/reboot-react`) returns the
  `@modelcontextprotocol/ext-apps` `App`; `openLink({ url })` resolves to
  `{ isError }` — the host may deny a blocked domain or the user cancel.
- The entity's authorizer still applies in the web app: the signed-in
  user must be allowed to read the deep-linked entity.

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`react-app-tsx.md`](react-app-tsx.md) — how the hook resolves the entity
- [`react-generated-client.md`](../../python/references/react-generated-client.md) — the handle's `state_id`

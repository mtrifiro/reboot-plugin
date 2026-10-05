---
title: Pop-out button — deep-linking an MCP UI widget to your web app
impact: MEDIUM
impactDescription: An MCP UI widget runs in a sandboxed iframe that blocks `window.open`, so a naive "open in browser" button silently does nothing in most hosts. Use the bound entity's `state_id` to build a deep link and ask the host to open it via the MCP Apps `openLink` request, with a `window.open` fallback.
tags: react, app-tsx, pop-out, deep-link, openLink, state_id, useMcpApp, dual-frontend, web-app
summary: "The sandboxed iframe blocks `window.open`: build a deep link from the handle's `state_id`, open it with `useMcpApp().openLink({ url })`, fall back to `window.open`; `rbt_session` keeps sign-in."
step: frontend
applies: [mcp-ui]
always: false
when: "a widget needs a \"pop out into the web app\" button"
verified: 1.6.0
docs: ""
---

# Pop-out button — deep-linking an MCP UI widget to your web app

## When you are here

The same backend also serves a standalone web app (the `web-app` skill),
and an MCP UI widget needs a "pop out into the web app" button that
opens the **same entity** in a full browser tab. Building the web app
itself, and sharing one `User` across both frontends via `oauth=...`, is
not covered here.

## Do this

```tsx
import { useMcpApp } from "@reboot-dev/reboot-react";
import { useCounter } from "@api/<pkg>/v1/<name>_rbt_react";

export const ClickerApp = () => {
  // Resolved from the MCP tool-call target; `undefined` until then.
  const { counter } = useCounter();

  // The MCP host handle; `null` when not under a host, and on early
  // renders while the host connection is set up.
  const mcpApp = useMcpApp();

  if (counter === undefined) {
    return null;
  }

  // The resolved entity ID, even though no `{ id }` was passed.
  const counterId = counter.state_id;

  const handlePopOut = async () => {
    // The web app reads this query param on load to render that one
    // entity.
    const url =
      "https://your-web-app.example/?counter=" + encodeURIComponent(counterId);

    // Ask the host to open the link; `window.open` is blocked in the
    // sandboxed iframe. Fall back to `window.open` when not under an
    // MCP host (or the host declines the request).
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

Two facts make this work: the generated handle exposes the resolved
entity ID as `state_id`, so a widget that auto-resolved its entity still
recovers the concrete ID; and the host opens external URLs on the
widget's behalf through the MCP Apps `openLink` request.

The web app reads the query param on load and shows just that entity —
`?counter=<id>` selects a single-counter view via `useCounter({ id })`.
Both frontends share the `oauth=...`-driven session (the `rbt_session`
cookie), so a user signed in through the MCP host is already signed in
when the tab opens.

## Never

- `window.open(url)` alone — the widget's iframe is sandboxed without
  `allow-popups`, so it silently no-ops in most hosts. Go through
  `openLink` first.
- `mcpApp.openLink(...)` without `?.` — `useMcpApp()` is `null` outside
  a host and on early renders.
- Calling `useMcpApp()` after the `counter === undefined` early return —
  hooks must run on every render; call both hooks first.
- A hardcoded `localhost` origin in a deployed app — source the web
  app's origin from config rather than assuming a port.

## Limits

- `useMcpApp()` is re-exported from `@reboot-dev/reboot-react`; its value
  is the `@modelcontextprotocol/ext-apps` `App`, whose `openLink({ url })`
  resolves to `{ isError }` — the host may deny a blocked domain, or the
  user may cancel.
- The entity's authorizer still applies in the web app: the deep-linked
  entity must be one the signed-in user may read.

## Scales as

- Not measured.

## Errors you will see

None known.

## See also

- [`react-app-tsx.md`](react-app-tsx.md) — how the hook resolves the entity
- [`react-generated-client.md`](../../python/references/react-generated-client.md) — the handle's `state_id`

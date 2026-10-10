---
title: Wire the Web SPA to the Reboot Backend
impact: HIGH
impactDescription: The browser shell, the backend URL, the generated hooks, and how a typed backend error reaches the user
tags: web-app, react, vite, hooks, errors, RebootClientProvider, template, allowed-origins
summary: "An unset `VITE_REBOOT_URL` points at Vite's origin; copy `build/templates/web-app/web/`; own port, `strictPort`, sign-in, typed errors."
step: frontend
applies: [web-app]
always: false
verified: 1.6.0
docs: ""
---

# Wire the Web SPA to the Reboot Backend

## When you are here

Building the standalone browser frontend at `web/`: Vite shell, provider
and backend URL, sign-in, components calling the generated hooks. **Do
not read the `mcp-ui` scaffolding references**: their Vite config,
nested `frontend/mcp/<name>/index.html` output and `UI()` machinery are
MCP-host-specific. The hook surface is
[`react-generated-client.md`](../../python/references/react-generated-client.md).

## Do this

### The `web/` shell — copy it

`web/` arrives with the template (`copy.sh web-app ...`; see
[`build/templates/README.md`](../../build/templates/README.md)); do not
run `npm create vite@latest`. Then `cd web && npm install`, `rbt generate`
again, and `npm run build` to check the bundle. Every file is explained
in the templates README; two are load-bearing:

- **`vite.config.ts`** — `resolve.dedupe: ["react", "react-dom", "zod"]`
  (two copies break hooks and schema identity at runtime);
  `server.host: true` (Vite's `localhost` binds IPv6 `[::1]` only, so a
  forwarded IPv4 port is refused with no dev-server error — the most
  common "starts fine, won't open").
- **`src/App.tsx`** — the sign-in gate and one signed-in component;
  replace its body.

### The backend URL — set it explicitly in dev

`<RebootClientProvider>` with no `url` falls back to `window.REBOOT_URL`,
then `?rebootUrl=`, then `window.location.origin` — the **wrong** origin
in dev, where the SPA is on Vite's port and the backend on the port
`.rbtrc` names. The template reads `web/.env.development`
(`VITE_REBOOT_URL=http://localhost:<port>`, written by the scaffold with
the same port as `.rbtrc`; a second copy of the app changes both):

```tsx
const REBOOT_URL =
  (import.meta.env.VITE_REBOOT_URL as string | undefined) ??
  window.location.origin; // keeps a backend-served build working
// <RebootClientProvider url={REBOOT_URL}>
```

### The generated client

Hooks, mutators and error classes from `rbt generate --react=` — the
`useFoo` overloads, `UseFooApi`, the three-field reader return,
`ResponseOrAborted`, `<Type><Method>Aborted`, snake→camel naming, why a
hook id must be real on every render — are in
[`react-generated-client.md`](../../python/references/react-generated-client.md).
Do **not** open `web/src/api/**/*_rbt_react.ts` to rediscover them.
Client state on top of the hooks:
[`patterns-react-state.md`](../../python/references/patterns-react-state.md).

### Sign-in and sign-out

`useSignIn()` / `useSignOut()` from `@reboot-dev/reboot-react` drive the
built-in OAuth server at `/__/oauth/*`. The session is the HttpOnly
`rbt_session` cookie (no token to store). The no-argument `useUser()`
(present because the API declares a `User` type) returns
`{ user, isLoading }`: `user === undefined` when signed out, `isLoading`
while the `/__/oauth/whoami` probe runs. The template's `App.tsx` gates
on `user`, then mounts `SignedIn({ user }: { user: UseUserApi })` so
every hook below has a real id.

### Surfacing a typed error

`aborted.error` is a union of the method's declared errors and the
framework's (`PermissionDenied`, `Unknown`, …), tagged by `error.type`
(the Python class name), with the pydantic error model's fields
camelCased. Translate in one place; the backend already refused, the
frontend only reports:

```ts
// web/src/errors.ts
export function friendlyError(aborted: {
  error: { type: string } & Record<string, unknown>;
  message: string;
}): string {
  switch (aborted.error.type) {
    case "QuotaExceededError":
      return `Limit reached (${String(aborted.error.limit)}).`;
    case "PermissionDenied":
      return "You don't have access to do that.";
    default:
      return aborted.message || `Something went wrong.`;
  }
}
```

### Accessible markup, so scenarios can drive the page

Scenarios ([`testing-web-app.md`](../../python/references/testing-web-app.md))
find elements as a person or screen reader does, never by selector. Build
every page this way from the start:

```tsx
<label htmlFor="amount">Amount ($)</label>          {/* field by label */}
<input id="amount" type="number" value={amount} onChange={...} />
<button onClick={open}>Open Account</button>        {/* button by text */}
<button aria-label="Delete" onClick={remove}><TrashIcon /></button>
<h2 id="your-accounts">Your Accounts</h2>           {/* table by heading */}
<table aria-labelledby="your-accounts">...</table>
<td data-testid="account-id">{account.id}</td>      {/* a backend-made value */}
```

- A `<select>` gets a paired label too, its `<option>`s saying the value
  a scenario picks; a placeholder is not a label.
- A table or list a scenario names has a labeled heading as above, or a
  `<caption>`.
- `data-testid` only on an element whose text is exactly a value a
  scenario reads back.
- Nameable roles: `button`, `link`, `tab`, `checkbox`, `radio`,
  `menuitem`, `option`, `row`, `table` — use the native element
  (`<button>`, `<a href>`, `<input type="checkbox">`), never a
  `<div onClick>`.
- Render values that change on backend events as text so
  `eventually sees` can wait.

## Never

- `npm create vite@latest` for `web/`: it emits React 19 / TypeScript 6
  tsconfigs (`erasableSyntaxOnly`) the TypeScript 5 set rejects. Copy
  the template.
- `process.env.PORT` in `vite.config.ts` without `@types/node`: `tsc -b`
  fails. The template uses a literal port.
- Leaving the port at Vite's default 5173 or dropping `strictPort`:
  another project's server on `[::1]:5173` silently answers `localhost` while this
  one answers `127.0.0.1`, and without `strictPort` Vite slides to the
  next port, leaving `.env` and `allowed_origins` wrong.
- Deploying with `allowed_origins=[]`: a standalone SPA is cross-origin
  from its backend by construction. `rbt dev run` allows `http://localhost(:*)` itself,
  hiding this in development. Set the production origin in `main.py`'s
  `OAuth(allowed_origins=[...])` when choosing the provider (`deploy`
  skill).
- The subscription traps (`#` in an id, an actor that may not exist,
  a seventh live read): `react-generated-client.md` § Never and Limits.

## Limits

- `useUser()` exists only when the API has a `User` type;
  `@reboot-dev/reboot-react` 1.6.0 exports no other session hook.
  Without a `User` type, read a domain reader at the top of the tree and
  treat `aborted.error.type === "Unauthenticated"` as signed out
  (reboot-bluesky, 1.4.1).

## Scales as

- The template's production bundle is about 384 kB of JS (115 kB gzip)
  at 1.6.0, almost all React, `zod` and the Reboot client.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Could not detect Reboot server URL. Ensure the page is served from the Reboot server.` | No `url` and no fallback resolved | Pass `url={REBOOT_URL}` from `VITE_REBOOT_URL` |
| `Property 'env' does not exist on type 'ImportMeta'` | `src/vite-env.d.ts` missing | Copy it from the template |
| `error TS2688: Cannot find type definition file for 'node'.` | `"types": ["node"]` without `@types/node` | Copy the template's `package.json` |
| `Cannot find name 'process'` | `process.env` in `vite.config.ts` without `@types/node` | Same |
| `` `Application(oauth=...)` is running without `OAuth(allowed_origins=[...])` `` | `allowed_origins` left out: works under `rbt dev run`, production refuses to start | Pass a list (the template passes `[]`); list the SPA origin before deploying |
| `/__/oauth/whoami` CORS error in the browser console on every load | The client probes it whether or not the app has `oauth=`; nothing breaks. On 1.4.0 the response lacked `access-control-allow-credentials` and the client retried forever | Ignore it; on 1.4.0 serve same-origin through a Vite proxy |

## See also

- [`react-generated-client.md`](../../python/references/react-generated-client.md) — hooks, mutators, typed errors
- [`testing-web-app.md`](../../python/references/testing-web-app.md) — scenarios that drive this page
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained

---
title: Wire the Web SPA to the Reboot Backend
impact: HIGH
impactDescription: The browser shell, the backend URL, the generated hooks, and how a typed backend error reaches the user
tags: web-app, react, vite, hooks, errors, RebootClientProvider, template, allowed-origins
summary: "Copy `build/templates/web-app/web/`; set `VITE_REBOOT_URL` in dev (the default resolves to Vite's origin); `server.host`, own port, `strictPort`; sign-in/out, accessible markup, typed errors."
step: frontend
applies: [web-app]
always: false
verified: 1.6.0
docs: ""
---

# Wire the Web SPA to the Reboot Backend

## When you are here

You are building the standalone browser frontend at `web/`: its Vite
shell, the provider and backend URL, sign-in, and the components that
call the generated hooks. This is the web-app counterpart of the
`mcp-ui` scaffolding references — **do not read those**: their Vite
config, nested `frontend/mcp/<name>/index.html` output and `UI()`
machinery are MCP-host-specific. The hook surface itself is
[`react-generated-client.md`](../../python/references/react-generated-client.md).

## Do this

### The `web/` shell — copy it

`web/` arrives with the template (`copy.sh web-app ...`, see
[`build/templates/README.md`](../../build/templates/README.md)). Do
not run `npm create vite@latest`. Then `cd web && npm install`, run
`rbt generate` again, and `npm run build` to check the bundle. Why the
files look the way they do:

- **`package.json`** — `@reboot-dev/reboot-api` and
  `@reboot-dev/reboot-react` pinned to the backend's `reboot`
  version; React 18, `zod` 4; dev dependencies `@types/node`,
  `@types/react(-dom)`, `@vitejs/plugin-react`, `typescript` 5.9,
  `vite` 6. `@bufbuild/protobuf` is a peer dependency of
  `reboot-react` that npm installs on its own.
- **`vite.config.ts`** — stock plus three load-bearing additions:
  `resolve.dedupe: ["react", "react-dom", "zod"]` (two copies break
  hooks and schema identity at runtime); `server.host: true` (Vite's
  `localhost` binds IPv6 `[::1]` only, so a forwarded port over IPv4
  gets connection refused while the dev server logs no error — the
  most common "starts fine, won't open"); and a project port (`5273`)
  with `strictPort: true`. Change the port if another project on the
  machine uses it.
- **`tsconfig.app.json` / `tsconfig.node.json`** — React 18 /
  TypeScript 5 settings; the node half has `"types": ["node"]` for
  `vite.config.ts`. The app half includes `src/`, generated client
  and all; that type-checks cleanly at 1.6.0.
- **`.env.development`** and **`src/main.tsx`** — the backend URL,
  below. **`src/vite-env.d.ts`** types `import.meta.env`.
- **`src/App.tsx`** — the sign-in gate and one signed-in component;
  replace its body with the app.

### The backend URL — set it explicitly in dev

`<RebootClientProvider>` with no `url` falls back to
`window.REBOOT_URL`, then a `?rebootUrl=` query parameter, then
`window.location.origin`. In development the SPA is on Vite's port and
the backend on `:9991`, so the fallback is the **wrong** origin. The
template passes it from `web/.env.development`
(`VITE_REBOOT_URL=http://localhost:9991`):

```tsx
const REBOOT_URL =
  (import.meta.env.VITE_REBOOT_URL as string | undefined) ??
  window.location.origin;
// <RebootClientProvider url={REBOOT_URL}>
```

The `?? window.location.origin` keeps a build the backend serves from
its own origin working.

### The generated client

Hooks, mutators and error classes from `rbt generate --react=` are in
[`react-generated-client.md`](../../python/references/react-generated-client.md):
the `useFoo` overloads, `UseFooApi`, the three-field reader return,
`ResponseOrAborted`, `<Type><Method>Aborted`, snake→camel naming, and
why a hook id must be real on every render. Do **not** open
`web/src/api/**/*_rbt_react.ts` to rediscover them. Where client state
lives on top of the hooks is
[`patterns-react-state.md`](../../python/references/patterns-react-state.md).

### Sign-in and sign-out

`useSignIn()` / `useSignOut()` from `@reboot-dev/reboot-react` drive
the built-in OAuth server at `/__/oauth/*`. The session lives in the
HttpOnly `rbt_session` cookie (no token to store), and the no-argument
`useUser()` reports it: `{ user, isLoading }`, `user === undefined`
when signed out, `isLoading` while the `/__/oauth/whoami` probe runs.
The template's `App.tsx` is the whole shape: gate on `user`, then
mount a `SignedIn({ user }: { user: UseUserApi })` child so every hook
below it has a real id. `useUser` exists because the API declares a
`User` type.

### Surfacing a typed error

`aborted.error` is a union of the method's declared errors and the
framework's (`PermissionDenied`, `Unknown`, …), tagged by
`error.type`, the Python class name. Its fields are the pydantic
error model's, camelCased. One translator keeps the switch in one
place:

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

The frontend only reports; the backend already refused.

### Accessible markup, so scenarios can drive the page

Web app scenarios
([`testing-web-app.md`](../../python/references/testing-web-app.md))
find elements as a person or screen reader does, never by selector.
Build every page this way from the start:

```tsx
<label htmlFor="amount">Amount ($)</label>          {/* field by label */}
<input id="amount" type="number" value={amount} onChange={...} />
<button onClick={open}>Open Account</button>        {/* button by text */}
<button aria-label="Delete" onClick={remove}><TrashIcon /></button>
<h2 id="your-accounts">Your Accounts</h2>           {/* table by heading */}
<table aria-labelledby="your-accounts">...</table>
<td data-testid="account-id">{account.id}</td>      {/* a backend-made value */}
```

A `<select>` gets a paired label too; a placeholder is not a label.
`data-testid` belongs only on an element whose text is exactly a
value a scenario reads back. Roles a scenario may name: `button`,
`link`, `tab`, `checkbox`, `radio`, `menuitem`, `option`, `row`,
`table` — use the native element (`<button>`, `<a href>`,
`<input type="checkbox">`), never a `<div onClick>`. Render values that
change on backend events as text so `eventually sees` can wait.

## Never

- `npm create vite@latest` for `web/`: it emits React 19 /
  TypeScript 6 tsconfigs (`erasableSyntaxOnly`) that the TypeScript 5
  set here rejects. Copy the template.
- `process.env.PORT` in `vite.config.ts` without `@types/node`:
  `tsc -b` fails. The template uses a literal port.
- Leaving the port at Vite's default 5173 or dropping `strictPort`:
  another project's server on `[::1]:5173` silently answers
  `localhost` while this one answers `127.0.0.1`, and without
  `strictPort` Vite slides to the next port, leaving `.env` and
  `allowed_origins` wrong.
- Deploying with `allowed_origins=[]`: a standalone SPA is
  cross-origin from its backend by construction. `rbt dev run` allows
  `http://localhost(:*)` on its own, so it is invisible in
  development. Set the production origin in `main.py`'s
  `OAuth(allowed_origins=[...])` when choosing the provider (`deploy`
  skill).
- `#` in an actor id a page subscribes to: the id rides a WebSocket
  URL and `#` truncates it (`Failed to construct 'WebSocket'`); `@`,
  `:`, `~` are safe (observed at 1.4.x).
- Subscribing to an actor that may not exist: the reader aborts
  `StateNotConstructed` and retries about once a second, disturbing
  every other subscription on the page. Mount the subscribing
  component after the actor is constructed (observed at 1.4.x).

## Limits

- Reactive readers hold streaming connections; HTTP/1.1 allows about
  six per host, and Reboot logs a warning naming the fix (HTTP/2 via
  TLS). Keep subscriptions per page few (observed at 1.4.x).
- `useUser()` exists only when the API has a `User` type;
  `@reboot-dev/reboot-react` 1.6.0 exports no other session hook.

## Scales as

- The template's production bundle is about 384 kB of JS (115 kB
  gzip) at 1.6.0, almost all React, `zod` and the Reboot client.

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Could not detect Reboot server URL. Ensure the page is served from the Reboot server.` | No `url` and no fallback resolved | Pass `url={REBOOT_URL}` from `VITE_REBOOT_URL` |
| `Property 'env' does not exist on type 'ImportMeta'` | `src/vite-env.d.ts` missing | Copy it from the template |
| `error TS2688: Cannot find type definition file for 'node'.` | `"types": ["node"]` without `@types/node` | Copy the template's `package.json` |
| `Cannot find name 'process'` | `process.env` in `vite.config.ts` without `@types/node` | Same |
| `` `Application(oauth=...)` is running without `OAuth(allowed_origins=[...])` `` | `allowed_origins` left out: works under `rbt dev run`, production refuses to start | Pass a list (the template passes `[]`); list the SPA origin before deploying |

## See also

- [`react-generated-client.md`](../../python/references/react-generated-client.md) — hooks, mutators, typed errors
- [`testing-web-app.md`](../../python/references/testing-web-app.md) — scenarios that drive this page
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained

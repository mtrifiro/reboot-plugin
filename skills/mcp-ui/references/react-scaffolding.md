---
title: React Scaffolding — package.json, vite.config.ts, tsconfigs, index.css
impact: CRITICAL
impactDescription: The shell files for the `frontend/` tree. `vite.config.ts` is load-bearing — flattening the HTML output breaks MCP UI artifact discovery (the server resolves `frontend/dist/mcp/<name>/index.html`, the **nested** Vite default). `npm run build` runs `build.mjs`, which auto-discovers and builds every UI; tsconfigs split into `app` and `node` halves.
tags: web, react, vite, tsconfig, package-json, css, build, hmr, scaffolding, build-mjs, template
summary: "Copy `build/templates/mcp-ui/frontend/`; `vite.config.ts` exactly: flattening output breaks UI discovery at `frontend/dist/mcp/<name>/index.html`. `npm install` before the second `rbt generate`."
step: frontend
applies: [mcp-ui]
always: false
verified: 1.6.0
docs: ""
---

# React Scaffolding — package.json, vite.config.ts, tsconfigs, index.css

## When you are here

Creating or extending an MCP UI's `frontend/` tree: `package.json`, Vite
and TypeScript config, `build.mjs`, and per-UI entry files under
`frontend/mcp/<ui-name>/`. The component: [`react-app-tsx.md`](react-app-tsx.md);
project-root files: [`project-shell.md`](project-shell.md). A standalone
web app does not use this tree (`web-app` skill).

## Do this

`frontend/` arrives with the template
(`<plugin>/skills/build/templates/copy.sh mcp-ui ...`; see
[`build/templates/README.md`](../../build/templates/README.md)). Then:

```sh
rbt generate                  # writes frontend/api/
cd frontend && npm install
cd .. && rbt generate         # again, now that node_modules exists
cd frontend && npm run build  # tsc -b, then build.mjs
```

- **`frontend/vite.config.ts` — copy exactly, never edit.** One config,
  three jobs: the `serve` dev server (HMR for every `mcp/<name>` UI and
  the `web/` SPA under `base: "/__/frontend/"`, port `RBT_VITE_PORT` or
  `4444`, `strictPort`, `host: true`), and two builds chosen by
  `RBT_BUILD_TARGET`: `mcp:<name>` roots at `mcp/<name>/` so
  `index.html` lands at the **nested** `dist/mcp/<name>/index.html` the
  MCP server resolves, JS and CSS inlined by `viteSingleFile`; `web`
  builds the SPA into `dist/web/` with `base: "/__/frontend/web/"`. Also
  sets the `@api` alias and `dedupe: ["react", "react-dom", "zod"]`.
- **`frontend/build.mjs`** — `npm run build` runs `tsc -b && node
  build.mjs`, which discovers every `mcp/<name>/index.html` (and
  `web/index.html`) and builds each through `vite.config.ts`. Adding or
  removing a UI touches no script.
- **`frontend/package.json`** — the set `@reboot-dev/create-ui@1.6.0`
  writes: `@reboot-dev/reboot-react` and `@reboot-dev/reboot-api` at the
  backend's `reboot` version, the two `@modelcontextprotocol` packages,
  React 18, `zod` 4, dev dependencies including `@types/node` and
  `vite-plugin-singlefile`. Rename only `name`.
- **`frontend/tsconfig.json` / `tsconfig.app.json` /
  `tsconfig.node.json`** — the app half type-checks `mcp`, `web` and
  `vite-env.d.ts` with the `@api/*` path; the node half `vite.config.ts`.
  **`frontend/vite-env.d.ts`** (Vite client types) types `*.module.css`
  imports and `import.meta.env`.
- **`frontend/mcp/clicker/`** — one UI: `index.html`, `main.tsx`
  (`RebootClientProvider` with no `url`; the backend serves the UI),
  `App.tsx`, `App.module.css`, `index.css` (theme variables, with a
  `[data-theme="light"]` override).

### Adding a UI

Each `UI(path="frontend/mcp/<name>")` needs `frontend/mcp/<name>/` with
the same five files: copy `frontend/mcp/clicker/`, change `<title>` and
the component, `npm run build`. Or `npm create @reboot-dev/ui`, which
writes only missing files for every `UI()` method lacking an
`index.html`.

## Never

- Rewrite `vite.config.ts` to emit a flat `dist/<name>.html`: the MCP
  server only finds `frontend/dist/mcp/<name>/index.html`. A missing
  artifact means the build did not run, not that the config is wrong.
- Hand-maintain per-UI `build:<name>` scripts; `build.mjs` discovers UIs.
- Run the second `rbt generate` before `npm install`: the documented
  order is generate, install, generate. (At 1.6.0 the two runs differed
  only in import formatting in the smoke test.)
- Copy a `tsconfig*.json` from `npm create vite@latest`: it now targets
  React 19 / TypeScript 6 (`erasableSyntaxOnly`), not the React 18 /
  TypeScript 5 set pinned here.

## Limits

- The dev server port is fixed by `.rbtrc`'s
  `dev run:hmr --frontend-host=http://localhost:4444`; change both
  together (or set `RBT_VITE_PORT`).
- Every UI must live under `frontend/mcp/<name>/` to share the dev
  server; `create-ui` skips a `UI(path=...)` outside it.

## Scales as

- Each MCP UI builds to one self-contained HTML file: the sample clicker
  is about 455 kB (131 kB gzip) at 1.6.0, almost all React, `zod` and the
  Reboot client (template smoke test).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Web artifact 'frontend/dist/mcp/<name>/index.html' is missing` | The UI was never built | `cd frontend && npm run build` — do not edit `vite.config.ts` |
| `Unknown build target:` | `vite build` ran without `RBT_BUILD_TARGET`, or for a UI with no `index.html` | Run `npm run build` (it sets the target) |
| `Property 'useGet' does not exist on type '{ counter: UseCounterApi \| undefined; isLoading: boolean; }'` | Zero-arg `use<Type>()` returns `{ <type>, isLoading }` at 1.6.0, not the handle | Destructure it and mount a child once the handle is defined (template `App.tsx`) |

## See also

- [`react-app-tsx.md`](react-app-tsx.md) — writing the component
- [`project-shell.md`](project-shell.md) — `.rbtrc` HMR and dist configs
- [`build/templates/README.md`](../../build/templates/README.md) — every template file explained

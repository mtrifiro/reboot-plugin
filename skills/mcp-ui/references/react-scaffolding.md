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

You are creating or extending the `frontend/` tree of an MCP UI: its
`package.json`, Vite and TypeScript config, `build.mjs`, and the
per-UI entry files under `frontend/mcp/<ui-name>/`. Writing the
component itself is [`react-app-tsx.md`](react-app-tsx.md); the
project-root files are [`project-shell.md`](project-shell.md). A
standalone web app does not use this tree (`web-app` skill).

## Do this

The `frontend/` tree arrives with the template
(`<plugin>/skills/build/templates/copy.sh mcp-ui ...`, see
[`build/templates/README.md`](../../build/templates/README.md)). Then:

```sh
rbt generate                  # writes frontend/api/
cd frontend && npm install
cd .. && rbt generate         # again, now that node_modules exists
cd frontend && npm run build  # tsc -b, then build.mjs
```

What the files are, and what you change:

- **`frontend/vite.config.ts` — copy exactly, never edit.** One config
  does three jobs: the `serve` dev server (HMR for every `mcp/<name>`
  UI and the `web/` SPA under `base: "/__/frontend/"`, port
  `RBT_VITE_PORT` or `4444`, `strictPort`, `host: true`), and two
  builds selected by `RBT_BUILD_TARGET`: `mcp:<name>` roots the build
  at `mcp/<name>/` so its `index.html` lands at the **nested**
  `dist/mcp/<name>/index.html` the MCP server resolves, with JS and
  CSS inlined by `viteSingleFile`; `web` builds the SPA into
  `dist/web/` with `base: "/__/frontend/web/"`. It also sets the `@api`
  alias and `dedupe: ["react", "react-dom", "zod"]`.
- **`frontend/build.mjs`** — `npm run build` runs `tsc -b && node
  build.mjs`; the script discovers every `mcp/<name>/index.html` (and
  `web/index.html`) and builds each through `vite.config.ts`. Adding or
  removing a UI touches no script.
- **`frontend/package.json`** — the dependency set
  `@reboot-dev/create-ui@1.6.0` writes: `@reboot-dev/reboot-react` and
  `@reboot-dev/reboot-api` at the backend's `reboot` version, the two
  `@modelcontextprotocol` packages, React 18, `zod` 4, and dev
  dependencies including `@types/node` and `vite-plugin-singlefile`.
  Rename only `name`.
- **`frontend/tsconfig.json` / `tsconfig.app.json` /
  `tsconfig.node.json`** — the app half type-checks `mcp`, `web` and
  `vite-env.d.ts` with the `@api/*` path; the node half type-checks
  `vite.config.ts`. **`frontend/vite-env.d.ts`** (Vite client types)
  is what types `*.module.css` imports and `import.meta.env`.
- **`frontend/mcp/clicker/`** — one UI: `index.html`, `main.tsx`
  (`RebootClientProvider` with no `url`; the UI is served by the
  backend), `App.tsx`, `App.module.css`, `index.css` (theme
  variables, with a `[data-theme="light"]` override).

### Adding a UI

Each `UI(path="frontend/mcp/<name>")` in the API needs a directory
`frontend/mcp/<name>/` with the same five files. Copy
`frontend/mcp/clicker/` to the new name, change `<title>` and the
component, and run `npm run build`. `npm create @reboot-dev/ui`
does the same for every `UI()` method that has no `index.html` yet
(it writes only missing files).

## Never

- Rewrite `vite.config.ts` to emit a flat `dist/<name>.html`: the MCP
  server only finds `frontend/dist/mcp/<name>/index.html`. A missing
  artifact means the build did not run, not that the config is wrong.
- Hand-maintain per-UI `build:<name>` scripts; `build.mjs` discovers
  UIs.
- Run the second `rbt generate` before `npm install`: the documented
  order is generate, install, generate. (At 1.6.0 the two runs'
  output differed only in import formatting in the smoke test.)
- Copy a `tsconfig*.json` from `npm create vite@latest`: it now
  targets React 19 / TypeScript 6 (`erasableSyntaxOnly`), not the
  React 18 / TypeScript 5 set pinned here.

## Limits

- The dev server port is fixed by `.rbtrc`'s
  `dev run:hmr --frontend-host=http://localhost:4444`; change both
  together (or set `RBT_VITE_PORT`).
- Every UI must live under `frontend/mcp/<name>/` to share the one
  dev server; `create-ui` skips a `UI(path=...)` outside it.

## Scales as

- Each MCP UI builds to one self-contained HTML file: the sample
  clicker is about 455 kB (131 kB gzip) at 1.6.0, almost all of it
  React, `zod` and the Reboot client (measured in the template smoke
  test).

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

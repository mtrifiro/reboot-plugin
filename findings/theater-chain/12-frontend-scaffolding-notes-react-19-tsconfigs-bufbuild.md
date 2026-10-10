---
id: theater-chain-12
project: theater-chain
source: "theater-chain/reboot-findings.md §12"
reboot_version: 1.4.1
severity: unrated
target: plugin
names:
  - web-app/references/react-client.md
tags: [scaffold, version-drift, frontend]
cluster: "B"
still_applies: yes
status: Resolved
resolved_by: "build/templates/README.md § `web-app/` adds"
---

# Frontend scaffolding notes: React 19 tsconfigs, bufbuild, exclude

**What happened.** (1) `npm create vite@latest` now emits React 19 + TypeScript 6, whose `tsconfig.node.json` uses `erasableSyntaxOnly`, unknown to the TypeScript 5.x the Reboot React client is built against. Overwrite both `tsconfig.app.json` and `tsconfig.node.json` when pinning back to React 18. The skill's `package.json` pin is right but does not warn that the scaffold's tsconfigs come from the future; `@bufbuild/protobuf` is a peer dependency of `@reboot-dev/reboot-react` that npm does not install. (2) `exclude: ["src/api"]` in `tsconfig.app.json` keeps `strict` + `noUnusedLocals` from type-checking tens of thousands of generated lines on every build. (3) Generated TS types are real (`z.infer` of a Zod schema); model types import from `<name>_rbt_types`, not `_rbt_react`. (4) `useSignIn()` sends the browser to `/__/oauth/dev-login`, a fake account picker (Alice, Ben, Carlos, Dani, Esi) minting a stable `dev-{hash}` id; ideal for multi-patron contention testing with two browser profiles.

**Expected.** Add the two tsconfigs to `react-client.md` alongside the `package.json`, and add `@bufbuild/protobuf` to the dependency list.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md`.

**Checked at 1.6.0.** Still absent. Grep of `web-app/`, `mcp-ui/`, and `python/` for erasableSyntaxOnly / `exclude` of `src/api` / bufbuild found nothing, and `web-app/references/react-client.md` has no `package.json` or tsconfig content at all.

**Reopened 2026-10-08.** Partly covered: the web-app template fixes the React 19 / TS 6 tsconfig problem and its README notes the `@bufbuild/protobuf` peer. Still missing: the template's `tsconfig.app.json` does not exclude `src/api`.

**Resolution (2026-10-10).** The web template's tsconfigs are the React 18 / TypeScript 5 set and its README says npm installs the `@bufbuild/protobuf` peer; the `src/api` exclude is not applied because `tsc` type-checks imported files regardless of `exclude`, and `npm run typecheck` runs `tsc -b`.

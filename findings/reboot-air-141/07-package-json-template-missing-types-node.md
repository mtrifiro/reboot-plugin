---
id: reboot-air-141-07
project: reboot-air-141
source: "reboot-air/REBOOT_FINDINGS.md §7"
reboot_version: 1.4.1
severity: green
target: plugin
names:
  - web-app/references/react-client.md
  - web-app/SKILL.md
tags: [scaffold, frontend]
cluster: "B"
still_applies: yes
status: Resolved
resolved_by: "web-app/references/react-client.md § Do this"
---

# package.json template missing @types/node

**What happened.** The documented web `package.json` lists no `devDependencies`. A stock Vite React-TS `tsconfig.node.json` carries `"types": ["node"]` and the `vite.config.ts` the reference tells you to write reads `process.env.PORT`. Assembling `web/` from the reference verbatim and running `npm run build` fails with `error TS2688: Cannot find type definition file for 'node'.` Cost: one failed build and one guess, at the moment the skill says to sanity-check the bundle.

**Expected.** Show the full `package.json` including a `devDependencies` block (`@types/node`, `@types/react`, `@types/react-dom`, `@vitejs/plugin-react`, `typescript`, `vite`), since the reference commits to being the place the dependency set comes from.

**Repro.** Not recorded.

**Where in the skills.** `web-app/references/react-client.md` (the `web/` shell `package.json`) plus the `tsconfig.node.json` implied by the Project Layout.

**Checked at 1.6.0.** Still present, arguably worse. `web-app/SKILL.md:557` says `references/react-client.md` has "the `package.json` dependency set", but grep of `web-app/references/` for package.json / types/node / bufbuild finds nothing. A complete `package.json` with `@types/node` exists only in `mcp-ui/references/react-scaffolding.md:39`.

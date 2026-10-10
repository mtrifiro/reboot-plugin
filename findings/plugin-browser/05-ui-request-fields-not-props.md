---
id: plugin-browser-05
project: plugin-browser
source: "plugin-browser/FINDINGS.md § Plugin skills, item 3"
reboot_version: 1.6.0
severity: green
target: plugin
names:
  - mcp-ui/references/api-method-types.md
  - mcp-ui/references/react-app-tsx.md
tags: [scaffold, frontend]
cluster: ""
still_applies: unknown
status: Open
resolved_by: ""
---
# `UI(request=<Model>)` fields don't arrive as props in the template's wiring

**What happened.** `mcp-ui/references/api-method-types.md` says a UI's request fields "arrive as camelCased props", but the template's `main.tsx` renders the component with no props, and nothing else passes them. Reading them with `useMcpToolData()` from `@reboot-dev/reboot-react` ("the merged tool-input bag the MCP host delivered") works instead. Not verified inside a real host.

**Expected.** The reference to show where the props come from, or to point at `useMcpToolData()`.

**Repro.** `Catalog.show_findings=UI(request=FindingsView, …)` with the template's `main.tsx`.

**Where in the skills.** `mcp-ui/references/api-method-types.md` § "Where a `UI()` goes"; `mcp-ui/references/react-app-tsx.md`.

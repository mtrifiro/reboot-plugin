---
name: app
description: Build a Reboot application from a user description. Every backend is designed ready for both front doors — an MCP UI (ChatGPT, Claude, VSCode, Goose) and a standalone web app — with one `User` per identity via `oauth=...`. Builds the front door(s) the prompt names (MCP/Claude/ChatGPT → `mcp-ui`; a URL/SPA/"website" → `web-app`; both named → both); otherwise builds the web app first without asking and offers the MCP UI at handoff.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# app — Build a Reboot Application

Decide which **front door** to build first, then build it with the
[`build` skill](../build/SKILL.md) plus the matching front-door skill
(`mcp-ui`, `web-app`, or both). The backend is always ready for both.

## Routing

Every app gets a backend **ready for both front doors**: a `User` type,
`oauth=`, and each method's AI role and AI-facing `description=` in the
design (`build`, Design Phase). What varies is which front door is
built first.

### The two destinations

- **`mcp-ui`** — exposed through an MCP host (ChatGPT, Claude, VSCode,
  Goose, etc.) via MCP tools; any visual UI is embedded in the host as
  MCP UI artifacts.
- **`web-app`** — served at a URL and used in a normal browser: the
  Reboot backend behind a React frontend.

### Triggers (verbatim in the prompt)

**`mcp-ui`** if the prompt contains any of:

- `MCP`, `MCP host`, `MCP server`, `MCP app`, `MCP tool`, `mcp=Tool`,
  `UI()` (as a Reboot method type).
- `ChatGPT`, `Claude`, `VSCode`, `Goose`, `Cursor`, or
  "Anthropic / OpenAI" **named as the runtime** ("I want to use this
  from Claude", "expose it as a tool to ChatGPT"). Mentioning the
  company ("like ChatGPT") doesn't count.
- "MCP UI", "AI tool", "tool for an LLM/agent", "expose to an
  LLM/agent".

**`web-app`** if the prompt contains any of:

- A URL or scheme: `https://…`, `localhost:`, `example.com`.
- A route/page literal: `/login`, `/dashboard`, `/home`, `/admin`, etc.
- "website", "web app", "web site", "SPA", "single-page app", "in
  the browser", "served at <url>".

Domain words (CRM, todo, dashboard, chat room, …), "app", "UI",
"login" or "users" are not triggers: they say what the app does, not
where it is used.

### Decision flow

1. **Both front doors named** ("expose it to Claude **and** host it on
   the web", "MCP server plus a dashboard at crm.example.com") → say
   "Building this as a Reboot app with an MCP UI and a web app.", load
   [`build`](../build/SKILL.md), [`mcp-ui`](../mcp-ui/SKILL.md) _and_
   [`web-app`](../web-app/SKILL.md), and follow `build` taking both
   branches at each step. One backend `Application(oauth=...)` serves
   both with one `User` per upstream identity; signing in on one signs
   in on both.
2. **Only an MCP trigger** → say "Building this as a Reboot MCP UI;
   the backend will be ready for a web app too.", load `build` and
   `mcp-ui`, and follow `build` taking the `mcp-ui:` branches.
3. **Only a web-app trigger, or no trigger (default)** → say "Building
   this as a Reboot web app; the backend will be ready for an MCP UI
   too.", load `build` and `web-app`, and follow `build` taking the
   `web-app:` branches. Don't ask: the web app is the default first
   front door.
4. **"Only" / "just" / "no …"** ("just a website", "only an MCP tool",
   "no web UI") → build that one and skip the handoff offer for the
   other.

**At handoff** (build Step 7), unless step 4 applied, offer the other
front door in one line: "Want this in Claude and ChatGPT too? The
backend is ready; it adds an MCP UI beside the web app." (or the
reverse). On yes, follow `build`'s Update Flow, "Adding the other
front door".

### Worked examples

| Prompt fragment | Decision | Why |
| --- | --- | --- |
| "a CRM for my personal relationships, with notes and a timeline" | `web-app`, offer MCP | No trigger: the default. |
| "a todo list app" | `web-app`, offer MCP | "app" alone is not a trigger. |
| "a dashboard for our team's metrics, served at metrics.example.com" | `web-app`, offer MCP | Explicit URL. |
| "a tool I can use from Claude to track my reading list" | `mcp-ui`, offer web | "from Claude" names the runtime. |
| "just a simple website for signups" | `web-app`, no offer | "just" scopes it to one. |
| "expose a CRM as an MCP server, and also a dashboard at crm.example.com" | Both | Both named. |

## Note

On every route, `build` starts by agreeing each capability in plain
English and writing it as a `@wip` feature file before its API exists
([`feature` skill](../feature/SKILL.md)). Don't load `python/SKILL.md`
for an MCP UI or Web App: the front-door skills' reading lists name the
`python` references each step needs. A dual-frontend app reads both
lists, each reference once.

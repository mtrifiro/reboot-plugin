---
name: app
description: Build a Reboot application from a user description. Routes to the `mcp-ui` skill (MCP UIs for ChatGPT, Claude, VSCode, Goose), the web-app skill (standalone web apps with a browser frontend), or BOTH (dual-frontend apps sharing one backend and one User per identity via `oauth=...`). Commits to a route only when the prompt verbatim names the front-door (MCP/Claude/ChatGPT for MCP UI; a URL/SPA/"website" for web-app; explicit conjunction for both); otherwise asks the user. Does NOT infer the front-door from the app's domain (CRM, todo, dashboard, blog, …) — those describe what the app does, not where it lives.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# app — Build a Reboot Application

Decide the app's **front door**, then build it with the
[`build` skill](../build/SKILL.md) plus the matching front-door skill
(`mcp-ui`, `web-app`, or both).

## Routing

> **Default: ASK.** A wrong guess costs ~12 files of regeneration, so
> commit only when the description **names** the front-door verbatim.
> Never infer it from the app's _domain_ (CRM, blog, store, dashboard,
> todo, chat room, journal, …): domain words say what the app **does**,
> not **where** it's used — a "CRM" or "chat room" can be a website or
> an MCP tool exposed to Claude.

### The two destinations

- **`mcp-ui`** — exposed through an MCP host (ChatGPT, Claude, VSCode,
  Goose, etc.) via MCP tools; any visual UI is embedded in the host as
  MCP UI artifacts.
- **`web-app`** — served at a URL and used in a normal browser: the
  Reboot backend behind a React (or similar) frontend.

### Commit-without-asking triggers (must be VERBATIM in the prompt)

Commit immediately **only** on one of these phrases — no inference, no
synonyms, no "they probably mean…".

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
- A browser-auth phrase: "log in via email", "OAuth login", "cookie
  session", "sign up form".

**BOTH** (load mcp-ui + web-app) only on an explicit conjunction: "and
also a website", "MCP server **plus** a dashboard", "expose it to
Claude **and** host it on the web". Dual-frontend apps share one
backend, one `oauth=...`, and one `User` actor per upstream identity;
cross-frontend SSO is automatic.

### Do NOT infer commitment from any of these

If these are all the prompt offers, **ask**:

- The word "app" alone.
- Domain words: CRM, blog, store, dashboard, todo, todo list, journal,
  kanban, tracker, inventory, wiki, forum, chat room, counter, social
  network, planner, calendar, notes app, …
- "users", "auth", "login", "permissions" without "browser" /
  "website" / "URL" — both flavors have users.
- CRUD operations, fields, schemas, entity relationships, search,
  history, timelines, …
- "frontend" or "UI" without "browser" / "website" / "URL" — MCP UIs
  also have a UI (rendered in the host).
- A vibe of "this sounds like a SaaS / CRM / dashboard", "web-y" or
  "chat-y".

### Decision flow

1. **Verbatim MCP UI trigger** → say "Building this as a Reboot MCP
   UI.", load the [`build` skill](../build/SKILL.md) and the
   [`mcp-ui` skill](../mcp-ui/SKILL.md), and follow `build` from the
   top with the user's description, taking the `mcp-ui:` branches and
   `mcp-ui`'s reading lists.
2. **Verbatim web-app trigger** → say "Building this as a Reboot Web
   App.", load the [`build` skill](../build/SKILL.md) and the
   [`web-app` skill](../web-app/SKILL.md), and follow `build` from the
   top with the user's description, taking the `web-app:` branches and
   `web-app`'s reading lists.
3. **Both triggers, or explicit "I want both"** → say "Building this
   as a dual-frontend Reboot app — both MCP and standalone web.", load
   [`build`](../build/SKILL.md), [`mcp-ui`](../mcp-ui/SKILL.md) _and_
   [`web-app`](../web-app/SKILL.md), and follow `build` taking both
   branches at each step. One backend `Application(oauth=...)` serves
   both frontends with one shared `User` actor per upstream identity.
   Signing in on one frontend signs in on both: `/authorize`
   short-circuits when the browser already has the session cookie, and
   `/callback` sets it on every flow.
4. **Otherwise (default)** → **ask** this question, presenting the
   options and waiting for the answer (**mandatory**):

   ```
   Question: "Before I scaffold — which kind of app are you building?"
   Header:   "App type"
   Options:
     - "MCP UI" — exposed through an MCP host (ChatGPT, Claude,
       VSCode, Goose, …) via MCP tools; optional embedded UI.
     - "Web App"  — a standalone website / SPA users open in a
       normal browser.
     - "Both"     — a single app exposed through both an MCP host
       and a standalone browser SPA, sharing one `User` actor per
       upstream identity (cross-frontend SSO).
   ```

   Then route per steps 1–3; "Both" loads both front-door skills
   beside `build`, layered on the one backend `oauth=...`.

   > **Critical — non-skippable, including in "auto" / "autonomous" /
   > "don't ask" / skip-approvals / bypass-permissions modes.** This is
   > not a clarifying question but the skill's routing input; a
   > skill-level instruction beats a generic "make the reasonable call"
   > preference, and here the reasonable call _is_ to ask. Silence on
   > the topic is not delegation of the `mcp-ui` / `web-app` choice.
   > Do not skip it because the concept "feels obviously" web-y or
   > chat-y, because picking would be "faster" (the wrong pick is a
   > hard rollback), or because you have half-committed — stop and ask
   > before any file is written. Step 4 is skipped **only** when steps
   > 1–3 fired on a verbatim trigger in the user's prompt; if you are
   > drafting "I'll build this as a …" without a matched trigger or the
   > user's answer, **stop and ask**.

### Worked examples

| Prompt fragment                                                          | Decision                | Why                                                          |
| ------------------------------------------------------------------------ | ----------------------- | ------------------------------------------------------------ |
| "a CRM for my personal relationships, with notes and a timeline"         | **ASK**                 | CRM is a domain word, not a front-door. No verbatim trigger. |
| "a todo list app"                                                        | **ASK**                 | "app" alone is not a trigger.                                |
| "a dashboard for our team's metrics, served at metrics.example.com"      | `web-app`               | Explicit URL.                                                |
| "a tool I can use from Claude to track my reading list"                  | `mcp-ui`                | "from Claude" names the runtime; "tool" + LLM context.       |
| "a website where users can sign up and create journals"                  | `web-app`               | "website" is a verbatim trigger.                             |
| "a kanban board with login"                                              | **ASK**                 | "login" alone is not enough — MCP UIs also have auth.        |
| "expose a CRM as an MCP server, and also a dashboard at crm.example.com" | Both — load both skills | Explicit conjunction; dual-frontend app.                     |

## Note

On every route, `build` starts by agreeing each capability in plain
English and writing it as a `@wip` feature file before its API exists
([`feature` skill](../feature/SKILL.md)). Don't load `python/SKILL.md`
for an MCP UI or Web App: the front-door skills' reading lists name the
`python` references each step needs. A dual-frontend app reads both
lists, each reference once.

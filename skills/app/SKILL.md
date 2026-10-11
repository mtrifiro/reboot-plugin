---
name: app
description: Build a Reboot application from a user description. Every backend is designed ready for both front doors, an MCP UI (ChatGPT, Claude, VSCode, Goose) and a standalone web app, with one `User` per identity via `oauth=...`. Builds the front door(s) the prompt names (MCP/Claude/ChatGPT → `mcp-ui`; a URL/SPA/"website" → `web-app`; both named → both); otherwise builds the web app first without asking and offers the MCP UI at handoff.
argument-hint: [<app-description>]
allowed-tools: Bash, Read, Write, Glob, Grep, Edit
---

# app: Build a Reboot Application

**Say the welcome first,** the moment this skill loads, before
invoking `build` or any other skill, and before the routing line or the
scope round. It is fixed text except the examples in angle brackets:
two things from the user's brief that will be objects, and two of its
roles, in the user's words ("a class or a membership", "a member, a
trainer"). An existing project skips it.

> **Welcome to Reboot.** A Reboot app is built from your domain's
> objects and the methods on them. Each object, <a room or a
> reservation>, is a durable actor: it keeps its own state and handles
> one request at a time, so the rules you describe hold without a
> database to manage.
>
> Designing a Reboot app answers three questions, and this build
> answers them out loud:
> - **What are the objects?** Each thing with its own life, <a room or a
>   reservation>, is one object, and each rule lives on the object whose
>   data it protects.
> - **What can each object do?** Its methods: one reads, one changes
>   the object, one changes several objects all or nothing, one runs
>   over time or calls the outside world.
> - **Who may call each method?** <A guest, a manager>, or only the app.
>
> How this build proceeds:
> 1. A few questions about scope.
> 2. Features before code: each capability written as rules and
>    examples in plain English, which become the app's tests.
> 3. The domain model: the objects, their methods, and who may call
>    each, shown as a map of the app.
> 4. A working prototype of the whole scope, built to those features.
> 5. Your review on the running app, then new features one at a time.

**Voice, before anything else.** Everything said to the user, from
the first line of the session to the handoff, is a statement of fact
about the app, never the first person: no I, me, my, we or us. Not
"I'll model each suite as its own actor" but "Each suite is its own
actor"; not "I'll build a quick prototype first" but "A quick prototype
of the whole hotel comes first". The subject is the app, the design,
the build or the prototype, and "you" is the user. Say more, not less,
at the level of the domain: each step ends in two or three statements
about their objects, rules and roles and the decisions between them,
never an account of what was done, never what comes next, never which
reference or step is in hand. A sentence that starts with I is
rewritten before it is sent. The first sentence about an object says
why it exists, with the object as its subject. Sentences under about
twenty words, one idea each; no em or en dashes, no semicolons, no
parentheses; facts, not praise.

A **front door** is the way people reach a Reboot app's backend: the
interface they use to get to its data and actions. There are two: a
**web app** (a website in a browser) and an **MCP UI** (tools and views
inside an AI chat app such as Claude or ChatGPT). An app can have
either or both; the backend behind them is the same.

Decide which front door to build first, then build it with the
[`build` skill](../build/SKILL.md) plus the matching front-door skill
(`mcp-ui`, `web-app`, or both). The backend is always ready for both.

**Invoke them as skills, not as files.** In Claude Code that is the
Skill tool (`reboot:build`, then `reboot:web-app` or `reboot:mcp-ui`);
in Codex, the skill by name. Reading `SKILL.md` with Read instead puts
the same words in front of you but not the skill's own step order, and
the plugin's band and checks key on the invocation. A build that skims
the file is the one that skips the checkpoint.

## Routing

Every app gets a backend **ready for both front doors**: a `User` type,
`oauth=`, and each method's AI role and AI-facing `description=` in the
design (`build`, Design Phase). What varies is which front door is
built first. Design, the Reboot Flywheel's first stage, starts here and
ends at the build skill's "Accept the Design"
([`build/references/flywheel.md`](../build/references/flywheel.md)).

### The two destinations

- **`mcp-ui`** exposed through an MCP host (ChatGPT, Claude, VSCode,
  Goose, etc.) via MCP tools; any visual UI is embedded in the host as
  MCP UI artifacts.
- **`web-app`** served at a URL and used in a normal browser: the
  Reboot backend behind a React frontend.

### Triggers (verbatim in the prompt)

**`mcp-ui`**: `MCP` in any form (`MCP host`, `MCP server`, `mcp=Tool`,
`UI()` as a method type); `ChatGPT`, `Claude`, `VSCode`, `Goose`,
`Cursor`, Anthropic or OpenAI named as the runtime ("use this from
Claude"), not as a comparison ("like ChatGPT"); "AI tool", "tool for an
LLM or agent", "expose to an agent".

**`web-app`**: a URL or scheme (`https://…`, `localhost:`,
`example.com`); a route literal (`/login`, `/dashboard`, `/admin`);
"website", "web app", "SPA", "single-page app", "in the browser",
"served at".

Domain words (CRM, todo, dashboard, chat room), "app", "UI", "login"
or "users" are not triggers: they say what the app does, not where it
is used.

### Decision flow

1. **Both named** ("expose it to Claude and host it on the web") → after the
   welcome, say "This is a Reboot app with an MCP UI and a web app on one backend.",
   invoke [`build`](../build/SKILL.md), [`mcp-ui`](../mcp-ui/SKILL.md)
   and [`web-app`](../web-app/SKILL.md) as skills, and follow `build`
   taking both branches at each step. One `Application(oauth=...)`
   serves both with one `User` per upstream identity.
2. **Only an MCP trigger** → after the welcome, say "This is an MCP UI on a Reboot
   backend. The backend can also serve a web app.", invoke `build` and
   `mcp-ui`, and follow the `mcp-ui:` branches.
3. **Only a web-app trigger, or none (the default)** → after the welcome, say "This is a
   web app on a Reboot backend. The backend can also serve an MCP UI.",
   invoke `build` and `web-app`, and follow the `web-app:` branches.
   Never ask.
4. **"Only", "just", "no …"** ("just a website", "no web UI") → build
   that one and skip the handoff offer for the other.

**At handoff** (build Step 7), unless step 4 applied, offer the other
front door in one line: "Want this in Claude and ChatGPT too? The
backend is ready; it adds an MCP UI beside the web app." (or the
reverse). On yes, follow `build`'s Update Flow, "Adding the other
front door".

### Worked examples

| Prompt fragment | Decision |
| --- | --- |
| "a CRM for my personal relationships", "a todo list app" | `web-app`, offer MCP: no trigger |
| "a dashboard for our metrics, served at metrics.example.com" | `web-app`, offer MCP: a URL |
| "a tool I can use from Claude to track my reading list" | `mcp-ui`, offer web: the runtime |
| "just a simple website for signups" | `web-app`, no offer |
| "a CRM as an MCP server, and also a dashboard at crm.example.com" | both |

## Note

On every route, `build` writes each capability as a `@wip` feature file
from the scope round, before its API exists ([`feature`
skill](../feature/SKILL.md)). Don't invoke `python` for an MCP UI or
Web App: the front-door skills' reading lists name the `python`
references each step needs. A dual-frontend app reads both lists, each
reference once.

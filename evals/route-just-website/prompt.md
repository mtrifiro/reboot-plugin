---
description: "Saying just a website scopes the build to one front door and drops the MCP offer."
tags: [routing]
runs: 3
max_turns: 20
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating what kind of app you are building (a web app, an MCP UI for an AI host, or both) and the design so far."
---

Build just a simple website for event signups on Reboot.

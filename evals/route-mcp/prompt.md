---
description: "An MCP host named as the runtime: MCP UI first, backend ready for a web app."
tags: [routing]
runs: 3
max_turns: 20
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating which kind of app you are building (which front door or front doors) and the design so far."
---

Build a reading-list tracker on Reboot that I can use from Claude.

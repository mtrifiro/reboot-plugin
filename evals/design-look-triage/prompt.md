---
description: "List-shaped work gets a list: a triage app's primary view is a grouped list with labelled filters, not a chart."
tags: [design, look]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating what kind of app you are building (a web app, an MCP UI for an AI host, or both) and the design so far."
---

A web app on Reboot to triage a few hundred bug reports by severity and status. Show me the design before writing any code.

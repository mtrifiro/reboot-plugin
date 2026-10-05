---
description: "Domain words are not triggers: web app first, no question."
tags: [routing]
runs: 3
max_turns: 20
timeout_seconds: 420
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating which kind of app you are building (which front door or front doors) and the design so far."
---

I want a personal CRM on Reboot: people, notes about each conversation, and a timeline of when I last talked to them.

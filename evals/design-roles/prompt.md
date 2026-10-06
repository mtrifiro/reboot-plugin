---
description: "A domain with roles: the design names them and enforces which methods each may call."
tags: [design, auth]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating which kind of app you are building (which front door or front doors) and the design so far."
---

A hotel app on Reboot: front-desk staff take reservations and check guests in and out; housekeeping sees which rooms need cleaning and marks them clean. Show me the design before writing any code.

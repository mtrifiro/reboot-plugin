---
description: "The design is ready for both front doors and highly visual by default."
tags: [design]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing. End with a short summary stating which kind of app you are building (which front door or front doors) and the design so far."
---

A team kudos board on Reboot: anyone on the team can give a teammate kudos with a short note, and everyone sees the latest kudos and who has received the most. Show me the design before writing any code.

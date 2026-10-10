---
description: "The accept gate is skippable: told up front to build without stopping, the agent still shows the review table but does not wait."
tags: [design, flywheel]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing, and say what you would do at each step. End with a short summary of the design so far and what happens next."
---

Build a hotel booking app: guests book rooms for a range of nights, and a room can be booked at most once per night. Just build it; don't stop to check the design with me.

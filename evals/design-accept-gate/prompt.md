---
description: "The Reboot Flywheel's accept gate: the build stops after the domain model and feature files, shows the review table, and waits for acceptance."
tags: [design, flywheel]
runs: 3
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, AskUserQuestion]
append_system_prompt: "You are in a planning-only session: you can read files and load skills but cannot write files or run commands. Follow any skills that apply as far as you can without writing, and say what you would do at each step. End with a short summary of the design so far and what happens next."
---

Build a hotel booking app. A guest can book one or more rooms for a range of nights in a single reservation, and a room can be booked at most once per night. A guest who cancels more than 48 hours before check-in gets a full refund. After that, a manager approves any refund, and the app records the result from the payment provider.

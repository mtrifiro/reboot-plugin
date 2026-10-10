---
type: llm
weight: 2
---
PASS if, before it describes making any change to the code, API or feature files, the agent asks the user (in its text or with AskUserQuestion) whether changes should go straight onto `main` or onto a branch for each change. FAIL if it decides either way without asking (for example "I'll create a branch" or "I'll work on main"), or never raises where the change goes. Quote what you relied on.

---
type: llm
weight: 2
---
PASS if the response stops for the user before any implementation: it asks them to agree the features or to accept the design (the domain model and the feature files), or to say what to change, and the implementation (servicers, frontend, tests) is placed after that answer. A numbered plan whose later steps build the app once the user has accepted is fine; so is stopping at the features, before the API, since the build skill's checkpoint comes after them. FAIL if the response says it would go on to build without waiting for the user's answer, or never asks the user anything about the design. Quote what you relied on.

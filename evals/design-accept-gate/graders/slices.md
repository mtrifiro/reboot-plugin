---
type: llm
weight: 1
---
PASS if the design is presented feature by feature: after each feature (booking, cancellation, and so on) is described in plain English, the response shows the state types, methods or review-table rows that feature adds before moving to the next, or asks whether there is another feature, so the model grows a slice at a time. FAIL if the whole domain model appears in one block with no feature-by-feature build-up. A final table that repeats every row is fine when the slices came before it. Quote what you relied on.

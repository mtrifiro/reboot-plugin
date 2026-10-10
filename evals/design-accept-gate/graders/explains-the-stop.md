---
type: llm
weight: 1
arm: with-only
---
PASS if, where the response stops for the user, it asks for their go-ahead or their changes in plain words and says what the decision covers (the domain model and the feature files, in the app's own terms: rooms, reservations, refunds) or why now is the moment to change them (before anything is built on them). FAIL if it stops with a bare question, or frames the stop as a rule imposed on the user (for example "nothing is built until you accept", "no implementation happens before that", or "silence does not count"). Quote what you relied on.

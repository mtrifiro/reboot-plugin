---
type: llm
weight: 2
---
PASS if the design maps the rules the prompt implies (a room is booked at most once per night; a reservation for several rooms books every room or none; a cancellation more than 48 hours before check-in is refunded automatically and a later one waits for a manager's approval; the payment provider's result is recorded) each to the state type that owns it, the method that enforces it, that method's kind (Reader, Writer, Transaction or Workflow) and who may call it, in prose, a list or a table, and names an example or scenario for the rules where it gives one. A fuller rule-by-rule table may be promised for after the API and feature files are written; that is fine. FAIL if the design is only a list of types and methods with no rule mapped to an owner, or names the rules without a method and a kind for each. Quote what you relied on.

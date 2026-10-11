---
type: llm
weight: 2
---
PASS if the design maps each rule of the feature it builds first (for the booking feature the prompt implies: a room is booked at most once per night; a reservation for several rooms books every room or none) to the state type that owns it, the method that enforces it, that method's kind (Reader, Writer, Transaction or Workflow) and who may call it, in prose, a list or a table, names an example or scenario for each, and either maps the remaining rules the same way (a cancellation more than 48 hours before check-in is refunded automatically and a later one waits for a manager's approval; the payment provider's result is recorded) or names them as features in a backlog to come after the first prototype runs. FAIL if the design is only a list of types and methods with no rule mapped to an owner, names the rules without a method and a kind for each, or drops the cancellation and refund rules without a backlog. Quote what you relied on.

---
type: llm
weight: 1
---
PASS if, while describing the build, the response explains at least two ideas of how Reboot works in terms of the user's own app (for example: a state type is an actor whose methods run one at a time, so two guests cannot book the same night; a reader, writer, transaction or workflow differs in what a method may touch; an authorizer decides who may call a method and is enforced in production; a scenario is a rule in English that the tests run; the dev loop restarts on an edit; `rbt inspect` reads what is stored). FAIL if it names Reboot features without tying them to the app, or explains nothing about how Reboot works. Quote what you relied on.

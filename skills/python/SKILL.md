---
name: python
description: Reboot Python framework for building transactional microservices with durable actor state; APIs are defined in pydantic Python (`reboot.api`). Use when writing Python for a Reboot application: defining APIs with reader/writer/transaction/workflow methods; changing an API of an application already deployed or holding persisted state (schema evolution rules; see `references/api-schema-evolution.md`); implementing Servicers; calling actor refs across services; scheduling work (including recurring / "cron" jobs); building durable workflows with the right call primitive (`.per_workflow(alias)` / `.per_iteration(alias)` / `.always()` for Reboot calls; `at_least_once` / `at_most_once` for external calls; `until` / `until_changes` for reactive waiting on Reboot state); calling an LLM / building an AI agent in the backend via the durable `reboot.agents.pydantic_ai.Agent`; or testing with Gherkin feature files run by `reboot.bdd` (and, for crash recovery, the `Reboot()` test harness).
license: Apache-2.0
metadata:
  author: reboot
  version: "1.0.0"
  organization: Reboot
  date: April 2026
  abstract: Comprehensive guide for building Reboot Python applications. Covers pydantic API definitions, the Servicer pattern, reader/writer/transaction/workflow contexts, the workflow call-classification model (Reboot scopes `.per_workflow` / `.per_iteration` / `.always()` for Reboot calls; external-call primitives `at_least_once` / `at_most_once`; reactive-waiting primitives `until` / `until_changes`), actor refs, scheduling, the standard library (OrderedMap, Queue, PubSub, Presence, Item), and testing.
---

# Reboot Python Best Practices

> **Building an MCP UI or Web App?** Follow
> [`../build/SKILL.md`](../build/SKILL.md) and your front-door skill;
> this skill is the reference catalog and the entry point for
> backend-only work.

> **Version notices:** if `rbt` reports a version mismatch or a newer
> Reboot, follow the [upgrade skill](../upgrade/SKILL.md).

Reboot APIs are defined in pydantic Python (`reboot.api`) and
code-generated into typed Servicer base classes; you implement `async`
methods that receive a typed context (`ReaderContext`, `WriterContext`,
`TransactionContext`, or `WorkflowContext`).

## When to Apply

Any Python for a Reboot app (see the description). Specifically:

- Changing the API of an app that has persisted state or is deployed:
  read `references/api-schema-evolution.md` first.
- Workflows: pick primitives per `servicer-workflow-calls.md` —
  `.per_workflow(alias)` / `.per_iteration(alias)` / `.always()` for
  Reboot calls; `at_least_once` by default for external calls
  (`at_most_once` for the rare non-retryable one); `until` /
  `until_changes` for reactive waiting.
- Scheduling via `ref.schedule(when=...).method(context)`; recurring /
  "cron" jobs self-reschedule at an absolute wall-clock time.
- Calls to another actor: `Service.ref(id).method(context, ...)`.
- The standard library (`OrderedMap`, mailgun, etc.).
- Verifying any change: **type-check with `mypy backend/ tests/` and fix all
  errors** (see "Type-checking" below).

## Rule Categories by Priority

References are grouped by filename prefix into the categories, in
priority order, of `references/_sections.md`; the catalog below follows
that order. `Workflow(...)` is the fourth servicer context type; its
router `servicer-workflow.md` sends you to six parts.

## Critical Rules

### Servicer Pattern

Subclass the generated `<Type>.Servicer`; one `async def` per RPC, whose
second argument's context type is set by the API factory
(`Reader`/`Writer`/`Transaction`/`Workflow`):

```python
from chat_room.v1.chat_room_rbt import ChatRoom
from reboot.aio.contexts import ReaderContext, WriterContext


class ChatRoomServicer(ChatRoom.Servicer):
    # No `authorizer()` yet: `rbt dev` warns and allows, but the
    # `Reboot()` test harness, `rbt serve` and Reboot Cloud deny
    # every external call. Write a real rule before the first test
    # (references/servicer-authorizer.md).

    async def messages(
        self,
        context: ReaderContext,
    ) -> ChatRoom.MessagesResponse:
        return ChatRoom.MessagesResponse(messages=self.state.messages)

    async def send(
        self,
        context: WriterContext,
        request: ChatRoom.SendRequest,
    ) -> None:
        self.state.messages.append(request.message)
```

### Application Entry

`main` awaits
`Application(servicers=[ChatRoomServicer], initialize=initialize).run()`
under `asyncio` (`asyncio.run`); `initialize` may
construct a singleton implicitly by its first write. Full file:
`references/lifecycle-application-entry.md`.

### The API File Drives Code Generation

Never hand-edit generated `*_rbt.py`; the pydantic API file is the
source of truth (see `references/api-pydantic.md`):

```python
from reboot.api import API, Field, Methods, Model, Reader, Type, Writer


# Every Field needs an explicit default and a description (see Key
# Constraints below).
class ChatRoomState(Model):
    messages: list[str] = Field(
        tag=1,
        default_factory=list,
        description="Every message posted to the room, oldest first.",
    )

class SendRequest(Model):
    message: str = Field(
        tag=1,
        default="",
        description="The text to post, as the sender typed it.",
    )

class MessagesResponse(Model):
    messages: list[str] = Field(
        tag=1,
        default_factory=list,
        description="Every message posted so far, oldest first.",
    )

api = API(
    ChatRoom=Type(
        state=ChatRoomState,
        methods=Methods(
            messages=Reader(
                request=None,
                response=MessagesResponse,
                description="Every message posted so far, oldest first.",
                mcp=None,
            ),
            send=Writer(
                request=SendRequest,
                response=None,
                description="Post one message to the room.",
                mcp=None,
            ),
        ),
        description="One chat room, and everyone posting into it.",
    ),
)
```

`rbt generate` (run by `rbt dev run`) emits `<pkg>/<v>/<name>_rbt.py`:
the `<Type>` class with nested request/response messages, the `Servicer`
base, and the `.ref(id)` factory.

### Key Constraints

- Each method's context type **must match** its factory: `Reader(...)` →
  `ReaderContext`, `Writer(...)` → `WriterContext`, `Transaction(...)` →
  `TransactionContext`, `Workflow(...)` → `WorkflowContext`.
- `self.state` is read-only in `ReaderContext`; mutate it only in
  `WriterContext` or `TransactionContext`. Workflows mutate via
  `Service.ref().write(context, callback)`, not `self.state`, because
  they re-execute on replay.
- `.rbtrc` is **line-based**, not YAML: `<subcommand> <flag>` per line.
  Use `--application-name=<app>` (canonical since Reboot 1.0.4; `--name`
  is a deprecated alias that warns).
- The actor's ID is `self.ref().state_id` in writer/reader/transaction
  methods and `context.state_id` in workflows; `self.state_id` raises
  `AttributeError`.
- **Every `Field(tag=N)` needs an explicit zero-value default**
  (`default=""`, `default=0`, `default=0.0`, `default=False`,
  `default_factory=list`, etc.) in state, request/response and error
  Models: (1) `model_construct()` drops fields without declared
  defaults, so reads raise `AttributeError`; (2) non-zero defaults raise
  `UserPydanticError` at import time. Set domain defaults (`turn="r"`,
  `delay=1.0`) in the constructor method.
- **Every `Field(tag=N)` gets a `description=`** of what the value means,
  in every Model; the dashboard shows it beside the property and flags
  one without. Describe the value, not the type: "What the account
  holds, in dollars, never below zero", not "The balance (float)".
- Cross-actor and external-service calls belong in `TransactionContext`
  (one-shot) or `WorkflowContext` (durable, long-running).
- **Changing an API after the app has persisted state or been
  deployed?** Read `references/api-schema-evolution.md` first.
- Pass actor-method arguments as **kwargs**:
  `await ref.deposit(context, amount=10)`, not
  `await ref.deposit(context, DepositRequest(amount=10))`.
- **`Queue`, `Topic`, `OrderedMap`, `Presence`, `Item` are
  stdlib actor names — use them, don't redefine them.** When a design
  names one ("publish to a `Topic`", "members in an `OrderedMap`"),
  _import_ the stdlib actor; a same-named pydantic `Model` forfeits its
  durability, ordering, blocking semantics and concurrency guarantees.
  See the stdlib table under "Implementing a Servicer".

## How to Use

Footguns are spread across references; skipping the right one means a
runtime error it would have prevented. Load what the task requires from
the lists below:

- Read each reference **once**, at the step that needs it (everything
  read is re-sent every later turn); skip a line ending *Only when …*
  unless it holds.
- **One per tool call**: `cat`-ing several can exceed the output limit
  and be cut off.
- Never read generated or installed source (`*_rbt.py`,
  `*_rbt_react.ts`, `site-packages/`, `node_modules/`, codegen
  templates) — the costliest way to learn a fact; the references hold
  the shapes. If something isn't covered, bound the output (a targeted
  `grep -n … | head -40`, or `sed -n '<start>,<end>p'` over a known
  range), never a whole generated file.

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. MCP UIs
and Web Apps read their builder skill's lists instead. -->

### Defining the API

<!-- generated:start reading-list front-door=backend-only step=api -->
- `references/api-methods.md` — The factory fixes the servicer's context type, and `mcp=` is required; `Reader`/`Writer`/`Transaction`/`Workflow`, `factory=True`, `errors=`, `description=`.
- `references/api-pydantic.md` — A non-zero `Field` default is rejected at import; tags, zero defaults, `API(...)` wiring, Request/Response naming.
- `references/state-actor-decomposition.md` — A Type with unrelated field clusters serializes writers and grows a God `User`; split it into separate Types.
- `references/state-collections.md` — Never `list[Entity]` on parents; decide if each item is its own Type, then `list[Sub]`, ID list or `OrderedMap`.
- `references/state-nested-models.md` — Never a state `Model` inside another; group related fields in nested non-state `Model`s, mutated in place.
- `references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `references/api-errors.md` — only when the API declares typed errors.
- `references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

### The project shell

<!-- generated:start reading-list front-door=backend-only step=shell -->
- `references/lifecycle-application-entry.md` — Pass servicer classes, not instances, and register stdlib libraries; `async def main()` awaiting `Application(servicers=[...], initialize=...).run()`.
- `references/lifecycle-project-setup.md` — Never add `__init__.py` or edit `*_rbt.py`; copy `build/templates/<front-door>/`; mypy sees `self.state` as `Any`: typed locals.
- `references/lifecycle-rbtrc.md` — `.rbtrc` is line-based, not YAML; `--application-name` not `--name`; `--env-file` for secrets; `serve run` lines; named configs.
- `references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

### Implementing a Servicer

<!-- generated:start reading-list front-door=backend-only step=servicer -->
- `references/lifecycle-initialize-hook.md` — Each `initialize` call runs once per app lifetime, not per boot; migrations need new aliases; failures retry forever.
- `references/rpc-calls.md` — Writers can't call writers or transactions, even their own; caller identity doesn't travel; writer cycles deadlock; pass kwargs.
- `references/servicer-constructor.md` — Never set initial state in `__init__`; a second call aborts `StateAlreadyConstructed`; use `Transaction(factory=True)` if it constructs others.
- `references/servicer-reader.md` — Mutating `self.state` in a reader is silently discarded; signature must match the API; reader-to-reader calls; subscription re-runs.
- `references/servicer-writer.md` — Writers mutate one actor: no writes to others, no external calls, schedule only on self; errors roll back.
- `references/rpc-constructor-calls.md` — Constructors aren't on `.ref(id)` and a second call aborts; call `<X>.<ctor>(context, id, ...)`; get-or-create.
- `references/rpc-refs.md` — `self.state_id` raises, use `self.ref().state_id`; probing existence without `StateNotConstructed`; caller-supplied IDs; reserved method names.
- `references/servicer-workflow.md` — only when you declared a `Workflow`.
- `references/agent-pydantic-ai.md` — only when the backend calls an LLM.
- `references/agent-tools.md` — only when an LLM agent needs tools that read or change Reboot state.
- `references/crypto-root-keys.md` — only when building your own key-derivation feature.
- `references/lifecycle-seeding.md` — only when the app seeds data in `initialize` or a script.
- `references/scheduling-basic.md` — only when deferring work with `schedule()` or `spawn(when=…)`.
- `references/servicer-transaction.md` — only when you declared a `Transaction`.
- `references/stdlib-ciphertext.md` — only when storing secrets or PII encrypted at rest.
- `references/stdlib-ordered-map.md` — only when the design uses an `OrderedMap`.
- `references/stdlib-queue.md` — only when the design uses a work `Queue`.
- `references/rpc-forall.md` — only when fanning one call out to many actors.
- `references/scheduling-recurring.md` — only when the app needs a recurring or cron job.
- `references/stdlib-presence.md` — only when tracking who is connected (presence).
- `references/stdlib-pubsub.md` — only when publishing to topics (pub/sub).
- `references/stdlib-item.md` — only when using the stdlib `Item` value envelope.
<!-- generated:end -->

The stdlib already provides these; read the reference **before**
writing your own actor type — a hand-rolled `Queue` / `OrderedMap` /
etc. is almost always wrong:

| You need...                                       | Use                 | Reference                |
| ------------------------------------------------- | ------------------- | ------------------------ |
| Durable FIFO — work queue, job queue, intake      | `Queue`             | `stdlib-queue.md`        |
| Sorted key-value with pagination / ordering       | `OrderedMap`        | `stdlib-ordered-map.md`  |
| Presence — who's online / connected               | `Presence`          | `stdlib-presence.md`     |
| Pubsub / broadcast / fan-out to subscribers       | `PubSub`            | `stdlib-pubsub.md`       |
| Item builder for `Queue` / `PubSub` payloads      | `Item`              | `stdlib-item.md`         |
| Store OAuth access/refresh tokens from a provider | `OAuthTokenManager` | `stdlib-oauth-tokens.md` |
| A field holds a password/API key/secret/PII       | `Ciphertext`        | `stdlib-ciphertext.md`   |
| Encrypt at rest / crypto-shred (right-to-erasure) | `Ciphertext`        | `stdlib-ciphertext.md`   |

Each stdlib reference lists its registration: forgetting
`<thing>_library()` and `<thing>.servicers()` in `Application(...)`
fails on the type's first call (unknown state type), not at startup;
only a missing dependency library fails at startup with
`Missing required libraries: …`.

Backend LLM calls (chat, agents, tool-using assistants) go through the
durable `reboot.agents.pydantic_ai.Agent`, **never** a raw `anthropic` /
`openai` SDK or bare `pydantic_ai.Agent`, which re-hits (and re-bills)
the provider on every workflow replay. Read `agent-pydantic-ai.md`
first.

### Authorization

<!-- generated:start reading-list front-door=backend-only step=auth -->
- `references/auth-allow-deny.md` — `allow()` to silence warnings, pass tests or mark internal methods makes them public; `deny()` blocks everyone; `return allow()`.
- `references/auth-allow-if.md` — `is_app_internal` in `any` turns anonymous `Unauthenticated` into `PermissionDenied`; `allow_if(all=[...])` or `allow_if(any=[...])`, never both or nested; `all` short-circuits.
- `references/auth-built-in-predicates.md` — Token predicates alone deny servicer-to-servicer calls; `has_verified_token`, `is_app_internal`, `state_id_is_user_id` and compositions.
- `references/servicer-authorizer.md` — Without real rules every external call is denied; identity doesn't cross servicer calls; tokenless paths; `oauth=` vs `token_verifier=`.
- `references/auth-custom-predicates.md` — Predicates must be keyword-only with `**kwargs` and check `context.app_internal` first; per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`.
- `references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
<!-- generated:end -->

### Testing

Tests are Gherkin `.feature` files run by `reboot.bdd`; the order of
work (agree in English, tag `@wip`, iterate on scenarios) is the
[`feature` skill](../feature/SKILL.md).

<!-- generated:start reading-list front-door=backend-only step=tests -->
- `references/patterns-idempotency.md` — Replayed calls return the first run's response; what `IdempotencyUncertainError` means, when retries need keys, idempotent `create`/`initialize`.
- `references/testing-features.md` — Built-in steps match their exact spelling; who calls, `creates` / `does`, saved values, `eventually`, aborts, `@wip`, custom steps.
- `references/testing-project-setup.md` — Missing `pytest.ini` paths break `_rbt` imports; no `pytest-asyncio`; `tests/` layout, fixture with `allowed_origins=[]`, `reboot[dev]`.
- `references/testing-external-context.md` — only when writing custom steps or harness tests.
- `references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

### Type-checking (do this after every change)

The generated `*_rbt.py` stubs are fully typed, so mypy catches what a
visual read misses: wrong field types, missing or misspelled kwargs, the
wrong context type, nonexistent response fields, wrong return types.

- Every project ships a project-root `.mypy.ini` (config and rationale
  in `references/lifecycle-project-setup.md`) putting `backend/src`,
  `backend/api`, `tests` and `api` on `mypy_path` with
  `explicit_package_bases = True` so `*_rbt.py` modules resolve. Missing?
  Create it first — `mypy` is useless without it.
- After any Python edit under `backend/`, run `uv run mypy backend/ tests/`
  (or `mypy backend/ tests/`) from the project root; fix **every** error.
- "Done" means both `mypy backend/ tests/` and `uv run pytest` are green.

## Available Reference Files

Files in `references/` are named `{prefix}-{topic}.md`, prefix per
`references/_sections.md`.
Load only what the task needs (the lists above say when). Full catalog:

<!-- generated:start catalog skill=python -->
**Lifecycle**
- `references/lifecycle-application-entry.md` — Define the Application Entry Point
- `references/lifecycle-backup-restore.md` — Back Up and Restore — `rbt export`, Expunge, `rbt import`
- `references/lifecycle-dev-loop.md` — Debug the Dev and Test Loop
- `references/lifecycle-dockerfile.md` — Write a Reboot Cloud Dockerfile
- `references/lifecycle-initialize-hook.md` — Use `initialize` for First-Run Setup
- `references/lifecycle-project-setup.md` — Set Up a Reboot Python Project
- `references/lifecycle-rbtrc.md` — Configure `.rbtrc` Correctly
- `references/lifecycle-reboot-cloud.md` — Deploy on Reboot Cloud
- `references/lifecycle-secrets.md` — Set Secrets — Env Vars in Dev, `rbt cloud secret set` in Cloud
- `references/lifecycle-seeding.md` — Seed Data in Batches, Sequentially, with Aliases

**API**
- `references/api-errors.md` — Define and Raise Typed Errors
- `references/api-methods.md` — Pick a Method Factory — `Reader`, `Writer`, `Transaction`, or `Workflow`
- `references/api-pydantic.md` — Define APIs in Pydantic
- `references/api-schema-evolution.md` — Schema Evolution Is Additive-Only on Deployed Applications

**Servicer**
- `references/servicer-authorizer.md` — Authorizers — When to Write Them, What They See
- `references/servicer-constructor.md` — Handle Constructor Methods
- `references/servicer-reader.md` — Implement Reader Methods
- `references/servicer-transaction.md` — Implement Transaction Methods
- `references/servicer-workflow-calls.md` — Classifying Workflow Calls and Calling Reboot (via `servicer-workflow.md`)
- `references/servicer-workflow-declare.md` — Declaring and Starting a Workflow (via `servicer-workflow.md`)
- `references/servicer-workflow-exit.md` — How a Workflow Exits (via `servicer-workflow.md`)
- `references/servicer-workflow-external.md` — Calling External Systems from a Workflow (via `servicer-workflow.md`)
- `references/servicer-workflow-loop.md` — Iterating in a Workflow with context.loop (via `servicer-workflow.md`)
- `references/servicer-workflow-wait.md` — Waiting in a Workflow with until and until_changes (via `servicer-workflow.md`)
- `references/servicer-workflow.md` — Building Durable Workflows
- `references/servicer-writer.md` — Implement Writer Methods

**Agent**
- `references/agent-pydantic-ai.md` — Call LLMs via the Reboot `Agent`, Never a Raw SDK
- `references/agent-tools.md` — Give the Agent Tools with `@agent.tool` and `@agent.tool_plain`

**Stdlib**
- `references/stdlib-ciphertext.md` — Use `Ciphertext` for Envelope Encryption and Crypto-Shredding
- `references/stdlib-item.md` — Use `Item` for Heterogeneous Values in Stdlib Containers
- `references/stdlib-oauth-tokens.md` — Store Provider OAuth Tokens in `OAuthTokenManager`, Not Hand-Rolled `Ciphertext`
- `references/stdlib-ordered-map.md` — Use `OrderedMap` for Distributed Sorted Key/Value Storage
- `references/stdlib-presence.md` — Track Online Subscribers with `Presence`
- `references/stdlib-pubsub.md` — Use `Topic` for Publish/Subscribe Fan-Out to Queues
- `references/stdlib-queue.md` — Use `Queue` for Durable FIFO Work Queues

**Crypto**
- `references/crypto-root-keys.md` — Derive Your Own Keys from Reboot's Managed Crypto Root Keys (with Rotation)

**State**
- `references/state-actor-decomposition.md` — Split a State Type That Holds Multiple Concerns
- `references/state-collections.md` — Pick the Right Shape for Each Collection
- `references/state-nested-models.md` — Compose State with Nested `Model`s
- `references/state-scalar-fields.md` — Use Zero-Value Defaults for Scalar State Fields

**Auth**
- `references/auth-allow-deny.md` — `allow()` and `deny()` — Narrow Uses, Not Defaults
- `references/auth-allow-if.md` — Compose Predicates with `allow_if(all=...)` / `allow_if(any=...)`
- `references/auth-built-in-predicates.md` — Built-In Authorizer Predicates
- `references/auth-claims.md` — Identity Claims and `User.set_claims`
- `references/auth-custom-predicates.md` — Write Custom Authorizer Predicates
- `references/auth-external-api-calls.md` — Calling External-Service APIs on the User's Behalf

**RPC**
- `references/rpc-calls.md` — Call Actor Methods with Kwargs and a Context
- `references/rpc-constructor-calls.md` — Use `Service.create` and `Service.<ctor>` for Constructor Calls
- `references/rpc-forall.md` — Fan Out Calls with `Service.forall(ids).method(context)`
- `references/rpc-refs.md` — Get Actor References with `Service.ref(id)`

**Scheduling**
- `references/scheduling-basic.md` — Schedule Future Work with `ref.schedule(when=...)`
- `references/scheduling-recurring.md` — Recurring and "Cron" Schedules by Self-Rescheduling

**Testing**
- `references/testing-external-context.md` — Drive Tests with `create_external_context`, Assert, Wait, and Mock
- `references/testing-failure-recovery.md` — Test Failure Recovery — `rbt.down()` and `rbt.up(revision=...)`
- `references/testing-features.md` — Specify Behavior in Feature Files
- `references/testing-harness.md` — Spin Up Tests with the `Reboot()` Harness
- `references/testing-project-setup.md` — Lay Out a Reboot Backend Test Suite
- `references/testing-web-app.md` — Drive the Web App from Scenarios

**Patterns**
- `references/patterns-common-gotchas.md` — Every "Never" in One List
- `references/patterns-cross-actor-reads.md` — Cross-Actor Reads and Reader Shape
- `references/patterns-error-handling.md` — Error Handling Patterns
- `references/patterns-idempotency.md` — Make Constructor and `initialize` Calls Idempotent
- `references/patterns-load-and-benchmarking.md` — Load, Cost and Benchmarking
- `references/patterns-react-state.md` — React State on Top of Reactive Readers
- `references/patterns-time-and-randomness.md` — Time and Randomness in Method Bodies

**React**
- `references/react-generated-client.md` — The Generated React Client Contract

**Lookups**
- `references/errors.md` — Look Up an Error
<!-- generated:end -->

## External References

- https://docs.reboot.dev/
- Public examples:
  - https://github.com/reboot-dev/reboot-bank-pydantic (pydantic API definition)

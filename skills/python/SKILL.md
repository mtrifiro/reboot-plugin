---
name: python
description: Reboot Python framework for building transactional microservices with durable actor state. APIs are defined in pydantic Python (`reboot.api`). Use this skill when writing Python code for a Reboot application, defining APIs with reader/writer/transaction/workflow methods, changing an API of an application that has already been deployed or has persisted state (schema evolution rules; see `references/api-schema-evolution.md`), implementing Servicers, calling actor refs across services, scheduling work (including recurring / "cron" jobs), building durable workflows with the right call primitive (`.per_workflow(alias)` / `.per_iteration(alias)` / `.always()` for Reboot calls; `at_least_once` / `at_most_once` for external calls; `until` / `until_changes` for reactive waiting on Reboot state), calling an LLM / building an AI agent in the backend via the durable `reboot.agents.pydantic_ai.Agent`, or testing Reboot applications with Gherkin feature files run by `reboot.bdd` (and, for crash recovery, the `Reboot()` test harness).
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
> [`../build/SKILL.md`](../build/SKILL.md) and your front-door skill
> instead; this skill is the reference catalog and the entry point
> for backend-only work.

> **Version notices:** if `rbt` reports a version mismatch or that a
> newer Reboot is available, the [upgrade skill](../upgrade/SKILL.md)
> says how and when to react.

Guide for building transactional microservices in Python with the Reboot
framework. Reboot APIs are defined in pydantic Python
(`reboot.api`) and code-generated into typed Servicer base classes;
you implement `async` methods that receive a typed context
(`ReaderContext`, `WriterContext`, `TransactionContext`, or
`WorkflowContext`).

## When to Apply

Reference these guidelines when:

- Scaffolding a new Reboot Python project (`.rbtrc`, `pyproject.toml`,
  application entry point)
- Defining or modifying an API in pydantic Python (state,
  reader/writer/transaction/workflow methods, errors, constructors)
- Changing the API of an application that has persisted state or has
  been deployed — read `references/api-schema-evolution.md` first
- Implementing or modifying a Servicer
- Calling another actor via `Service.ref(id).method(context, ...)`
- Building a durable workflow with `WorkflowContext`, picking the right
  primitive per `servicer-workflow-calls.md` (Reboot calls use
  `.per_workflow(alias)` / `.per_iteration(alias)` / `.always()`;
  external calls default to `at_least_once`, with `at_most_once` for
  the rare non-retryable call)
  plus `until` / `until_changes` for reactive waiting
- Scheduling work via `ref.schedule(when=...).method(context)`,
  including recurring / "cron" jobs (self-rescheduling at an absolute
  wall-clock time)
- Calling an LLM or building an AI agent in the backend via the
  durable `reboot.agents.pydantic_ai.Agent`
- Using the standard library (`OrderedMap`, mailgun, etc.)
- Writing tests: Gherkin feature files run by `reboot.bdd`, and
  crash-recovery tests on the `Reboot()` harness
- Verifying any change: **type-check with `mypy backend/ tests/` and fix all
  errors** before considering Python work done (see "Type-checking"
  below)

## Rule Categories by Priority

References are grouped by filename prefix into the categories, in
priority order, defined in `references/_sections.md`; the catalog
under "Available Reference Files" lists them in that order.

The `Workflow(...)` context method is the fourth servicer context
type alongside reader / writer / transaction; its reference is the
router `servicer-workflow.md`, which sends you to six parts.

## Critical Rules

### Servicer Pattern

A Reboot Servicer subclasses the generated `<Type>.Servicer` base class and
implements one `async def` per RPC. Each method takes a typed context as the
second argument; that type is determined by the API method factory
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

A Reboot application's `main` constructs an `Application` with the list of
Servicer classes and runs it under `asyncio`:

```python
import asyncio
from reboot.aio.applications import Application
from reboot.aio.external import InitializeContext
from chat_room.v1.chat_room_rbt import ChatRoom
from chat_room_servicer import ChatRoomServicer


async def initialize(context: InitializeContext):
    # Implicitly construct the singleton on first write.
    await ChatRoom.ref("reboot-chat-room").send(context, message="Hello!")


async def main():
    await Application(
        servicers=[ChatRoomServicer],
        initialize=initialize,
    ).run()


if __name__ == '__main__':
    asyncio.run(main())
```

### The API File Drives Code Generation

Never hand-edit generated `*_rbt.py` files. The pydantic API definition
file is the source of truth (see `references/api-pydantic.md`):

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

`rbt generate` (run automatically by `rbt dev run`) emits
`<pkg>/<v>/<name>_rbt.py` with the `<Type>` class, request/response
messages nested as attributes, the `Servicer` base class, and the
`.ref(id)` factory.

### Key Constraints

- The context type in each method **must match** the API method
  factory. `Reader(...)` requires `ReaderContext`; `Writer(...)`
  requires `WriterContext`; `Transaction(...)` requires
  `TransactionContext`; `Workflow(...)` requires `WorkflowContext`.
- `self.state` is read-only inside `ReaderContext`. Mutate it only inside
  `WriterContext` or `TransactionContext`. Workflows mutate state by
  calling `Service.ref().write(context, callback)` — not `self.state` —
  because workflows can re-execute on replay.
- `.rbtrc` is **line-based**, not YAML. Each line is `<subcommand> <flag>`.
  Use `--application-name=<app>` (canonical since Reboot 1.0.4; `--name`
  still works as a deprecated alias but warns).
- The actor's ID is `self.ref().state_id` inside writer/reader/
  transaction methods, and `context.state_id` inside workflows.
  `self.state_id` does not exist and raises `AttributeError`.
- **Every `Field(tag=N)` needs an explicit zero-value default**
  (`default=""`, `default=0`, `default=0.0`, `default=False`,
  `default_factory=list`, etc.). Two layered rules:
  (1) `model_construct()` drops fields lacking declared defaults, so
  reads `AttributeError`; (2) only the type's zero value is accepted —
  non-zero defaults raise `UserPydanticError` at import time. Set
  domain defaults (`turn="r"`, `delay=1.0`, etc.) inside the
  constructor method, not on the Field. Applies to state,
  request/response, and error Models.
- **Every `Field(tag=N)` gets a `description=`** saying what the
  value means, in state, request, response, and error Models alike.
  The dashboard shows it beside the property, and a property without
  one shows a request to add it. Never add a property without a
  description, and describe the value, not the type: "What the
  account holds, in dollars, never below zero", not "The balance
  (float)".
- Cross-actor and external-service calls belong in `TransactionContext`
  (one-shot) or `WorkflowContext` (durable, long-running).
- **Changing an API after the application has persisted state or has
  been deployed?** Read `references/api-schema-evolution.md` to
  understand the rules you must follow for API schema evolution.
- Pass arguments to actor methods as **kwargs**, not as Request wrappers:
  `await ref.deposit(context, amount=10)`, not
  `await ref.deposit(context, DepositRequest(amount=10))`.
- **`Queue`, `Topic`, `OrderedMap`, `Presence`, `Item` are
  stdlib actor names — use them, don't redefine them.** If a
  design or task names any of these (e.g. "publish to a
  `Topic`", "track members in an `OrderedMap`", "subscribe a
  `Queue`", "presence shows who's online"), the answer is to
  _import_ the stdlib actor — not to declare a pydantic `Model`
  with the same name. Defining your own `Topic` / `Queue` /
  etc. forfeits durability, ordering, blocking semantics, and
  concurrency guarantees the stdlib already provides. See the
  trigger table under "How to Use → Using stdlib state types"
  below.

## How to Use

Most footguns in this skill are **distributed across reference files**
— skipping the right reference means hitting a runtime error that the
docs would have prevented. Before writing code, load the references
the task actually requires from the lists below, at the step that
needs them. A line ending *Only when …* is skipped unless that is
true of your app.

Everything you read stays in the conversation and is re-sent on every
later turn, so read a reference at the step that needs it rather than
all of them up front, read each one **once**, and read **one per tool
call** (`cat`-ing several at once can exceed the tool's output limit
and be cut off). That cost is also
why generated and installed source — `*_rbt.py`, `*_rbt_react.ts`,
`site-packages/`, `node_modules/`, codegen templates — is the most
expensive place in the system to learn a fact: the shapes worth
knowing are written out in the references below. When something
genuinely isn't covered, bound the output hard (a targeted
`grep -n … | head -40`, or `sed -n '<start>,<end>p'` over a known
range), never a whole generated file.

<!-- The lists below are generated from each reference's frontmatter
by tools/gen-index.py. Edit the frontmatter, not the lists. MCP UIs
and Web Apps read their builder skill's lists instead. -->

### Defining the API

<!-- generated:start reading-list front-door=backend-only step=api -->
- `references/api-methods.md` — Which factory (`Reader`, `Writer`, `Transaction`, `Workflow`) and the servicer signature and context type each obliges; `factory=True` marks creation; `errors=`, `description=` and the required `mcp=`.
- `references/api-pydantic.md` — Every `Field` needs a tag and a zero-value default (non-zero is rejected at import time); wire declarations through `API(...)`; generated Request/Response names come from the method name, not the class.
- `references/state-actor-decomposition.md` — Split a Type whose fields cluster by unrelated concern (auth, persona, background engine, cache) into separate Types, or its writers serialize and `User` becomes a God actor.
- `references/state-collections.md` — Decide whether each "list of X" item is its own state Type (usually yes), then pick `list[Sub]`, `list[str]` of IDs, or an `OrderedMap`; never `list[Entity]` on a parent.
- `references/state-nested-models.md` — Group related fields into nested non-state `Model`s instead of parallel flat names, and mutate them in place; never put a state `Model` inside another state `Model`.
- `references/api-schema-evolution.md` — only when changing an API that is deployed or has persisted state.
- `references/api-errors.md` — only when the API declares typed errors.
- `references/state-scalar-fields.md` — only when a field holds a secret, token or PII, or you want a non-zero default.
<!-- generated:end -->

### The project shell

<!-- generated:start reading-list front-door=backend-only step=shell -->
- `references/lifecycle-application-entry.md` — An `async def main()` that awaits `Application(servicers=[...], initialize=...).run()`; pass servicer classes, not instances; register stdlib libraries alongside your servicers.
- `references/lifecycle-project-setup.md` — Copy `build/templates/<front-door>/`: layout, `pyproject.toml`, `.gitignore`, `.mypy.ini`. No `__init__.py`; never edit `*_rbt.py`; mypy sees `self.state` as `Any` — use typed locals.
- `references/lifecycle-rbtrc.md` — `.rbtrc` is line-based `<subcommand> <flag>`, not YAML; `--application-name` (not `--name`) persists state; `--env-file` for secrets; `serve run` lines for production; named configs.
- `references/lifecycle-secrets.md` — only when the app needs secrets (API keys, OAuth client secrets).
<!-- generated:end -->

### Implementing a Servicer

<!-- generated:start reading-list front-door=backend-only step=servicer -->
- `references/lifecycle-initialize-hook.md` — Each `initialize` call runs once in the app's lifetime, not per boot, so a migration needs a new alias; create singletons here, not in `__init__`; failures retry forever.
- `references/rpc-calls.md` — Pass kwargs: `await ref.deposit(context, amount=10)`; writers and transactions can't be called from a WriterContext, even your own; caller identity does not travel; writer cycles deadlock.
- `references/servicer-constructor.md` — Set initial state in the `factory=True` method, never in `__init__`; a constructor runs once per actor (a second call aborts `StateAlreadyConstructed`); declare `Transaction(factory=True)` if it may construct others.
- `references/servicer-reader.md` — The reader signature must match the API file; mutating `self.state` is silently discarded; readers may call other readers, and a subscribed reader re-runs when any actor it read changes.
- `references/servicer-writer.md` — A writer mutates `self.state` on one actor only: no writes to other actors, no external calls, schedule only on itself; errors roll back the mutation; writers may return no response.
- `references/rpc-constructor-calls.md` — Call constructors as `<X>.<ctor>(context, id, ...)`, never through `.ref(id)`; `create` exists only if a factory is named that; outside a replayed key a second call aborts.
- `references/rpc-refs.md` — `self.ref().state_id`, never `self.state_id`; IDs are caller-supplied strings; checking whether an actor exists without hitting `StateNotConstructed`; `self.ref().schedule(...)`; reserved method names.
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

If your design calls for any of the concepts in the left column,
the stdlib already provides the canonical actor. Read the
reference **before** writing your own actor type — defining your
own `Queue` / `OrderedMap` / etc. is almost always wrong
and forfeits durability, ordering, and concurrency guarantees:

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

Each stdlib reference also lists its library registration —
forgetting `<thing>_library()` and the stdlib actor's
`<thing>.servicers()` in your `Application(...)` fails when the
type is first called (an unknown state type), not at startup; only a
library whose dependency library is missing fails at startup with
`Missing required libraries: …`.

Backend LLM calls — chat completions, AI agents, tool-using
assistants — go through the durable `reboot.agents.pydantic_ai.Agent`,
**never** a raw `anthropic` / `openai` SDK or a bare
`pydantic_ai.Agent`. A raw call re-hits (and re-bills) the provider
on every workflow replay. Read `agent-pydantic-ai.md` before writing agent code.

### Authorization

<!-- generated:start reading-list front-door=backend-only step=auth -->
- `references/auth-allow-deny.md` — `allow()` only for genuinely public endpoints, never to silence dev warnings, pass tests, or mark "internal-only" methods; `deny()` locks a method out; return an instance.
- `references/auth-allow-if.md` — `allow_if(all=[...])` or `allow_if(any=[...])`, never both, never nested; `all` short-circuits in order; `is_app_internal` in `any` turns anonymous callers' `Unauthenticated` into `PermissionDenied`.
- `references/auth-built-in-predicates.md` — `has_verified_token`, `is_app_internal` and `state_id_is_user_id` and their common compositions; a self-scheduled workflow needs `is_app_internal`; predicates always take `**kwargs`.
- `references/servicer-authorizer.md` — Write real rules on every servicer before the first test; list the tokenless call paths first; identity does not cross servicer calls; `oauth=` vs. the `token_verifier=` escape hatch.
- `references/auth-custom-predicates.md` — Per-method rules via `<Type>.Authorizer(method=rule, _default=rule)`; keyword-only predicates ending in `**kwargs`, annotated or `mypy` fails; check `context.app_internal` first; `PermissionDenied` vs. `Unauthenticated`.
- `references/auth-external-api-calls.md` — only when calling an external service's API as the user.
- `references/stdlib-oauth-tokens.md` — only when storing a user's OAuth tokens for an external service.
<!-- generated:end -->

### Testing

An application's tests are Gherkin `.feature` files run by
`reboot.bdd`; the order of work that writes them (agree on the
feature in English, tag it `@wip`, iterate on scenarios) is the
[`feature` skill](../feature/SKILL.md).

<!-- generated:start reading-list front-door=backend-only step=tests -->
- `references/patterns-idempotency.md` — What `IdempotencyUncertainError` means and when a retry needs an idempotency key; replayed calls return the first run's response; idempotent `create` / `initialize`; UUIDv7 for insertable records.
- `references/testing-features.md` — The built-in steps' exact spelling (who calls, `creates` / `does`, saved values, `eventually`, aborts, tasks), `@wip` / `@blocked`, feature / rule / scenario shape, custom steps, mocks.
- `references/testing-project-setup.md` — `tests/` layout; the template's `pytest.ini` (three paths, or generated `_rbt` imports fail) and fixture (`allowed_origins=[]`); `reboot[dev]`, no `pytest-asyncio`; never construct servicers directly.
- `references/testing-external-context.md` — only when writing custom steps or harness tests.
- `references/testing-failure-recovery.md` — only when the app has a spawned task, a `Workflow`, or scheduled work.
- `references/testing-harness.md` — only when writing custom steps.
<!-- generated:end -->

### Type-checking (do this after every change)

The generated `*_rbt.py` stubs are fully typed, so mypy checks the
code you write against them and catches the mistakes that pass a
visual read — a field set to the wrong type, a missing or misspelled
keyword argument, a method called with the wrong context type, a
response field that doesn't exist, a servicer method returning the
wrong type. Treat a clean type-check as part of finishing, not an
optional extra:

- Every project ships a project-root `.mypy.ini` (config and rationale
  in `references/lifecycle-project-setup.md`). It puts `backend/src`,
  `backend/api`, `tests`, and `api` on `mypy_path` with
  `explicit_package_bases = True` so the generated `*_rbt.py` modules
  resolve. If it's missing, create it first — `mypy` is useless
  without it.
- After writing or editing any Python under `backend/`, run
  `uv run mypy backend/ tests/` (or `mypy backend/ tests/`) from the project root and
  fix **every** error.
- "Done" means both `mypy backend/ tests/` and `uv run pytest` are green.

## Available Reference Files

Reference files live in `references/` and are named
`{prefix}-{topic}.md`; the prefix is the concept in
`references/_sections.md`. Load only what the current task needs —
the lists above say when. The full catalog:

<!-- generated:start catalog skill=python -->
**Lifecycle**
- `references/lifecycle-application-entry.md` — Define the Application Entry Point
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

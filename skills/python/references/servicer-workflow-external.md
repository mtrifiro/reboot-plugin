---
title: Calling External Systems from a Workflow
impact: CRITICAL
impactDescription: A plain await or the wrong primitive re-bills on replay, charges twice, or poisons the step so the workflow can never finish
tags: workflow, external, at_least_once, at_most_once, idempotency key, effect validation, retry, now, randomness, LLM
summary: "A plain await on external calls re-runs on replay; `at_least_once` by default, `at_most_once` when duplicates fail; annotate returns."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "you declared a `Workflow`"
via: servicer-workflow.md
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Calling External Systems from a Workflow

## When you are here

You are calling outside Reboot from a workflow (HTTP, payment/SMS API,
S3, clock, randomness). These skills confine external calls to workflows
(the public docs allow idempotent side effects in any task). LLM calls
use the
durable `reboot.agents.pydantic_ai.Agent`, never a raw `anthropic` /
`openai` SDK or bare `pydantic_ai.Agent`, which re-bill on every replay
([`agent-pydantic-ai.md`](agent-pydantic-ai.md)).

## Do this

### Decide

```
External call from workflow
└── Could a duplicate cause harm the destination can't dedup away?
    ├── No → at_least_once. Idempotent (GET, If-Match, compare-and-set)
    │        → no key. Destination dedups by key (Stripe, AWS) → key
    │        generated OUTSIDE the callable.
    └── Yes → Is a duplicate worse than never running it?
        ├── No → at_least_once, with a comment on the trade-off.
        └── Yes (wire transfer, SMS racing a TOTP rotation, raw chat
                 post) → STOP. at_most_once inside try/except, then ASK
                 THE DEVELOPER how failures are handled.
```

Both memoize success identically. On failure (a raise, or the machine
dying mid-call) `at_least_once` records nothing and re-runs (one or
more times); `at_most_once` records the failure, **poisoning** the
alias so every later attempt raises `AtMostOnceFailedBeforeCompleting`
(zero or one times).

### `at_least_once` — the default

```python
from reboot.aio.workflows import at_least_once


@classmethod
async def charge(
    cls, context: WorkflowContext, request: ChargeRequest,
) -> None:
    # Stable across replays because it's derived from stable inputs.
    key = f"charge:{context.state_id}:{request.invoice_id}"

    async def do_charge() -> ChargeResult:   # ← return annotation required
        return await stripe_client.payment_intents.create(
            amount=request.amount,
            currency="usd",
            idempotency_key=key,
        )

    result = await at_least_once("Charge customer", context, do_charge)
```

- No stable input for a key: generate one in **its own** step,
  `key = await at_least_once("Generate charge key", context, make_key)`
  (`make_key` returns `str(uuid.uuid4())`).
- Clock and randomness are external reads; `WorkflowContext` has no
  clock. Capture "now" once:
  `started_at_ms = await at_least_once("Capture start time", context, _now_ms)`
  where `async def _now_ms() -> int` returns `int(time.time() * 1000)`.

- **Annotate every callable's return type** (also for `until`); it
  checks and pickles the memo, and unannotated means `None`, so any
  other return raises. `type=` only for a lambda
  or dynamic type:
  `await at_least_once("Fetch embeddings", context, fetch, type=list[Vector])`.
- Failures retry forever by **replaying the workflow from the top**, by
  design; closure state does not survive. Let the raise propagate. Only
  when giving up is product behaviour, loop **inside** the callable and
  return exhaustion as data:

```python
async def fetch() -> Optional[list[League]]:
    for attempt in range(5):
        try:
            return await fetch_leagues(token)
        except aiohttp.ClientError:
            await asyncio.sleep(2**attempt)
    return None  # data, not a raise — a raise retries forever

leagues = await at_least_once("Fetch leagues", context, fetch)
```

### `at_most_once` — only when a duplicate is the failure

Non-negotiable: (1) catch inside the callable and return failures as
data; (2) also catch `AtMostOnceFailedBeforeCompleting` at the call (a
mid-call machine death can't be caught inside); (3) **ask the
developer** how failures are handled (record and continue, record and
pause, fallback provider, fail the workflow) before writing that branch.

```python
from reboot.aio.workflows import at_most_once, AtMostOnceFailedBeforeCompleting


@classmethod
async def send_login_sms(
    cls, context: WorkflowContext, request: SendLoginSmsRequest,
) -> None:
    async def do_send() -> SmsResult:
        try:
            response = await sms_client.send(
                to=request.phone,
                body=f"Your code: {request.code}",
            )
            return SmsResult(ok=True, message_id=response.id)
        except sms_client.TransientError as e:
            # MUST be data, not raise — a raise poisons the alias.
            return SmsResult(ok=False, reason=f"transient: {e}")
        except sms_client.PermanentError as e:
            return SmsResult(ok=False, reason=f"permanent: {e}")

    try:
        outcome = await at_most_once("Login SMS", context, do_send)
    except AtMostOnceFailedBeforeCompleting:
        # Machine died mid-call: the SMS may or may not have gone out.
        outcome = SmsResult(ok=False, reason="interrupted before completing")

    if not outcome.ok:
        # Developer-chosen handling; a declared abort stops without
        # retrying (servicer-workflow-exit.md).
        raise User.SendLoginSmsAborted(
            SmsDelivery(reason=outcome.reason),
        )
```

## Never

- A plain `await` on an external call — it re-runs on every replay,
  possibly returning a different value, so derived state diverges.
- `idempotency_key=str(uuid.uuid4())` inside the effecting callable — a
  new key per attempt defeats dedup.
- Counting attempts in a closure to give up — the count resets every
  replay; the give-up branch is dead.
- `raise` inside an `at_most_once` callable — poisons the alias forever.
- A value-returning callable with no annotation and no `type=` — raises
  at runtime; inside `at_most_once` that poisons the alias.
- `at_most_once` for a Reboot call or an idempotent external call.
- A test stand-in that pops answers off a list — effect validation runs
  the callable twice. Derive the answer from the input.

## Limits

- **Effect validation runs an `at_least_once` callable twice** in
  development and the test harness, memoizing the **second** result;
  both run before anything commits, so no guard sees the second. Opt
  billed or non-deterministic calls (LLM, paid search) out per call,
  rather than app-wide:
  `at_least_once(..., effect_validation=EffectValidation.DISABLED)`
  (`from reboot.aio.workflows import EffectValidation`). `at_most_once`
  and `until` callables are not re-run.
- `at_most_once(..., retryable_exceptions=[...])`: a listed exception
  resets the step for a later attempt. List only exceptions proving the
  side effect did not happen.
- A memo is frozen: a pass resumed hours later reuses what it fetched
  then. For a fresh value during replay, use an alias that never ran.
- Results are pickled; return values must be pickle-able.
- No built-in retry budget or backoff on either primitive.
- Scope tuples for these two take `PER_WORKFLOW` or `PER_ITERATION`, not
  `ALWAYS`.

## Scales as

- Effect validation doubles every `at_least_once` callable's cost in
  development: Drive downloads ran twice, a large part of a 70-minute
  pass over 1,666 notes (observed at 1.6.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `AtMostOnceFailedBeforeCompleting` | This `at_most_once` alias started earlier and never stored a result | Catch it at the call site; the alias stays poisoned until expunge |
| `which will now forever more raise` | stderr note: an exception escaped an `at_most_once` callable | Return failures as data |
| `` is not `None` but no `type=` argument was passed `` | Callable returns a value with no annotation | Annotate the return type |
| `is not compatible with the expected type` | Return value disagrees with the annotation | Fix the annotation or `type=` |
| `Re-running block with idempotency alias` | INFO: effect validation re-ran an `at_least_once` callable (not `at_most_once`, not `until`); its second result is memoized; silenced for 5 minutes after printing | Expected in dev; measure progress from state, not log counts; pass `effect_validation=EffectValidation.DISABLED` on calls that must run once in dev |

## See also

- [`servicer-workflow-exit.md`](servicer-workflow-exit.md) — stopping after a failed call
- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — LLM calls in workflows
- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — alias naming rules

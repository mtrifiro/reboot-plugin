---
title: Calling External Systems from a Workflow
impact: CRITICAL
impactDescription: A plain await or the wrong primitive re-bills on replay, charges twice, or poisons the step so the workflow can never finish
tags: workflow, external, at_least_once, at_most_once, idempotency key, effect validation, retry, now, randomness, LLM
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
verified: 1.6.0
docs: "https://docs.reboot.dev/develop/side_effects"
---

# Calling External Systems from a Workflow

## When you are here

Inside a workflow you are about to call something outside Reboot: HTTP,
a payment or SMS API, S3, the wall clock, a random source. Wrap every
such call in `at_least_once` unless a duplicate is itself the failure,
in which case it is `at_most_once`. The public docs allow idempotent side
effects in any task; these skills deliberately confine external calls to
workflows. LLM calls go through the durable
`reboot.agents.pydantic_ai.Agent`, never a raw `anthropic` / `openai` SDK
or bare `pydantic_ai.Agent` (those re-bill on every replay); see
[`agent-pydantic-ai.md`](agent-pydantic-ai.md).

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

Both memoize a success identically. They differ on failure (a raise, or
the machine dying mid-call): `at_least_once` records nothing and re-runs
the callable on the next attempt (one or more times); `at_most_once`
records the failure, the alias is **poisoned**, and every later attempt
raises `AtMostOnceFailedBeforeCompleting` (zero or one times).

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

The wrapper memoizes the first successful result (every replay sees the
same value), retries failures, and names the step. With no stable input
for a key, generate one in **its own** `at_least_once`:
`key = await at_least_once("Generate charge key", context, make_key)`
where `make_key` returns `str(uuid.uuid4())`.

Wall-clock time and randomness are external reads. There is no clock on
`WorkflowContext`; capture "now" once:

```python
async def _now_ms() -> int:
    return int(time.time() * 1000)

started_at_ms = await at_least_once("Capture start time", context, _now_ms)
```

**Annotate every callable's return type** (here and for `until`). The
primitive uses it to check and pickle the memoized value; without one
`at_least_once` / `at_most_once` assume `None` and any other return
raises. Use `type=` only for a lambda or a dynamic type:
`await at_least_once("Fetch embeddings", context, fetch, type=list[Vector])`.

Failures retry by **replaying the workflow from the top**: memoized steps
return their cached results until this step runs again. The callable is
never re-invoked in-process, so closure state does not survive a retry.
Retrying indefinitely is the design; let the raise propagate. Only when
giving up is product behaviour, loop **inside** the callable and return
exhaustion as data:

```python
async def fetch() -> Optional[list[League]]:
    for attempt in range(5):
        try:
            return await fetch_leagues(token)
        except aiohttp.ClientError:
            await asyncio.sleep(2**attempt)
    return None  # data, not a raise — a raise retries forever

leagues = await at_least_once("Fetch leagues", context, fetch)
if leagues is None:
    ...  # Degrade, fall back, or raise a declared abort.
```

### `at_most_once` — only when a duplicate is the failure

Three non-negotiables: (1) catch inside the callable and return failures
as data; (2) also catch `AtMostOnceFailedBeforeCompleting` around the
call, because a mid-call machine death cannot be caught inside; (3)
**stop and ask the developer** how failures are handled (record and
continue, record and pause, fallback provider, fail the workflow) before
writing that branch. Never invent the handling.

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
        # Started but never completed (machine died mid-call): the SMS
        # may or may not have gone out.
        outcome = SmsResult(ok=False, reason="interrupted before completing")

    if not outcome.ok:
        # Developer-chosen handling. To stop without retrying, raise a
        # declared abort (servicer-workflow-exit.md).
        raise User.SendLoginSmsAborted(
            SmsDelivery(reason=outcome.reason),
        )
```

## Never

- A plain `await` on an external call — it re-runs on every replay and
  can return a different value each time, so derived state diverges.
- `idempotency_key=str(uuid.uuid4())` inside the effecting callable — a
  new key per attempt defeats the destination's dedup.
- Counting attempts in a closure to give up — the count resets on every
  replay, so the give-up branch is dead code.
- `raise` inside an `at_most_once` callable — poisons the alias forever.
- A value-returning callable with no annotation and no `type=` — raises
  at runtime; inside `at_most_once` that raise itself poisons the alias.
- `at_most_once` for a Reboot call or an idempotent external call.
- A test stand-in that pops answers off a list — with effect validation
  the callable runs twice. Derive the answer from the input.

## Limits

- **Effect validation runs an `at_least_once` callable twice** in
  development and the test harness, and memoizes the **second** result;
  both runs happen before anything commits, so no guard sees the second.
  Billed or intentionally non-deterministic calls (LLM, paid search)
  opt out per call:
  `at_least_once(..., effect_validation=EffectValidation.DISABLED)`
  (`from reboot.aio.workflows import EffectValidation`). Prefer this to
  disabling validation app-wide. `at_most_once` and `until` callables
  are not re-run.
- `at_most_once(..., retryable_exceptions=[...])`: an exception of a
  listed type resets the step so a later attempt runs the callable again.
  List only exceptions that prove the side effect did not happen.
- A memoized result is a frozen view: a pass resumed hours later reuses
  what it fetched then. To get a fresh value during a replay, call
  `at_least_once` under an alias that has never run.
- Results are pickled; the return value must be pickle-able.
- No built-in retry budget or backoff on either primitive.
- Scope tuples for these two take `PER_WORKFLOW` or `PER_ITERATION`, not
  `ALWAYS`.

## Scales as

- Effect validation doubles the cost of every `at_least_once` callable
  in development: Drive downloads ran twice, a large part of a
  70-minute pass over 1,666 notes (observed at 1.6.0).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `AtMostOnceFailedBeforeCompleting` | This `at_most_once` alias started earlier and never stored a result | Catch it at the call site; the alias stays poisoned until expunge |
| `which will now forever more raise` | stderr note: an exception escaped an `at_most_once` callable | Return failures as data |
| `` is not `None` but no `type=` argument was passed `` | Callable returns a value with no annotation | Annotate the return type |
| `is not compatible with the expected type` | Return value disagrees with the annotation | Fix the annotation or `type=` |
| `Re-running block with idempotency alias` | INFO: effect validation re-ran this callable; silenced for 5 minutes after printing | Expected in dev; measure progress from state, not log counts |

## See also

- [`servicer-workflow-exit.md`](servicer-workflow-exit.md) — stopping after a failed call
- [`agent-pydantic-ai.md`](agent-pydantic-ai.md) — LLM calls in workflows
- [`servicer-workflow-calls.md`](servicer-workflow-calls.md) — alias naming rules

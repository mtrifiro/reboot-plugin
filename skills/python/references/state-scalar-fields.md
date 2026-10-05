---
title: Use Zero-Value Defaults for Scalar State Fields
impact: MEDIUM
impactDescription: Non-zero defaults are rejected at import time
tags: state, scalar, fields, defaults, secret, token, password, credential, api-key, oauth, pii, encryption, ciphertext, bytes
summary: "Scalar `Field`s take the type's zero value, with real values set in the constructor; never store a secret in a plain field, store a `Ciphertext` id."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
when: "a field holds a secret, token or PII, or you want a non-zero default"
verified: 1.6.0
docs: ""
---

# Use Zero-Value Defaults for Scalar State Fields

## When you are here

You are declaring a scalar state field and either want it to start at
something other than zero, or it will hold a password, API key, token
or PII. The general field rules (tags, why defaults must be zero,
nested `Model`s) are in [`api-pydantic.md`](api-pydantic.md).

## Do this

### Zero on the `Field`, the real value in the constructor

| Type | Default |
| --- | --- |
| `int` | `0` |
| `float` | `0.0` |
| `bool` | `False` |
| `str` | `""` |
| `Literal["a", "b"]` | its first value, `"a"` |
| `Optional[T]` | `None` |
| `list[T]` | `default_factory=list` |
| `dict[str, T]` | `default_factory=dict` |

```python
class AccountState(Model):
    name: str = Field(tag=1, default="")
    balance: int = Field(tag=2, default=0)
```

```python
async def open(
    self, context: WriterContext, request: Account.OpenRequest,
) -> None:
    if context.constructor:
        self.state.name = request.name
        self.state.balance = 100  # initial balance applied here
```

Gate set-once values on `context.constructor`; a `start`-style reset
writer may set them unconditionally. Keep the domain default in a
module constant (`DEFAULT_MOVE_DELAY = 1.0`) and apply it when the
request leaves the field at zero.

### A secret is stored as a `Ciphertext` id

A `str` field is plaintext at rest: anyone with the database or a
leaked backup reads it. Encrypt the value with the `Ciphertext` stdlib
type (envelope encryption, per-scope crypto-shredding) and store the
returned `state_id`, itself a harmless `str`. Decrypt on demand.

```python
class IntegrationState(Model):
    # ID of the `Ciphertext` actor holding the encrypted API key.
    api_key_id: str = Field(tag=1, default="")
```

```python
ciphertext, _ = await Ciphertext.encrypt(
    context,
    plaintext=raw_api_key.encode(),
    associated_data=make_associated_data(tenant_id=tenant_id, purpose="api-key"),
    scope=f"tenant:{tenant_id}",  # crypto-shred unit for right-to-erasure
    key_manager_id=APP_SHARED_KEY_MANAGER_ID,
)
self.state.api_key_id = ciphertext.state_id
```

Pick by who holds the secret:

| Secret | Where it goes |
| --- | --- |
| Password, session token, PII, other per-user secret | `Ciphertext` id (method surface, library registration, `associated_data`: `stdlib-ciphertext.md`) |
| OAuth access/refresh token from an `OAuthProvider` | `OAuthTokenManager`, not `Ciphertext` by hand; with `store_tokens=True` the OAuth server stores them and you `fetch` (`stdlib-oauth-tokens.md`) |
| An API key the **user** provides for a non-OAuth service | `Ciphertext`; capture-and-call recipe in `auth-external-api-calls.md` (Path C) |
| A key the **developer** holds for the whole app (Stripe, OpenAI) | Not in state: an application secret via environment variables (`lifecycle-secrets.md`) |

## Never

- `api_key: str = Field(tag=1, default="")` holding the key itself —
  plaintext at rest. "It's just a string" is the trap. Store
  `api_key_id`.
- `balance: int = Field(tag=1, default=100)` — rejected at import;
  zero default, set `100` in the constructor.
- `image: bytes = Field(tag=1, default=b"")` — `bytes` is not a field
  type (`api-pydantic.md` § Limits). Base64 in a `str`.
- Hand-roll `Ciphertext` for OAuth tokens — `OAuthTokenManager` adds
  the per-user index, key manager and shred scope for you.

## Limits

- A value set in the constructor is not back-filled onto actors
  created before the code changed; see `api-schema-evolution.md`.

## Scales as

- Not measured.

## Errors you will see

None known beyond the default-value rows in
[`api-pydantic.md`](api-pydantic.md) § Errors you will see.

## See also

- [`stdlib-ciphertext.md`](stdlib-ciphertext.md) — encrypting secrets at rest
- [`stdlib-oauth-tokens.md`](stdlib-oauth-tokens.md) — storing OAuth tokens
- [`api-pydantic.md`](api-pydantic.md) — the full field rules

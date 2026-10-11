---
title: Use Zero-Value Defaults for Scalar State Fields
impact: MEDIUM
impactDescription: Non-zero defaults are rejected at import time
tags: state, scalar, fields, defaults, secret, token, password, credential, api-key, oauth, pii, encryption, ciphertext, bytes
summary: "Non-zero defaults are rejected and plain-field secrets leak; zero values, real values in the constructor, `Ciphertext` ids."
step: api
applies: [mcp-ui, web-app, backend-only]
always: false
when: "a field holds a secret, token or PII, or you want a non-zero default"
verified: 1.6.0
docs: ""
---

# Use Zero-Value Defaults for Scalar State Fields

## When you are here

You are declaring a scalar state field that should start non-zero, or
will hold a password, API key, token or PII. General field rules (tags,
why defaults are zero, nested `Model`s): [`api-pydantic.md`](api-pydantic.md).

## Do this

### Zero on the `Field`, the real value in the constructor

Defaults: `int` `0`, `float` `0.0`, `bool` `False`, `str` `""`,
`Literal["a", "b"]` its first value `"a"`, `Optional[T]` `None`,
`list[T]` `default_factory=list`, `dict[str, T]` `default_factory=dict`.

```python
class AccountState(Model):
    name: str = Field(tag=1, default="")
    balance: int = Field(tag=2, default=0)


async def open(
    self, context: WriterContext, request: Account.OpenRequest,
) -> None:
    if context.constructor:
        self.state.name = request.name
        self.state.balance = 100  # initial balance applied here
```

- Gate set-once values on `context.constructor`; a `start`-style reset
  writer may set them unconditionally.
- Keep the domain default in a module constant
  (`DEFAULT_MOVE_DELAY = 1.0`) and apply it when the request leaves the
  field at zero.

### A secret is stored as a `Ciphertext` id

A `str` field is plaintext at rest (database, leaked backups). Encrypt
with the `Ciphertext` stdlib type (envelope encryption, per-scope
crypto-shredding) and store only the returned `state_id`, e.g.
`api_key_id: str = Field(tag=1, default="")` set to
`ciphertext.state_id`; decrypt on demand. The encrypt/decrypt block is
in `stdlib-ciphertext.md`.

| Secret | Where it goes |
| --- | --- |
| Password, session token, PII, other per-user secret | `Ciphertext` id (method surface, library registration, `associated_data`: `stdlib-ciphertext.md`) |
| OAuth access/refresh token from an `OAuthProvider` | `OAuthTokenManager`, not `Ciphertext` by hand; with `store_tokens=True` the OAuth server stores them and you `fetch` (`stdlib-oauth-tokens.md`) |
| An API key the **user** provides for a non-OAuth service | `Ciphertext`; capture-and-call recipe in `auth-external-api-calls.md` (Path C) |
| A key the **developer** holds for the whole app (Stripe, OpenAI) | Not in state: an application secret via environment variables (`lifecycle-secrets.md`) |

## Never

- `api_key: str = Field(tag=1, default="")` holding the key itself —
  plaintext at rest. Store `api_key_id`.
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

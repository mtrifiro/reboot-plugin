---
title: Use `Ciphertext` for Envelope Encryption and Crypto-Shredding
impact: HIGH
impactDescription: Hand-rolled encryption-at-rest / right-to-erasure is easy to get wrong; the stdlib library is auditable and handles key rotation for you.
tags: stdlib, ciphertext, encryption, envelope, crypto-shred, gdpr, right-to-erasure, shred, scope, key-manager, associated-data
summary: "Envelope encryption and per-scope crypto-shredding with automatic key rotation, before you hand-roll any; needs `ordered_map_library()`; keep the `Ciphertext` id; never rebuild `associated_data` by hand."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "storing secrets or PII encrypted at rest"
verified: 1.6.0
docs: ""
---

# Use `Ciphertext` for Envelope Encryption and Crypto-Shredding

## When you are here

You store sensitive values (PII, secrets, notes) and want
encryption at rest, per-user/per-tenant erasure ("right to erasure"),
or both. `Ciphertext` (`reboot.std.ciphertext.v1.ciphertext` /
`rbt.std.ciphertext.v1.ciphertext_rbt`) is application-layer envelope
encryption with one-call crypto-shredding: destroy one key and a whole
*scope* of data becomes unrecoverable, without finding or rewriting the
data. Building your own key derivation is `crypto-root-keys.md`.

Three key layers:

```
root KEK   — derived from REBOOT_CRYPTO_ROOT_KEYS (auto-provisioned); never stored.
  └ wraps → WrappingKey — one per (key manager, scope); the revocable unit, stored *encrypted*.
     └ wraps → DEK — a fresh per-value data-encryption key.
        └ encrypts → your plaintext   (the stored "envelope")
```

Recovering a value needs both the database and `REBOOT_CRYPTO_ROOT_KEYS`
(which lives outside the DB), so a leaked backup alone is inert.

## Do this

### Register both libraries

```python
from reboot.std.ciphertext.v1.ciphertext import ciphertext_library
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)


async def main():
    await Application(
        servicers=[VaultServicer],
        libraries=[ciphertext_library(), ordered_map_library()],
    ).run()
```

### Imports and methods

```python
from rbt.std.ciphertext.v1.ciphertext_rbt import Ciphertext, KeyManager
from rbt.std.ciphertext.v1.ciphertext_pb2 import (
    DecryptionFailed, ScopeShredded, UnknownRootKeyVersion,
)
from reboot.std.ciphertext.v1.ciphertext import (
    APP_SHARED_KEY_MANAGER_ID, ciphertext_library, make_associated_data,
)
```

| Call | Kind | Notes |
| --- | --- | --- |
| `Ciphertext.encrypt(context, [id], *, plaintext, associated_data, scope, key_manager_id)` | transaction (constructor) | returns `(ref, EncryptResponse)`; omit `id` to auto-generate it, read it back as `ref.state_id` |
| `Ciphertext.ref(id).decrypt(context, *, associated_data)` | reader | `-> DecryptResponse(plaintext)`; raises `Ciphertext.DecryptAborted` |
| `Ciphertext.ref(id).rescope(context, *, scope)` | transaction | move to another scope in the same manager; only the wrapped DEK changes |
| `KeyManager.ref(manager_id).shred(context, *, scope)` | transaction | crypto-shred a scope; idempotent |
| `KeyManager.ref(manager_id).status(context)` | reader | `-> StatusResponse(active_version, rotating)` |

### Encrypt, store the id, decrypt

```python
ciphertext, _ = await Ciphertext.encrypt(
    context,
    plaintext=b"123-45-6789",
    associated_data=make_associated_data(user_id="42", purpose="ssn"),
    scope="user:42",                       # the crypto-shred unit
    key_manager_id=APP_SHARED_KEY_MANAGER_ID,
)
ciphertext_id = ciphertext.state_id   # store this to decrypt later

try:
    response = await Ciphertext.ref(ciphertext_id).decrypt(
        context,
        associated_data=make_associated_data(user_id="42", purpose="ssn"),
    )
    plaintext = response.plaintext
except Ciphertext.DecryptAborted as aborted:
    if isinstance(aborted.error, ScopeShredded):
        ...   # permanently unrecoverable — the scope was shredded
    elif isinstance(aborted.error, DecryptionFailed):
        ...   # wrong associated_data, or the envelope is corrupt
    elif isinstance(aborted.error, UnknownRootKeyVersion):
        ...   # its root key version was dropped from the env
    raise
```

`key_manager_id` is required: `APP_SHARED_KEY_MANAGER_ID` for the
application-wide manager, or your own id for an independent
`KeyManager` (its own rotation loop, registry and shred domain); two
managers may use the same `scope` without sharing or shredding each
other's wrapping key.

`associated_data` is authenticated but not stored: it binds a
ciphertext to its context (sealed for `user_id=42`, it won't decrypt
as `user_id=99`), and the identical bytes must be supplied at decrypt.
`make_associated_data(**fields)` gives a canonical, sorted,
length-prefixed encoding; use ASCII keys and string values. The
TypeScript `makeAssociatedData` produces identical bytes.

### Crypto-shred a scope

```python
await KeyManager.ref(APP_SHARED_KEY_MANAGER_ID).shred(context, scope="user:42")
```

Every `Ciphertext` in that scope is now undecryptable, even with full
database and root-key access; `decrypt` raises
`DecryptAborted(ScopeShredded())`. You never touch or enumerate the
ciphertexts. Key the scope on the entity you may need to forget (e.g.
the user id).

### Rotation is automatic

Operators add a version to `REBOOT_CRYPTO_ROOT_KEYS` (e.g.
`v2:NEW,v1:OLD`) and restart; the `KeyManager`'s `watch` loop re-wraps
every wrapping key onto the new version in the background. Only the
small wrapping keys are re-wrapped, never the data. Poll `status` until
`active_version` is the new version and `rotating` is false, then drop
the old one (`REBOOT_CRYPTO_ROOT_KEYS="v2:NEW"`). `rbt dev` and Reboot
Cloud provision the variable (`lifecycle-secrets.md`).

## Never

- `libraries=[ciphertext_library()]` alone — it requires the ordered-map
  library; add `ordered_map_library()`.
- `associated_data=b"user-42:ssn"` or `json.dumps(...)` — ambiguous or
  non-canonical; build it with `make_associated_data` and pass the same
  fields at decrypt.
- Addressing `WrappingKey` directly — an implementation detail; shred
  with `KeyManager.shred(scope=...)`.
- Calling these methods from untrusted clients — the servicers define
  no authorizer, so they get the app-internal default; call them from
  your own servicers, or add an explicit authorizer (`auth-allow-if.md`).
- Dropping the `Ciphertext` id — store `state_id`; nothing else finds
  the value again.
- Removing an old root key version before `status` shows
  `rotating == False` — values still wrapped under it fail with
  `UnknownRootKeyVersion`.

## Limits

- A shredded scope stays shredded: `WrappingKey.wrap` refuses a revoked
  key with `ScopeShredded`, so encrypting or rescoping into that scope
  again fails. Use a new scope string.
- `status().active_version` is unset until the manager has registered
  its first key.
- Rotation re-wraps in pages of 256 registry entries (`_ROTATE_PAGE_SIZE`,
  1.6.0 source).
- `REBOOT_CRYPTO_ROOT_KEYS` must be present wherever the app runs; see
  `crypto-root-keys.md` for its errors.

## Scales as

- Each `encrypt` is one transaction on the `Ciphertext` plus a `wrap` on
  its scope's `WrappingKey`; rotation cost grows with the number of
  wrapping keys (scopes), not with the number of ciphertexts (framework
  design).

## Errors you will see

| Error text (stable prefix) | Meaning | Fix |
| --- | --- | --- |
| `Missing required libraries: reboot.std.collections.ordered_map.v1.ordered_map` | `ciphertext_library()` without `ordered_map_library()` | Add `ordered_map_library()` |
| `DecryptAborted` with `ScopeShredded` | The scope was shredded | Treat as permanently erased |
| `DecryptAborted` with `DecryptionFailed` | `associated_data` differs, or corrupt envelope | Rebuild it with the same `make_associated_data` fields |

## See also

- [`crypto-root-keys.md`](crypto-root-keys.md) — the root-key facility underneath
- [`lifecycle-secrets.md`](lifecycle-secrets.md) — how `REBOOT_CRYPTO_ROOT_KEYS` is provisioned
- [`auth-allow-if.md`](auth-allow-if.md) — exposing methods beyond app-internal

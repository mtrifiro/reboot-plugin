---
title: Use `Ciphertext` for Envelope Encryption and Crypto-Shredding
impact: HIGH
impactDescription: Hand-rolled encryption-at-rest / right-to-erasure is easy to get wrong; the stdlib library is auditable and handles key rotation for you.
tags: stdlib, ciphertext, encryption, envelope, crypto-shred, gdpr, right-to-erasure, shred, scope, key-manager, associated-data
summary: "Don't hand-roll encryption or rebuild `associated_data`; envelope encryption, crypto-shredding, rotation; needs `ordered_map_library()`; keep the id."
step: servicer
applies: [mcp-ui, web-app, backend-only]
always: false
when: "storing secrets or PII encrypted at rest"
verified: 1.6.0
docs: ""
---

# Use `Ciphertext` for Envelope Encryption and Crypto-Shredding

## When you are here

Encrypting sensitive values at rest and/or erasing a whole user's or
tenant's data ("right to erasure"). `Ciphertext`
(`reboot.std.ciphertext.v1.ciphertext` /
`rbt.std.ciphertext.v1.ciphertext_rbt`) is envelope encryption with
one-call crypto-shredding: destroy one key and a whole *scope* becomes
unrecoverable without finding the data. Own key derivation:
`crypto-root-keys.md`.

```
root KEK   — derived from REBOOT_CRYPTO_ROOT_KEYS (auto-provisioned); never stored.
  └ wraps → WrappingKey — one per (key manager, scope); the revocable unit, stored *encrypted*.
     └ wraps → DEK — a fresh per-value data-encryption key.
        └ encrypts → your plaintext   (the stored "envelope")
```

Decrypting needs the database and `REBOOT_CRYPTO_ROOT_KEYS` (kept
outside the DB), so a leaked backup alone is inert.

## Do this

### Register both libraries; imports

```python
from rbt.std.ciphertext.v1.ciphertext_rbt import Ciphertext, KeyManager
from rbt.std.ciphertext.v1.ciphertext_pb2 import (
    DecryptionFailed, ScopeShredded, UnknownRootKeyVersion,
)
from reboot.std.ciphertext.v1.ciphertext import (
    APP_SHARED_KEY_MANAGER_ID, ciphertext_library, make_associated_data,
)
from reboot.std.collections.ordered_map.v1.ordered_map import (
    ordered_map_library,
)

async def main():
    await Application(
        servicers=[VaultServicer],
        libraries=[ciphertext_library(), ordered_map_library()],
    ).run()
```

| Call | Kind | Notes |
| --- | --- | --- |
| `Ciphertext.encrypt(context, [id], *, plaintext, associated_data, scope, key_manager_id)` | transaction (constructor) | returns `(ref, EncryptResponse)`; omit `id` to auto-generate; read it as `ref.state_id` |
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

- `key_manager_id` is required: `APP_SHARED_KEY_MANAGER_ID`, or your
  own id for an independent `KeyManager` (own rotation loop, registry
  and shred domain). Two managers may share a `scope` string without
  sharing or shredding each other's wrapping key.
- `associated_data` is authenticated, not stored: it binds the
  ciphertext to its context (sealed for `user_id=42`, it won't decrypt
  as `user_id=99`); pass identical bytes at decrypt.
  `make_associated_data(**fields)` is canonical (sorted,
  length-prefixed); use ASCII keys and string values. TypeScript
  `makeAssociatedData` produces identical bytes.

### Crypto-shred a scope

```python
await KeyManager.ref(APP_SHARED_KEY_MANAGER_ID).shred(context, scope="user:42")
```

Every `Ciphertext` in the scope is now undecryptable even with full
DB and root-key access; `decrypt` raises `DecryptAborted(ScopeShredded())`; no
enumeration needed. Key the scope on the entity you may need to forget
(e.g. the user id).

### Rotation is automatic

Operators add a version (`v2:NEW,v1:OLD`) and restart; the `KeyManager`'s `watch` loop re-wraps every wrapping key
(never the data) onto it in the background. Poll `status` until
`active_version` is the new version and `rotating` is false, then drop
the old one (`REBOOT_CRYPTO_ROOT_KEYS="v2:NEW"`). `rbt dev` and Reboot
Cloud provision the variable (`lifecycle-secrets.md`).

## Never

- `libraries=[ciphertext_library()]` alone — it requires
  `ordered_map_library()`.
- `associated_data=b"user-42:ssn"` or `json.dumps(...)` — ambiguous or
  non-canonical; use `make_associated_data` with the same fields at
  decrypt.
- Addressing `WrappingKey` directly — implementation detail; use
  `KeyManager.shred(scope=...)`.
- Calling these methods from untrusted clients — no authorizer, so the
  app-internal default applies; call from your servicers or add an
  authorizer (`auth-allow-if.md`).
- Dropping the `Ciphertext` id — store `state_id`; nothing else finds
  the value.
- Removing an old root key version before `status` shows
  `rotating == False` — values still wrapped under it fail with
  `UnknownRootKeyVersion`.

## Limits

- A shredded scope stays shredded: `WrappingKey.wrap` refuses a revoked
  key with `ScopeShredded`, so encrypt/rescope into it fails. Use a new
  scope string.
- `status().active_version` is unset until the manager registers its
  first key.
- Rotation re-wraps in pages of 256 registry entries (`_ROTATE_PAGE_SIZE`,
  1.6.0 source).
- `REBOOT_CRYPTO_ROOT_KEYS` must be present wherever the app runs; errors
  in `crypto-root-keys.md`.

## Scales as

- Each `encrypt` is one transaction on the `Ciphertext` plus a `wrap` on
  its scope's `WrappingKey`; rotation cost grows with wrapping keys
  (scopes), not ciphertexts (framework design).

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
